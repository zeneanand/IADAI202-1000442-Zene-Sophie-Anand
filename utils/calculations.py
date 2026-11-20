"""Statistical aggregations and metrics calculations for FA-2."""

import numpy as np
import pandas as pd

CORE_NUMERIC = ["Delivery_Time", "Agent_Age", "Agent_Rating"]


def late_threshold(series):
    s = series.dropna()
    if s.empty:
        return np.nan, np.nan, np.nan
    mu = float(s.mean())
    sd = float(s.std(ddof=1)) if len(s) > 1 else 0.0
    return mu, sd, mu + sd


def add_late(df, threshold):
    out = df.copy()
    out["Is_Late"] = out["Delivery_Time"] > threshold
    out["Late_Status"] = np.where(out["Is_Late"], "Late (> T_late)", "On-time")
    return out


def summary(df, threshold):
    t = df["Delivery_Time"].dropna()
    n = len(t)
    if n == 0:
        return {
            "Total orders": 0,
            "Mean (μ)": 0.0,
            "Std (σ)": 0.0,
            "Median": 0.0,
            "IQR": 0.0,
            "Late orders": 0,
            "Late delivery %": 0.0,
            "On-time orders": 0,
            "On-time %": 0.0,
        }
    mu = float(t.mean())
    sd = float(t.std(ddof=1)) if n > 1 else 0.0
    late = int((t > threshold).sum())
    late_pct = (late / n) * 100.0
    return {
        "Total orders": n,
        "Mean (μ)": mu,
        "Std (σ)": sd,
        "Median": float(t.median()),
        "IQR": float(t.quantile(0.75) - t.quantile(0.25)),
        "Late orders": late,
        "Late delivery %": late_pct,
        "On-time orders": n - late,
        "On-time %": 100.0 - late_pct,
    }


def group_table(df, by, target="Delivery_Time"):
    g = df.groupby(by)[target].agg(
        Orders="count",
        Mean="mean",
        Median="median",
        Std=lambda s: s.std(ddof=1) if len(s) > 1 else 0.0,
        Q25=lambda s: s.quantile(0.25),
        Q75=lambda s: s.quantile(0.75),
    ).reset_index()
    total_orders = len(df)
    g["Share_%"] = (g["Orders"] / total_orders * 100.0) if total_orders > 0 else 0.0
    if "Is_Late" in df.columns:
        late_g = df.groupby(by)["Is_Late"].agg(Late="sum", Late_pct=lambda s: s.mean() * 100.0).reset_index()
        merge_cols = [by] if isinstance(by, str) else by
        g = g.merge(late_g, on=merge_cols)
        g.rename(columns={"Late_pct": "Late_%"}, inplace=True)
    return g


def ordered(df, col):
    u = df[col].dropna().unique().tolist()
    order_maps = {
        "Traffic": ["Low", "Medium", "High", "Jam"],
        "Agent_Age_Group": ["Below 25", "25–40", "Above 40"],
        "Late_Status": ["On-time", "Late (> T_late)"],
    }
    if col in order_maps:
        return [x for x in order_maps[col] if x in u]
    return sorted(u, key=lambda x: str(x).lower())
