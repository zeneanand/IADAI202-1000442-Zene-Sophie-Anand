"""Cleaning pipeline: works on a copy, logs every action, never silently fills data."""
import re
import numpy as np
import pandas as pd

CAT_COLS = ["Weather", "Traffic", "Vehicle", "Area", "Category"]
NUM_COLS = ["Delivery_Time", "Agent_Rating", "Agent_Age"]
CORE = ["Delivery_Time", "Weather", "Traffic", "Vehicle", "Agent_Rating", "Agent_Age", "Area", "Category"]
OPTIONAL = ["Order_ID"]
NULL_TOKENS = {"", "nan", "none", "null", "na", "n/a", "nat", "-", "?"}
AGE_ORDER = ["Below 25", "25–40", "Above 40"]
RANGES = {"Delivery_Time": "> 0", "Agent_Rating": "0 < r ≤ 5", "Agent_Age": "0 < age ≤ 100"}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def auto_map(columns) -> dict:
    """Map each expected name to a dataset column (case/spacing-insensitive). Returns {target: source}."""
    cols, mapping = list(columns), {}
    for target in CORE + OPTIONAL:
        exact = [c for c in cols if _norm(c) == _norm(target)]
        prefix = [c for c in cols if _norm(c).startswith(_norm(target)) and c not in mapping.values()]
        pick = exact or prefix
        if pick:
            mapping[target] = pick[0]
    return mapping


def age_group(age: pd.Series) -> pd.Series:
    out = np.select([age < 25, age <= 40, age > 40], AGE_ORDER, default="Unknown")
    return pd.Series(out, index=age.index)


def prepare(raw: pd.DataFrame, mapping: dict):
    """Return (clean_df, report). `raw` is never modified."""
    df = raw.rename(columns={src: tgt for tgt, src in mapping.items()}).copy()
    log, warns = [], []

    def add(step, col, n, action):
        if n:
            log.append({"Step": step, "Column": col, "Rows affected": int(n), "Action": action})

    # 1. Text columns: trim, treat null-like tokens as missing, standardise capitalisation
    for c in CAT_COLS:
        orig = df[c].astype("string")
        s = orig.str.strip()
        add("Trim whitespace", c, (orig.notna() & (orig != s)).sum(), "Removed leading/trailing spaces")
        null_like = s.str.lower().isin(NULL_TOKENS).fillna(False)
        add("Normalise missing", c, null_like.sum(), "Converted blank/'nan'/'none' text to missing")
        s = s.mask(null_like | s.isna())
        titled = s.str.title()
        add("Standardise case", c, (s.notna() & (s != titled)).sum(), "Converted to Title Case so 'van' and 'Van' are one category")
        s = titled
        df[c] = s.astype(object).where(s.notna(), np.nan)
    if "Order_ID" in df:
        df["Order_ID"] = df["Order_ID"].astype("string").str.strip()

    # 2. Numeric columns: safe conversion, then range validation
    invalid = {}
    for c in NUM_COLS:
        before = df[c]
        num = pd.to_numeric(before, errors="coerce")
        text_bad = (before.notna() & num.isna()).sum()
        hi = 5 if c == "Agent_Rating" else 100 if c == "Agent_Age" else np.inf
        range_bad = ((num <= 0) | (num > hi)).sum()
        num = num.mask((num <= 0) | (num > hi))
        invalid[c] = int(text_bad + range_bad)
        add("Invalid numeric", c, text_bad, "Non-numeric text converted to missing")
        add("Invalid numeric", c, range_bad, f"Out-of-range value (valid: {RANGES[c]}) set to missing")
        df[c] = num

    missing_before = df[CORE].isna().sum()

    # 3. Duplicates (by Order_ID when available, else whole-row)
    n0 = len(df)
    df = df.drop_duplicates(subset=["Order_ID"] if "Order_ID" in df else None, keep="first")
    dup = n0 - len(df)
    add("Duplicates", "Order_ID" if "Order_ID" in df else "all columns", dup, "Removed repeated records (kept first)")

    # 4. Delivery_Time is the outcome variable: rows without a valid value are excluded, not imputed
    bad_time = int(df["Delivery_Time"].isna().sum())
    add("Exclude invalid outcome", "Delivery_Time", bad_time, "Row excluded (imputing the outcome would distort μ, σ and the late threshold)")
    df = df.dropna(subset=["Delivery_Time"]).copy()

    # 5. Impute remaining gaps: median (numeric) / mode (categorical)
    for c in ["Agent_Rating", "Agent_Age"]:
        n_miss = df[c].isna().sum()
        if n_miss and df[c].notna().any():
            df[c] = df[c].fillna(df[c].median())
            add("Impute (median)", c, n_miss, "Filled with median of valid values")
        elif n_miss:
            warns.append(f"'{c}' has no valid values, so it could not be imputed; age groups will show 'Unknown'.")
    for c in CAT_COLS:
        n_miss = df[c].isna().sum()
        if not n_miss:
            continue
        mode = df[c].dropna().mode()
        if len(mode):
            df[c] = df[c].fillna(mode.iloc[0])
            add("Impute (mode)", c, n_miss, f"Filled with most frequent value ('{mode.iloc[0]}')")
        else:
            df[c] = df[c].fillna("Unknown")
            warns.append(f"'{c}' has no valid values; filled with 'Unknown'. Charts using it will be uninformative.")

    df["Agent_Age_Group"] = age_group(df["Agent_Age"])
    df = df.reset_index(drop=True)
    report = {
        "raw_rows": len(raw), "final_rows": len(df), "duplicates": int(dup), "invalid_time_dropped": bad_time,
        "invalid_counts": invalid, "missing_before": missing_before, "missing_after": df[CORE].isna().sum(),
        "log": pd.DataFrame(log, columns=["Step", "Column", "Rows affected", "Action"]), "warnings": warns,
    }
    return df, report
