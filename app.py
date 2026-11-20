"""LogiSight Delivery Intelligence – FA-2 Streamlit dashboard.  Run: streamlit run app.py"""
import time
import pandas as pd
import streamlit as st
from utils import calculations as calc, charts as ch, data_loader as dl, insights as ins, preprocessing as pp

st.set_page_config(page_title="LogiSight Delivery Intelligence", page_icon="◧", layout="wide")
st.markdown("""<style>
html, body, [class*="css"] {font-family: Inter, "Segoe UI", Helvetica, Arial, sans-serif;}
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 1.6rem; max-width: 1250px;}
[data-testid="stSidebar"] {background: #F4F7F9; border-right: 1px solid #E1E7ED;}
.brand {font-size: 1.45rem; font-weight: 700; color: #0B1F3A; letter-spacing: -.02em;}
.brand b {color: #0F9D93;} .tag {color: #6B7A8C; font-size: .78rem; margin-bottom: .8rem;}
.kpi {background: #fff; border: 1px solid #E1E7ED; border-radius: 14px; padding: 16px 18px; box-shadow: 0 1px 2px rgba(11,31,58,.04); height: 100%;}
.kl {color: #5B6B7D; font-size: .8rem; font-weight: 600; text-transform: uppercase; letter-spacing: .04em;}
.kv {color: #0B1F3A; font-size: 2rem; font-weight: 700; line-height: 1.25;} .kv span {font-size: .95rem; color: #6B7A8C; margin-left: 4px; font-weight: 500;}
.kn {color: #6B7A8C; font-size: .78rem;}
.pill {display: inline-block; background: #E8F5F4; color: #0B6F68; border-radius: 999px; padding: 3px 12px; font-size: .8rem; margin-right: 6px;}
.pill.warn {background: #FDF0E6; color: #9A4A12;}
.sub {color: #5B6B7D; margin-top: -.6rem;}
</style>""", unsafe_allow_html=True)

PAGES = ["Executive Overview", "Delay Analyzer", "Fleet Performance", "Agent Analytics", "Regional Intelligence",
         "Product Categories", "Data Explorer", "Methodology & Data Quality"]
DESC = {
    PAGES[0]: "Headline delivery KPIs, distribution of delivery times and automatically generated operational insights.",
    PAGES[1]: "How weather and traffic conditions are associated with delivery duration and late deliveries.",
    PAGES[2]: "Compare delivery performance across vehicle types.",
    PAGES[3]: "Explore agent ratings and age groups against delivery time (descriptive, not causal).",
    PAGES[4]: "Find areas and area–traffic combinations with longer deliveries.",
    PAGES[5]: "Compare the spread of delivery times across product categories.",
    PAGES[6]: "Search, filter and export the cleaned and filtered data.",
    PAGES[7]: "How the data was cleaned and how every statistic is calculated.",
}


# ---------- cached loaders (keep the raw data untouched; cleaning runs on a copy) ----------
@st.cache_data(ttl=900, show_spinner="Connecting to Google Sheets…")
def cached_url(url):
    return dl.read_url(url), time.strftime("%d %b %Y, %H:%M:%S")


@st.cache_data(show_spinner=False)
def cached_file(name, data):
    return dl.read_upload(name, data)


@st.cache_data(show_spinner="Cleaning data…")
def cached_prepare(raw, mapping_items):
    return pp.prepare(raw, dict(mapping_items))


def csv_bytes(d):
    return d.to_csv(index=False).encode("utf-8")


def show(fig, note="Not enough valid data for this chart with the current filters."):
    if fig is None:
        st.info(note)
    else:
        st.plotly_chart(fig, width="stretch")


def table(t, **kw):
    st.dataframe(t.round(2), width="stretch", hide_index=True, **kw)


def kpi(col, label, value, unit, note):
    col.markdown(f'<div class="kpi"><div class="kl">{label}</div><div class="kv">{value}<span>{unit}</span></div>'
                 f'<div class="kn">{note}</div></div>', unsafe_allow_html=True)


