"""Statistics. Convention: SAMPLE standard deviation (ddof = 1), used everywhere."""
import numpy as np
import pandas as pd

DDOF = 1
TRAFFIC_ORDER = ["Low", "Medium", "High", "Jam"]
AGE_ORDER = ["Below 25", "25–40", "Above 40"]


def ordered(df: pd.DataFrame, col: str) -> list:
    """Categories actually present in the data, in a sensible order."""
    present = list(df[col].dropna().unique())
    if col == "Traffic":
        known = [v for v in TRAFFIC_ORDER if v in present]
        return known + sorted(v for v in present if v not in known)
    if col == "Agent_Age_Group":
        return [v for v in AGE_ORDER + ["Unknown"] if v in present]
    if col == "Late_Status":
        return [v for v in ["Late", "On-Time"] if v in present]
    return sorted(present)


def late_threshold(times: pd.Series):
    """μ, σ and the project-defined threshold T_late = μ + σ."""
    mu = times.mean()
    sd = times.std(ddof=DDOF) if len(times) > 1 else np.nan
    return mu, sd, (mu + sd if pd.notna(sd) else np.nan)


def add_late(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    df = df.copy()
    df["Is_Late"] = (df["Delivery_Time"] > threshold) if pd.notna(threshold) else False
    df["Late_Status"] = np.where(df["Is_Late"], "Late", "On-Time")
    return df


def summary(df: pd.DataFrame, threshold: float) -> dict:
    t = df["Delivery_Time"]
    n, late = len(t), int(df["Is_Late"].sum())
    q1, q3 = t.quantile(.25), t.quantile(.75)
    return {
        "Total orders": n, "Mean (μ)": t.mean(), "Median": t.median(),
        "Std deviation (σ, sample)": t.std(ddof=DDOF) if n > 1 else np.nan,
        "Minimum": t.min(), "Maximum": t.max(), "Q1": q1, "Q3": q3, "IQR": q3 - q1,
        "Late threshold T_late (global μ+σ)": threshold, "Late orders": late,
        "On-time orders": n - late, "Late delivery %": late / n * 100 if n else np.nan,
    }


def group_table(df: pd.DataFrame, by) -> pd.DataFrame:
    t = df.groupby(by).agg(Orders=("Delivery_Time", "count"), Mean=("Delivery_Time", "mean"),
                           Median=("Delivery_Time", "median"), Std=("Delivery_Time", lambda s: s.std(ddof=DDOF)),
                           Min=("Delivery_Time", "min"), Max=("Delivery_Time", "max"),
                           Late_Orders=("Is_Late", "sum")).reset_index()
    t["Late_%"] = t["Late_Orders"] / t["Orders"] * 100
    return t
