"""Operational insights computed from the filtered data. Neutral, descriptive language only."""
import pandas as pd
from . import calculations as calc

MIN_TOTAL, MIN_GROUP = 30, 5


def _groups(df, col, value="Mean", rows_ok=MIN_GROUP):
    g = calc.group_table(df, col)
    return g[g["Orders"] >= rows_ok]


def generate(df: pd.DataFrame) -> list:
    if len(df) < MIN_TOTAL:
        return [f"Only {len(df)} orders match the current filters; at least {MIN_TOTAL} are needed before insights are shown."]
    out = []
    g = _groups(df, "Weather")
    if len(g) >= 2:
        r = g.loc[g["Mean"].idxmax()]
        out.append(f"**Weather:** '{r['Weather']}' shows the highest average delivery time ({r['Mean']:.1f} min, {int(r['Orders'])} orders).")
    g = _groups(df, "Traffic")
    if len(g) >= 2:
        r = g.loc[g["Late_%"].idxmax()]
        out.append(f"**Traffic:** '{r['Traffic']}' has the highest late-delivery percentage ({r['Late_%']:.1f}%) among traffic conditions with enough orders.")
    g = _groups(df, "Vehicle")
    if len(g) >= 2:
        r = g.loc[g["Mean"].idxmin()]
        out.append(f"**Vehicles:** '{r['Vehicle']}' has the lowest average delivery time ({r['Mean']:.1f} min). This is a descriptive comparison and does not account for differences in routes or order mix.")
    g = _groups(df, "Area")
    if len(g) >= 2:
        r = g.loc[g["Mean"].idxmax()]
        out.append(f"**Areas:** '{r['Area']}' shows the highest average delivery time ({r['Mean']:.1f} min).")
    g = _groups(df, "Category")
    if len(g) >= 2:
        r = g.loc[g["Std"].idxmax()]
        out.append(f"**Categories:** '{r['Category']}' has the greatest spread in delivery times (σ = {r['Std']:.1f} min).")
    g = _groups(df, "Agent_Age_Group")
    g = g[g["Agent_Age_Group"] != "Unknown"]
    if len(g) >= 2:
        hi, lo = g.loc[g["Mean"].idxmax()], g.loc[g["Mean"].idxmin()]
        out.append(f"**Agent age groups:** averages range from {lo['Mean']:.1f} min ('{lo['Agent_Age_Group']}') to {hi['Mean']:.1f} min ('{hi['Agent_Age_Group']}'). Differences are descriptive, not causal.")
    if df["Agent_Rating"].nunique() > 1 and df["Delivery_Time"].nunique() > 1:
        r = df["Agent_Rating"].corr(df["Delivery_Time"])
        strength = "weak" if abs(r) < .3 else "moderate" if abs(r) < .6 else "strong"
        out.append(f"**Rating vs time:** Pearson r = {r:.2f}, a {strength} {'negative' if r < 0 else 'positive'} linear association. Correlation does not imply causation.")
    return out