def fmt(x, nd=1):
    return "—" if pd.isna(x) else f"{x:,.{nd}f}"


# ---------- sidebar: brand, navigation, data source ----------
sb = st.sidebar
sb.markdown('<div class="brand">Logi<b>Sight</b></div><div class="tag">Delivery Intelligence · FA-2</div>', unsafe_allow_html=True)
page = sb.radio("Navigate", PAGES, label_visibility="collapsed")
sb.divider()
sb.markdown("**Data source**")
source = sb.radio("Source", ["Google Sheets", "Upload CSV / Excel", "Demo data (synthetic)"], label_visibility="collapsed")
sb.button("Refresh data", on_click=st.cache_data.clear, width="stretch")

raw, src_label, refreshed = None, "", "—"
try:
    if source == "Google Sheets":
        raw, refreshed = cached_url(dl.SHEET_URL)
        src_label = "Google Sheets (live CSV)"
    elif source.startswith("Upload"):
        up = sb.file_uploader("CSV or Excel (.xlsx)", type=["csv", "xlsx"])
        if up:
            raw, src_label, refreshed = cached_file(up.name, up.getvalue()), up.name, "Uploaded this session"
    else:
        raw, src_label, refreshed = dl.make_sample(), "Synthetic demo data", "Generated this session"
except Exception as e:
    sb.error(f"Could not load data: {e}")
    if source == "Google Sheets":
        sb.caption("The sheet may be private or offline. Choose 'Upload' or 'Demo data' instead.")

if raw is None or raw.empty:
    st.markdown('<div class="brand">Logi<b>Sight</b> Delivery Intelligence</div>', unsafe_allow_html=True)
    st.info("No data loaded yet. Pick a source in the sidebar: connect Google Sheets, upload a CSV/Excel file, or try the demo data.")
    st.markdown("**Expected columns:** " + ", ".join(pp.CORE) + " (Order_ID is optional).")
    st.download_button("Download synthetic sample CSV", csv_bytes(dl.make_sample()), "sample_delivery_data.csv", "text/csv")
    st.stop()

# ---------- column validation / mapping ----------
mapping = pp.auto_map(raw.columns)
missing = [c for c in pp.CORE if c not in mapping]
if missing:
    with sb.expander("Map missing columns", expanded=True):
        for c in missing:
            free = [x for x in raw.columns if x not in mapping.values()]
            pick = st.selectbox(f"Which column is {c}?", ["— select —"] + free, key=f"map_{c}")
            if pick != "— select —":
                mapping[c] = pick
    still = [c for c in pp.CORE if c not in mapping]
    if still:
        st.error(f"Required column(s) not found: {', '.join(still)}. Use 'Map missing columns' in the sidebar, or upload a file containing them.")
        st.caption("Columns found in your data: " + ", ".join(map(str, raw.columns)))
        st.stop()

clean, report = cached_prepare(raw, tuple(sorted(mapping.items())))
if clean.empty:
    st.error("No valid delivery records remain after cleaning (Delivery_Time must be a positive number). See Methodology & Data Quality.")
    st.stop()
mu_all, sd_all, T = calc.late_threshold(clean["Delivery_Time"])   # threshold fixed on the full cleaned dataset
clean = calc.add_late(clean, T)

# ---------- global filters ----------
sig = f"{src_label}_{len(clean)}"
FILTERS = [("Weather", "Weather"), ("Traffic", "Traffic"), ("Vehicle", "Vehicle"), ("Area", "Area"),
           ("Category", "Product category"), ("Agent_Age_Group", "Agent age group"), ("Late_Status", "Delivery status")]
