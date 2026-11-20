"""Data sources: Google Sheets CSV, uploaded CSV/Excel, and a clearly-labelled synthetic demo set."""
import io
import numpy as np
import pandas as pd

# Source URL taken from the notebook (delivery_analysis_fa2.ipynb)
SHEET_URL = "https://docs.google.com/spreadsheets/d/11cYv3lIhqTo9aIWb0llt0eNHho6cJcaRhsOfzyOZLss/export?format=csv"


def read_url(url: str) -> pd.DataFrame:
    return pd.read_csv(url)


def read_upload(name: str, data: bytes) -> pd.DataFrame:
    lower = name.lower()
    if lower.endswith(".csv"):
        return pd.read_csv(io.BytesIO(data))
    if lower.endswith((".xlsx", ".xlsm")):
        return pd.read_excel(io.BytesIO(data), engine="openpyxl")
    raise ValueError("Unsupported file type. Please upload a .csv or .xlsx file.")


def make_sample(n: int = 1200, seed: int = 7) -> pd.DataFrame:
    """SYNTHETIC demo data (not real deliveries). Deliberately includes messy values
    (blanks, stray spaces, text in numeric fields, duplicates) to demonstrate cleaning."""
    rng = np.random.default_rng(seed)
    traffic = rng.choice(["Low", "Medium", "High", "Jam"], n, p=[.25, .35, .28, .12])
    weather = rng.choice(["Sunny", "Cloudy", "Fog", "Stormy", "Windy"], n)
    vehicle = rng.choice(["Motorcycle", "Scooter", "Van", "Bicycle"], n, p=[.5, .3, .15, .05])
    area = rng.choice(["Urban", "Metropolitian", "Semi-Urban", "Other"], n)
    category = rng.choice(["Clothing", "Electronics", "Grocery", "Books", "Toys", "Home"], n)
    base = pd.Series(traffic).map({"Low": 18, "Medium": 26, "High": 34, "Jam": 44}).to_numpy()
    base = base + pd.Series(weather).map({"Sunny": 0, "Cloudy": 2, "Fog": 5, "Stormy": 8, "Windy": 3}).to_numpy()
    time = np.clip(base + rng.normal(0, 8, n), 8, None).round(0)
    df = pd.DataFrame({
        "Order_ID": [f"ORD{100000 + i}" for i in range(n)],
        "Delivery_Time": time.astype(object),
        "Weather": weather, "Traffic": traffic, "Vehicle": vehicle,
        "Agent_Rating": rng.uniform(3.2, 5.0, n).round(1).astype(object),
        "Agent_Age": rng.integers(18, 52, n).astype(object),
        "Area": area, "Category": category,
    })
    df.loc[rng.choice(n, 25, replace=False), "Delivery_Time"] = np.nan
    df.loc[rng.choice(n, 4, replace=False), "Delivery_Time"] = "n/a"
    df.loc[rng.choice(n, 30, replace=False), "Agent_Rating"] = np.nan
    df.loc[rng.choice(n, 30, replace=False), "Agent_Age"] = np.nan
    df.loc[rng.choice(n, 15, replace=False), "Weather"] = np.nan
    df.loc[rng.choice(n, 40, replace=False), "Traffic"] = df["Traffic"] + " "
    df.loc[rng.choice(n, 40, replace=False), "Vehicle"] = df["Vehicle"].str.lower()
    return pd.concat([df, df.sample(6, random_state=1)], ignore_index=True)
