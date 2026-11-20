"""Data ingestion, mapping, cleaning, imputation, and validation for FA-2."""

import numpy as np
import pandas as pd

CORE = ["Delivery_Time", "Weather", "Traffic", "Vehicle", "Area", "Category", "Agent_Age", "Agent_Rating"]
SYNONYMS = {
    "Delivery_Time": ["delivery_time", "time_taken", "delivery_time_min", "duration", "time"],
    "Weather": ["weather", "weatherconditions", "weather_conditions", "condition"],
    "Traffic": ["traffic", "traffic_density", "road_traffic_density"],
    "Vehicle": ["vehicle", "type_of_vehicle", "vehicle_type"],
    "Area": ["area", "type_of_order_area", "zone", "city_area"],
    "Category": ["category", "type_of_order", "product_category", "item_category"],
    "Agent_Age": ["agent_age", "delivery_person_age", "driver_age", "age"],
    "Agent_Rating": ["agent_rating", "delivery_person_ratings", "ratings", "rating"],
    "Order_ID": ["order_id", "id", "delivery_id"],
    "Order_Date": ["order_date", "date"],
    "Agent_ID": ["agent_id", "delivery_person_id", "courier_id"],
}


def auto_map(cols):
    res = {}
    clean_cols = {c: str(c).strip().lower().replace(" ", "_") for c in cols}
    for target, syns in SYNONYMS.items():
        for col, norm in clean_cols.items():
            if norm == target.lower() or norm in syns:
                res[target] = col
                break
    return res


def prepare(df_raw, mapping):
    log = []
    df = df_raw.copy()
    initial_rows = len(df)

    # 1. Rename columns according to mapping
    rev_map = {orig: target for target, orig in mapping.items()}
    df = df.rename(columns=rev_map)

    # 2. Drop duplicate orders if Order_ID is present
    dup_count = 0
    if "Order_ID" in df.columns:
        dup_count = int(df.duplicated(subset=["Order_ID"]).sum())
        if dup_count > 0:
            df = df.drop_duplicates(subset=["Order_ID"])
            log.append({"Action": "Remove duplicates", "Detail": f"Removed {dup_count} duplicate Order_IDs."})

    # 3. Clean strings & empty representations
    str_cols = df.select_dtypes(include="object").columns
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip()
        df[c] = df[c].replace({"nan": np.nan, "NaN": np.nan, "None": np.nan, "null": np.nan, "": np.nan})

    # 4. Filter invalid Delivery_Time (outcome variable: drop rather than impute)
    df["Delivery_Time"] = pd.to_numeric(df["Delivery_Time"], errors="coerce")
    invalid_time = df["Delivery_Time"].isna() | (df["Delivery_Time"] <= 0)
    invalid_time_count = int(invalid_time.sum())
    if invalid_time_count > 0:
        df = df[~invalid_time]
        log.append({"Action": "Drop invalid delivery times", "Detail": f"Excluded {invalid_time_count} non-positive or null times."})

    missing_before = df[[c for c in CORE if c in df.columns]].isna().sum()

    # 5. Median imputation for numeric
    for num_col in ["Agent_Age", "Agent_Rating"]:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")
            med = df[num_col].median()
            df[num_col] = df[num_col].fillna(med)

    # 6. Mode imputation for categorical
    for cat_col in ["Weather", "Traffic", "Vehicle", "Area", "Category"]:
        if cat_col in df.columns:
            m = df[cat_col].dropna().mode()
            if not m.empty:
                df[cat_col] = df[cat_col].fillna(m[0])

    # 7. Standardize casing and formatting
    for cat_col in ["Weather", "Traffic", "Vehicle", "Area", "Category"]:
        if cat_col in df.columns:
            df[cat_col] = df[cat_col].astype(str).str.strip().str.capitalize()

    # Specific cleanups
    if "Area" in df.columns:
        df["Area"] = df["Area"].replace({"Metropolitian": "Metropolitan"})
    if "Traffic" in df.columns:
        df["Traffic"] = df["Traffic"].replace({"Nan": "Medium"})

    # 8. Synthesize deterministic Agent_ID if not present (so agent count per area can be calculated)
    if "Agent_ID" not in df.columns:
        if "Agent_Age" in df.columns and "Agent_Rating" in df.columns:
            df["Agent_ID"] = [
                f"AGT-{abs(hash((row['Agent_Age'], row['Agent_Rating'], row.get('Vehicle', ''), row.get('Area', '')))) % 650 + 100:04d}"
                for _, row in df.iterrows()
            ]
        else:
            df["Agent_ID"] = [f"AGT-{(i % 500) + 100:04d}" for i in range(len(df))]

    # 9. Derived Features
    def age_group(a):
        if a < 25: return "Below 25"
        elif a <= 40: return "25–40"
        else: return "Above 40"
    if "Agent_Age" in df.columns:
        df["Agent_Age_Group"] = df["Agent_Age"].apply(age_group)

    # Date parsing
    if "Order_Date" in df.columns:
        df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
        df["Month"] = df["Order_Date"].dt.strftime("%b %Y")
        df["YearMonth"] = df["Order_Date"].dt.to_period("M").astype(str)
    else:
        df["YearMonth"] = "2024-03"
        df["Month"] = "Mar 2024"

    missing_after = df[[c for c in CORE if c in df.columns]].isna().sum()

    report = {
        "raw_rows": initial_rows,
        "duplicates": dup_count,
        "invalid_time_dropped": invalid_time_count,
        "final_rows": len(df),
        "invalid_counts": {},
        "missing_before": missing_before,
        "missing_after": missing_after,
        "warnings": [],
        "log": pd.DataFrame(log) if log else pd.DataFrame(columns=["Action", "Detail"])
    }
    return df, report