keys = [f"f_{sig}_{c}" for c, _ in FILTERS]
sb.divider()
sb.markdown("**Filters**")
mask, active = pd.Series(True, index=clean.index), []
for (col, label), key in zip(FILTERS, keys):
    opts = calc.ordered(clean, col)
    sel = sb.multiselect(label, opts, default=opts, key=key)
    mask &= clean[col].isin(sel)
    if len(sel) < len(opts):
        active.append(f"{label}: {len(sel)}/{len(opts)}")
sb.button("Reset all filters", on_click=lambda: [st.session_state.pop(k, None) for k in keys], width="stretch")
df = clean[mask]
sb.markdown(f'<span class="pill{" warn" if active else ""}">{len(df):,} of {len(clean):,} records</span>', unsafe_allow_html=True)
sb.caption("Filters active: " + "; ".join(active) if active else "No filters active (all records shown).")

# ---------- header ----------
st.markdown(f"## {page}")
st.markdown(f'<p class="sub">{DESC[page]}</p>', unsafe_allow_html=True)
st.markdown(f'<span class="pill">Source: {src_label}</span><span class="pill">Last refresh: {refreshed}</span>'
            + (f'<span class="pill warn">Filters active · {len(df):,} records</span>' if active else ""), unsafe_allow_html=True)
for w in report["warnings"]:
    st.warning(w)
if df.empty:
    st.warning("No records match the current filters. Widen the selection or press 'Reset all filters'.")
    st.stop()
S = calc.summary(df, T)


def kpi_row():
    c = st.columns(5)
    kpi(c[0], "Total deliveries", f"{S['Total orders']:,}", "orders", "Valid orders after filters")
    kpi(c[1], "Avg delivery time", fmt(S["Mean (μ)"]), "min", "Mean of filtered orders")
    kpi(c[2], "Late deliveries", fmt(S["Late delivery %"]), "%", f"Above T_late = {fmt(T)} min")
    kpi(c[3], "Median delivery time", fmt(S["Median"]), "min", "Middle value, robust to outliers")
    kpi(c[4], "On-time deliveries", f"{S['On-time orders']:,}", "orders", "At or below T_late")
    st.write("")


def pattern(t, col, val="Mean", hi=True, unit="min"):
    t = t[t["Orders"] >= pp_min]
    if len(t) < 2:
        return
    r = t.loc[t[val].idxmax() if hi else t[val].idxmin()]
    st.caption(f"Observed: '{r[col]}' shows the {'highest' if hi else 'lowest'} {val.replace('_', ' ').lower()} "
               f"({r[val]:.1f} {unit}) among groups with ≥ {pp_min} orders.")


pp_min = ins.MIN_GROUP
two = st.columns(2)

# ---------- pages ----------
if page == PAGES[0]:
    kpi_row()
    with two[0]: show(ch.histogram(df, T))
    with two[1]: show(ch.late_bar(df, "Traffic", "Late deliveries by traffic (%)"))
    st.markdown("### Operational Insights")
    for line in ins.generate(df):
        st.markdown(f"- {line}")
    st.caption(f"T_late = μ + σ = {fmt(mu_all, 2)} + {fmt(sd_all, 2)} = {fmt(T, 2)} min, computed once on all {len(clean):,} cleaned orders. "
               "It is a project-defined statistical threshold, not an official company SLA.")

elif page == PAGES[1]:
    kpi_row()
    show(ch.delay_analyzer(df))
    gt = calc.group_table(df, "Weather")
    pattern(gt, "Weather")
    with two[0]: show(ch.late_bar(df, "Traffic", "Late deliveries by traffic (%)"))
    with two[1]: show(ch.box_by(df, "Traffic", "Delivery time by traffic condition", T))
    with st.expander("Weather and traffic statistics"):
        table(calc.group_table(df, ["Weather", "Traffic"]))

elif page == PAGES[2]:
    kpi_row()
    vt = calc.group_table(df, "Vehicle")
    show(ch.vehicle_comparison(df))
    pattern(vt, "Vehicle", hi=False)
    with two[0]: show(ch.mean_bar(df, "Vehicle", "Deliveries by vehicle type", "Orders"))
    with two[1]: show(ch.late_bar(df, "Vehicle", "Late deliveries by vehicle (%)"))
    sort_by = st.selectbox("Sort table by", ["Mean", "Median", "Orders", "Late_%", "Std"])
    table(vt.sort_values(sort_by, ascending=sort_by in ("Mean", "Median", "Std")))

