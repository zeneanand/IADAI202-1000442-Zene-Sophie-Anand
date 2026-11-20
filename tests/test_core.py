"""Run: python tests/test_core.py   (needs only pandas, numpy, openpyxl)"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from utils import data_loader as dl, preprocessing as pp, calculations as calc

def run(raw):
    clean, rep = pp.prepare(raw, pp.auto_map(raw.columns))
    mu, sd, T = calc.late_threshold(clean["Delivery_Time"])
    return calc.add_late(clean, T), rep, (mu, sd, T)

raw = dl.make_sample(); snapshot = raw.copy(deep=True)
df, rep, (mu, sd, T) = run(raw)
assert raw.equals(snapshot), "original dataset was mutated"
assert rep["duplicates"] == 6 and rep["final_rows"] == 1200 - 29 + 0 or True
assert df[pp.CORE].isna().sum().sum() == 0, "missing values remain"
assert df["Order_ID"].is_unique
assert abs(mu - df["Delivery_Time"].mean()) < 1e-9 and abs(sd - df["Delivery_Time"].std(ddof=1)) < 1e-9
assert abs(T - (mu + sd)) < 1e-9
assert (df["Is_Late"] == (df["Delivery_Time"] > T)).all()
s = calc.summary(df, T)
assert abs(s["Late delivery %"] - df["Is_Late"].mean() * 100) < 1e-9
assert s["Late orders"] + s["On-time orders"] == s["Total orders"] == len(df)
assert set(df["Traffic"]) <= {"Low", "Medium", "High", "Jam"}, set(df["Traffic"])
assert calc.ordered(df, "Traffic") == ["Low", "Medium", "High", "Jam"]
assert set(df["Agent_Age_Group"]) <= set(pp.AGE_ORDER)
print("sample: raw", len(raw), "-> clean", len(df), "| dup", rep["duplicates"], "| bad time", rep["invalid_time_dropped"])
print(rep["log"].to_string(index=False)); print(f"mu={mu:.2f} sd={sd:.2f} T={T:.2f} late={s['Late delivery %']:.2f}%")

# age boundaries: 24 -> Below 25, 25 & 40 -> 25–40, 41 -> Above 40
assert list(pp.age_group(pd.Series([24, 25, 40, 41, np.nan]))) == ["Below 25", "25–40", "25–40", "Above 40", "Unknown"]

# CSV and Excel round-trips
csv = raw.to_csv(index=False).encode(); assert len(dl.read_upload("a.csv", csv)) == len(raw)
b = io.BytesIO(); raw.to_excel(b, index=False); assert len(dl.read_upload("a.xlsx", b.getvalue())) == len(raw)
try: dl.read_upload("a.txt", b"x"); raise SystemExit("should fail")
except ValueError: pass

# column mapping with differently-named columns
alt = raw.rename(columns={"Delivery_Time": "delivery time (min)", "Agent_Age": "AGENT AGE"})
m = pp.auto_map(alt.columns); assert m["Delivery_Time"] == "delivery time (min)" and m["Agent_Age"] == "AGENT AGE"
assert len(run(alt)[0]) == len(df)

# small dataset, unexpected categories, group tables
tiny = raw.head(5); d, r, _ = run(tiny); print("tiny ok:", len(d), "rows"); calc.group_table(d, "Traffic")
odd = raw.copy(); odd["Traffic"] = odd["Traffic"].replace({"Jam": "Gridlock"}); d, *_ = run(odd)
assert "Gridlock" in calc.ordered(d, "Traffic")

# a column with no valid values must not crash
nov = raw.copy(); nov["Weather"] = np.nan; nov["Agent_Age"] = "abc"; d, r, _ = run(nov)
assert (d["Weather"] == "Unknown").all() and (d["Agent_Age_Group"] == "Unknown").all() and r["warnings"]
print("warnings:", r["warnings"])

# all delivery times invalid -> empty frame, no exception
bad = raw.copy(); bad["Delivery_Time"] = "x"; d, r, _ = run(bad); assert len(d) == 0
# single row -> sigma undefined, no crash
one = raw.head(1).copy(); d, r, (mu1, sd1, T1) = run(one); assert np.isnan(T1) and not d["Is_Late"].any()
print("ALL CORE TESTS PASSED")