elif page == PAGES[3]:
    kpi_row()
    fig, sampled = ch.agent_scatter(df, T)
    show(fig)
    if sampled:
        st.caption("Chart shows a random sample of 1,500 points for smooth rendering. All KPIs and tables use every filtered record.")
    g = calc.group_table(df, "Agent_Age_Group").merge(df.groupby("Agent_Age_Group")["Agent_Rating"].mean().rename("Avg_Rating").reset_index())
    with two[0]: show(ch.box_by(df, "Agent_Age_Group", "Delivery time by age group", T))
    with two[1]: show(ch.late_bar(df, "Agent_Age_Group", "Late deliveries by age group (%)"))
    table(g[["Agent_Age_Group", "Orders", "Avg_Rating", "Mean", "Median", "Late_%"]])
    if df["Agent_Rating"].nunique() > 1:
        st.caption(f"Pearson correlation between rating and delivery time: r = {df['Agent_Rating'].corr(df['Delivery_Time']):.2f}. This is an association, not evidence of cause.")

elif page == PAGES[4]:
    kpi_row()
    show(ch.area_heatmap(df))
    at = calc.group_table(df, "Area")
    pattern(at, "Area")
    with two[0]: show(ch.mean_bar(df, "Area", "Average delivery time by area (min)"))
    with two[1]: show(ch.late_bar(df, "Area", "Late deliveries by area (%)"))
    show(ch.mean_bar(df, "Area", "Order count by area", "Orders"))
    table(at.sort_values("Mean", ascending=False))

elif page == PAGES[5]:
    kpi_row()
    show(ch.category_box(df, T))
    ct = calc.group_table(df, "Category")
    pattern(ct, "Category")
    with two[0]: show(ch.mean_bar(df, "Category", "Average delivery time by category (min)"))
    with two[1]: show(ch.mean_bar(df, "Category", "Median delivery time by category (min)", "Median"))
    table(ct.sort_values("Mean", ascending=False))

elif page == PAGES[6]:
    q = st.text_input("Search all text columns", placeholder="e.g. Jam, Van, ORD1001…")
    view = df
    if q:
        txt = df.astype(str).apply(lambda s: s.str.contains(q, case=False, regex=False)).any(axis=1)
        view = df[txt]
    st.caption(f"Showing {len(view):,} of {len(df):,} filtered records (click a column header to sort).")
    st.dataframe(view, width="stretch", hide_index=True, height=420)
    summ = pd.DataFrame({"Metric": list(S.keys()), "Value": [round(v, 4) if isinstance(v, float) else v for v in S.values()]})
    report_txt = "LogiSight analytical summary\n" + "\n".join(f"{k}: {fmt(v, 2)}" for k, v in S.items()) + \
        "\n\nOperational insights\n" + "\n".join("- " + l.replace("**", "") for l in ins.generate(df))
    c = st.columns(5)
    c[0].download_button("Cleaned dataset", csv_bytes(clean), "cleaned_dataset.csv", "text/csv", width="stretch")
    c[1].download_button("Filtered dataset", csv_bytes(df), "filtered_dataset.csv", "text/csv", width="stretch")
    c[2].download_button("Statistical summary", csv_bytes(summ), "statistical_summary.csv", "text/csv", width="stretch")
    c[3].download_button("Late deliveries", csv_bytes(df[df["Is_Late"]]), "late_deliveries.csv", "text/csv", width="stretch")
    c[4].download_button("Insights report", report_txt.encode("utf-8"), "analytical_summary.txt", "text/plain", width="stretch")
    st.markdown("### Statistical summary (filtered data)")
    table(summ)

else:
    r = report
    c = st.columns(5)
    kpi(c[0], "Raw records", f"{r['raw_rows']:,}", "", "Rows in the source")
    kpi(c[1], "Duplicates removed", f"{r['duplicates']:,}", "", "Repeated Order_ID")
    kpi(c[2], "Invalid time excluded", f"{r['invalid_time_dropped']:,}", "", "Missing/invalid Delivery_Time")
    kpi(c[3], "Cleaned records", f"{r['final_rows']:,}", "", "Used in all analysis")
    kpi(c[4], "Invalid values", f"{sum(r['invalid_counts'].values()):,}", "", "Text or out-of-range numbers")
    st.markdown("### Cleaning actions")
    if r["log"].empty:
        st.success("No cleaning actions were needed.")
    else:
        table(r["log"])
    a, b = st.columns(2)
    with a:
        st.markdown("### Missing values (before → after)")
        table(pd.DataFrame({"Column": r["missing_before"].index, "Before": r["missing_before"].values, "After": r["missing_after"].values}))
    with b:
        st.markdown("### Column data types")
        table(pd.DataFrame({"Column": clean.columns, "Type": clean.dtypes.astype(str).values}))
    st.markdown("### Records before and after cleaning")
    a, b = st.columns(2)
    a.caption("Original (unchanged)"); a.dataframe(raw.head(8), width="stretch", hide_index=True)
    b.caption("Cleaned working copy"); b.dataframe(clean.head(8), width="stretch", hide_index=True)
    st.markdown("### Statistical methodology")
    st.latex(r"\mu=\frac{1}{n}\sum_{i=1}^{n}t_i \qquad \sigma=\sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(t_i-\mu)^2} \qquad T_{late}=\mu+\sigma")
    st.latex(r"\text{Late \%}=\frac{\#\{t_i>T_{late}\}}{n_{valid}}\times 100 \qquad IQR=Q_3-Q_1")
    st.markdown(f"""
- **Convention:** the *sample* standard deviation (divide by n − 1) is used everywhere. For this data μ = {fmt(mu_all, 2)} min, σ = {fmt(sd_all, 2)} min, T_late = {fmt(T, 2)} min.
- **Late threshold:** an order is late when Delivery_Time > μ + σ. This is a statistical threshold defined for this project, **not an official company SLA**. It is computed once on the full cleaned dataset so the definition of "late" stays constant while filters change; KPIs, percentages and charts respond to filters.
- **Why μ + σ:** if times were roughly normal, about 16% of orders would exceed it, so it flags unusually slow deliveries relative to this dataset.
- **Age groups:** Below 25 (age < 25), 25–40 (25 ≤ age ≤ 40), Above 40 (age > 40); missing ages are median-imputed first.
- **Cleaning choices:** median for numeric gaps (robust to outliers), mode for categorical gaps. Delivery_Time is the outcome variable, so rows without a valid value are excluded rather than imputed. Valid ranges: time > 0, rating 0–5, age 1–100.
- **Interpretation:** all findings are descriptive associations. They do not show that weather, traffic, vehicle or agent characteristics *cause* delays.
- **Limitations:** imputation can understate variability; groups with few orders give unstable averages (insights need ≥ {ins.MIN_GROUP} orders per group and ≥ {ins.MIN_TOTAL} overall); scatter plots sample 1,500 points for display only; no time or distance variables are available to control for confounding.
""")
    st.markdown("### FA-1 plan → FA-2 implementation")
    table(pd.DataFrame({"FA-1 planned feature": ["Delay Analyzer", "Vehicle Comparison", "Agent Performance Insights", "Regional Bottleneck Finder", "Category Visualizer", "Sidebar filters", "Data logic flow"],
                        "Implemented as": [PAGES[1], PAGES[2], PAGES[3], PAGES[4], PAGES[5], "Global sidebar filters (7 filters + reset)", "utils/preprocessing.py → calculations.py → charts.py"]}))
