"""Analyzing Last mile Delivery Data for Performance Insights – FA-2 Streamlit Dashboard.
Run: streamlit run app.py
"""

import time
import numpy as np
import pandas as pd
import streamlit as st
from utils import calculations as calc, charts as ch, data_loader as dl, insights as ins, preprocessing as pp

# -----------------------------------------------------------------------------
# Page Configuration & Metadata
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Analyzing Last mile Delivery Data for Performance Insights",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Global CSS & High-Contrast Design System
# -----------------------------------------------------------------------------
st.markdown("""<style>
html, body, [class*="css"] {
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}

#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 1.2rem; max-width: 1300px;}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #F4F7F9;
    border-right: 1px solid #E1E7ED;
}

/* Sidebar Text & Labels */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] label p,
[data-testid="stSidebar"] label span,
[data-testid="stSidebar"] .stCaption {
    color: #263445 !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong {
    color: #0B1F3A !important;
    font-weight: 700;
}

/* Sidebar multiselect surfaces */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #2B2926 !important;
    border-color: #2B2926 !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] > div > div:last-child,
[data-testid="stSidebar"] [data-baseweb="select"] > div > div:last-child > div {
    background: #2B2926 !important;
    border-color: #2B2926 !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] input {
    background: transparent !important;
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] svg {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}

/* Sidebar buttons */
[data-testid="stSidebar"] .stButton button,
[data-testid="stSidebar"] .stButton button p,
[data-testid="stSidebar"] .stButton button [data-testid="stMarkdownContainer"] p {
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] hr {
    border-color: #D5DDE5;
}

.brand-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #0B1F3A;
    line-height: 1.25;
    letter-spacing: -0.01em;
    margin-bottom: 4px;
}
.brand-title b { color: #0F9D93; }
.brand-sub { color: #5B6B7D; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.8rem; }

/* KPI Cards */
.kpi {
    background: #FFFFFF;
    border: 1px solid #E1E7ED;
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 1px 3px rgba(11, 31, 58, 0.05);
    height: 100%;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.kpi:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 14px rgba(11, 31, 58, 0.08);
}
.kl {
    color: #5B6B7D;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.kv {
    color: #0B1F3A;
    font-size: 2.1rem;
    font-weight: 800;
    line-height: 1.2;
    margin: 4px 0 2px 0;
}
.kv span {
    font-size: 0.95rem;
    color: #5B6B7D;
    margin-left: 4px;
    font-weight: 500;
}
.kn {
    color: #5B6B7D;
    font-size: 0.76rem;
    line-height: 1.35;
}

/* Pills & Badges */
.pill {
    display: inline-block;
    background: #E8F5F4;
    color: #0B6F68;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-right: 6px;
    border: 1px solid #B8E2DF;
}
.pill.warn {
    background: #FDF0E6;
    color: #9A4A12;
    border-color: #F8CCA8;
}

.sub {
    color: #5B6B7D;
    font-size: 0.92rem;
    margin-top: -0.4rem;
    margin-bottom: 0.8rem;
}

.section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 20px 0 12px 0;
    border-bottom: 2px solid #E1E7ED;
    padding-bottom: 6px;
}
.section-header h3 {
    margin: 0;
    color: #0B1F3A;
    font-size: 1.15rem;
    font-weight: 700;
}

/* Dynamic Filter Detection Popup Card */
.filter-change-popup {
    position: fixed;
    top: 65px;
    right: 24px;
    z-index: 999999;
    background: #FFFFFF;
    border: 2px solid #0F9D93;
    border-radius: 12px;
    padding: 12px 16px;
    box-shadow: 0 10px 25px rgba(11, 31, 58, 0.15);
    max-width: 320px;
    animation: slideIn 0.35s ease-out;
}
@keyframes slideIn {
    from { transform: translateX(110%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

.detection-banner {
    background: #E8F5F4;
    border-left: 4px solid #0F9D93;
    border-radius: 0 10px 10px 0;
    padding: 10px 14px;
    margin-bottom: 14px;
    font-size: 0.84rem;
    color: #0B1F3A;
    display: flex;
    align-items: center;
    gap: 10px;
}

.sim-notice {
    background: #FEF3C7;
    border-left: 4px solid #F59E0B;
    border-radius: 0 10px 10px 0;
    padding: 10px 14px;
    margin-bottom: 14px;
    font-size: 0.84rem;
    color: #78350F;
    display: flex;
    align-items: center;
    gap: 10px;
}
</style>""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Page Navigation Routes
# -----------------------------------------------------------------------------
PAGES = [
    "Executive Overview",
    "Delay Analyzer",
    "Fleet Performance",
    "Agent Analytics",
    "Regional Intelligence",
    "Product Categories",
    "Data Explorer",
    "Methodology & Data Quality"
]

DESC = {
    PAGES[0]: "Headline delivery KPIs, monthly trend line chart, delivery time histogram, late % breakdown, and agent territory distribution.",
    PAGES[1]: "How weather and traffic conditions are associated with delivery duration and late deliveries.",
    PAGES[2]: "Compare delivery performance across vehicle fleet types.",
    PAGES[3]: "Explore agent ratings and age groups against delivery turnaround speed.",
    PAGES[4]: "Find areas and area–traffic combinations with longer deliveries.",
    PAGES[5]: "Compare the spread of delivery times across product categories.",
    PAGES[6]: "Search, filter and export the cleaned and filtered data.",
    PAGES[7]: "How the data was cleaned and how every statistic is calculated.",
}

# -----------------------------------------------------------------------------
# Cached Data Loaders
# -----------------------------------------------------------------------------
@st.cache_data(ttl=900, show_spinner="Connecting to Data Source…")
def cached_url(url):
    return dl.read_url(url), time.strftime("%d %b %Y, %H:%M:%S")

@st.cache_data(show_spinner=False)
def cached_file(name, data):
    return dl.read_upload(name, data)

@st.cache_data(show_spinner="Cleaning & preparing data…")
def cached_prepare(raw, mapping_items):
    return pp.prepare(raw, dict(mapping_items))

def csv_bytes(d):
    return d.to_csv(index=False).encode("utf-8")

def show(fig, note="Not enough valid data for this chart with the current filters."):
    if fig is None:
        st.info(note)
    else:
        st.plotly_chart(fig, use_container_width=True, theme=None)

def table(t, **kw):
    st.dataframe(t.round(2), use_container_width=True, hide_index=True, **kw)

def kpi(col, label, value, unit, note):
    col.markdown(f'<div class="kpi"><div class="kl">{label}</div><div class="kv">{value}<span>{unit}</span></div>'
                 f'<div class="kn">{note}</div></div>', unsafe_allow_html=True)

def fmt(x, nd=1):
    return "—" if pd.isna(x) else f"{x:,.{nd}f}"

# -----------------------------------------------------------------------------
# Sidebar: Branding, Navigation & Data Source
# -----------------------------------------------------------------------------
sb = st.sidebar
sb.markdown('<div class="brand-title">Analyzing <b>Last mile Delivery</b> Data</div>'
            '<div class="brand-sub">For Performance Insights · FA-2</div>', unsafe_allow_html=True)

page = sb.radio("Navigate", PAGES, label_visibility="collapsed")
sb.divider()

sb.markdown("**Data source**")
source = sb.radio("Source", ["Google Sheets", "Upload CSV / Excel", "Demo data (synthetic)"], label_visibility="collapsed")
sb.button("Refresh data", on_click=st.cache_data.clear, use_container_width=True)

raw, src_label, refreshed = None, "", "—"
try:
    if source == "Google Sheets":
        raw, refreshed = cached_url(dl.SHEET_URL)
        src_label = "Google Sheets / Remote CSV"
    elif source.startswith("Upload"):
        up = sb.file_uploader("CSV or Excel (.xlsx)", type=["csv", "xlsx"])
        if up:
            raw, src_label, refreshed = cached_file(up.name, up.getvalue()), up.name, "Uploaded this session"
    else:
        raw, src_label, refreshed = dl.make_sample(), "Synthetic demo data", "Generated this session"
except Exception as e:
    sb.error(f"Could not load data: {e}")
    if source == "Google Sheets":
        sb.caption("Remote data source offline or unavailable. Switched to local dataset.")
        try:
            raw = pd.read_csv("delivery_data.csv")
            src_label = "Local delivery_data.csv"
            refreshed = time.strftime("%d %b %Y, %H:%M:%S")
        except Exception:
            raw = dl.make_sample()
            src_label = "Synthetic demo data"

if raw is None or raw.empty:
    st.markdown('<h2 style="color:#0B1F3A;">Analyzing Last mile Delivery Data for Performance Insights</h2>', unsafe_allow_html=True)
    st.info("No data loaded yet. Pick a source in the sidebar: connect Google Sheets, upload a CSV/Excel file, or try the demo data.")
    st.markdown("**Expected columns:** " + ", ".join(pp.CORE) + " (Order_ID is optional).")
    st.download_button("Download synthetic sample CSV", csv_bytes(dl.make_sample()), "sample_delivery_data.csv", "text/csv")
    st.stop()

# -----------------------------------------------------------------------------
# Column Auto-Mapping & Validation
# -----------------------------------------------------------------------------
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
        st.error(f"Required column(s) not found: {', '.join(still)}. Use 'Map missing columns' in the sidebar.")
        st.stop()

# Clean & Prepare Dataset
clean, report = cached_prepare(raw, tuple(sorted(mapping.items())))
if clean.empty:
    st.error("No valid delivery records remain after cleaning. Please check raw file.")
    st.stop()

# Fixed Statistical Late Threshold on Cleaned Population
mu_all, sd_all, T = calc.late_threshold(clean["Delivery_Time"])
clean = calc.add_late(clean, T)

# -----------------------------------------------------------------------------
# Global Sidebar Filters
# -----------------------------------------------------------------------------
sig = f"{src_label}_{len(clean)}"
FILTERS = [
    ("Weather", "Weather"),
    ("Traffic", "Traffic"),
    ("Vehicle", "Vehicle"),
    ("Area", "Area"),
    ("Category", "Product category"),
    ("Agent_Age_Group", "Agent age group"),
    ("Late_Status", "Delivery status")
]
keys = [f"f_{sig}_{c}" for c, _ in FILTERS]

sb.divider()
sb.markdown("**Filters**")
mask, active = pd.Series(True, index=clean.index), []
current_filter_selections = {}

for (col, label), key in zip(FILTERS, keys):
    opts = calc.ordered(clean, col)
    sel = sb.multiselect(label, opts, default=opts, key=key)
    current_filter_selections[col] = tuple(sel)
    mask &= clean[col].isin(sel)
    if len(sel) < len(opts):
        active.append(f"{label}: {len(sel)}/{len(opts)}")

sb.button("Reset all filters", on_click=lambda: [st.session_state.pop(k, None) for k in keys], use_container_width=True)

df = clean[mask]
is_simulated = False

# Zero-Blank-Screen Guarantee: Synthesize cohort if filter intersection has 0 historical orders
if df.empty:
    is_simulated = True
    df = calc.synthesize_cohort_for_filters(current_filter_selections, n_records=25, threshold=T)
    sb.markdown(f'<span class="pill warn">⚡ Adaptive Simulation: 25 calibrated records</span>', unsafe_allow_html=True)
    sb.caption("Zero historical rows for this hyper-specific filter combo; synthesized calibrated cohort.")
else:
    sb.markdown(f'<span class="pill{" warn" if active else ""}">{len(df):,} of {len(clean):,} records</span>', unsafe_allow_html=True)
    sb.caption("Filters active: " + "; ".join(active) if active else "No filters active (all records shown).")

# -----------------------------------------------------------------------------
# FILTER CHANGE & GRAPH VALUE DETECTION ENGINE (Toast & Pop-Up Card)
# -----------------------------------------------------------------------------
S = calc.summary(df, T)

curr_filter_signature = tuple((k, current_filter_selections[k]) for k in sorted(current_filter_selections.keys()))
prev_filter_signature = st.session_state.get("prev_filter_signature", None)
prev_metrics = st.session_state.get("prev_metrics", None)

filter_changed = (prev_filter_signature is not None) and (prev_filter_signature != curr_filter_signature)
detected_shift = None

if filter_changed and prev_metrics:
    delta_time = S["Mean (μ)"] - prev_metrics["mean"]
    delta_late = S["Late delivery %"] - prev_metrics["late_pct"]
    delta_count = len(df) - prev_metrics["count"]
    pct_of_total = (len(df) / len(clean)) * 100.0

    detected_shift = {
        "delta_time": delta_time,
        "delta_late": delta_late,
        "delta_count": delta_count,
        "curr_time": S["Mean (μ)"],
        "curr_late": S["Late delivery %"],
        "pct_of_total": pct_of_total,
        "count": len(df)
    }

    st.toast(
        f"🔔 **Graph Shift Detected!**\n\n"
        f"• **Avg Delivery Time:** {S['Mean (μ)']:.1f}m ({delta_time:+.1f}m)\n"
        f"• **Late Delivery Rate:** {S['Late delivery %']:.1f}% ({delta_late:+.1f}%)\n"
        f"• **Active Orders:** {len(df):,} ({pct_of_total:.1f}% slice)\n"
        f"All graph values updated!",
        icon="📊"
    )

st.session_state["prev_filter_signature"] = curr_filter_signature
st.session_state["prev_metrics"] = {
    "mean": S["Mean (μ)"],
    "late_pct": S["Late delivery %"],
    "count": len(df)
}

# -----------------------------------------------------------------------------
# Main Page Header & Title
# -----------------------------------------------------------------------------
st.markdown('<h1 style="color: #0B1F3A; font-size: 2.1rem; font-weight: 800; margin: 0 0 4px 0; letter-spacing: -0.02em;">'
            'Analyzing Last mile Delivery Data for Performance Insights</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="sub">{DESC[page]}</p>', unsafe_allow_html=True)

# Context Pills
st.markdown(
    f'<span class="pill">Source: {src_label}</span>'
    f'<span class="pill">Refreshed: {refreshed}</span>'
    + (f'<span class="pill warn">Active Slice: {len(df):,} records ({(len(df)/len(clean))*100:.1f}%)</span>' if active and not is_simulated else
       ('<span class="pill warn">⚡ Adaptive Synthetic Simulation: 25 records</span>' if is_simulated else '<span class="pill">Full Dataset: 100%</span>')),
    unsafe_allow_html=True
)

for w in report.get("warnings", []):
    st.warning(w)

# Adaptive Simulation Alert Banner (Shown when user isolates a combination with zero historical orders)
if is_simulated:
    st.markdown("""
    <div class="sim-notice">
        <span style="font-size:1.15rem;">🔮</span>
        <div>
            <strong>AI Predictive Micro-Simulation Active:</strong> The selected filter combination is a rare operational scenario 
            with 0 historical logs in this dataset slice. <b>25 calibrated benchmark orders</b> have been synthesized based on your exact filter selections 
            so all graphs, distributions, and percentages continue to render seamlessly.
        </div>
    </div>
    """, unsafe_allow_html=True)

# Floating Pop-up Card in Top-Right Corner (when change is detected)
if detected_shift:
    st.markdown(f"""
    <div class="filter-change-popup">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:700; color:#0B1F3A; font-size:0.86rem;">⚡ Graph Values Updated</span>
            <span style="background:#0F9D93; color:#fff; border-radius:10px; font-size:0.68rem; font-weight:700; padding:2px 7px;">DETECTED</span>
        </div>
        <div style="font-size:0.80rem; color:#263445; margin-top:8px; line-height:1.45;">
            <b>Late Deliveries:</b> <span style="color:#D9534F; font-weight:700;">{detected_shift['curr_late']:.1f}%</span> 
            ({detected_shift['delta_late']:+.1f}%)<br>
            <b>Avg Delivery Time:</b> <b>{detected_shift['curr_time']:.1f} min</b> 
            ({detected_shift['delta_time']:+.1f}m)<br>
            <b>Active Dataset:</b> {detected_shift['count']:,} orders ({detected_shift['pct_of_total']:.1f}% share)
        </div>
        <div style="font-size:0.72rem; color:#5B6B7D; margin-top:6px; font-style:italic;">
            Values & percentages refreshed on all charts.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Visible In-Page Detection Banner
    st.markdown(f"""
    <div class="detection-banner">
        <span>⚡</span>
        <div>
            <strong>Filter Modification Detected:</strong> Graph values updated! 
            Current <b>Avg Delivery Time: {detected_shift['curr_time']:.1f}m</b> ({detected_shift['delta_time']:+.1f}m), 
            <b>Late SLA Rate: {detected_shift['curr_late']:.1f}%</b> ({detected_shift['delta_late']:+.1f}%), 
            accounting for <b>{detected_shift['count']:,} orders</b> ({detected_shift['pct_of_total']:.1f}% of total).
        </div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# KPI Row Component (5 Core Operational Cards)
# -----------------------------------------------------------------------------
def kpi_row():
    c = st.columns(5)
    kpi(c[0], "Total deliveries", f"{S['Total orders']:,}", "orders", "Valid orders in active slice")
    kpi(c[1], "Avg delivery time", fmt(S["Mean (μ)"]), "min", f"Benchmark: {fmt(mu_all)} min")
    kpi(c[2], "Late deliveries", fmt(S["Late delivery %"]), "%", f"Above T_late = {fmt(T)} min")
    kpi(c[3], "Median delivery time", fmt(S["Median"]), "min", "Middle value (robust metric)")
    kpi(c[4], "On-time deliveries", f"{S['On-time orders']:,}", "orders", f"{fmt(S.get('On-time %', 100-S['Late delivery %']))}% fulfilled")
    st.write("")

def pattern(t, col, val="Mean", hi=True, unit="min"):
    if t.empty or len(t) < 1:
        return
    r = t.loc[t[val].idxmax() if hi else t[val].idxmin()]
    st.caption(f"💡 Observed: '{r[col]}' shows {val.replace('_', ' ').lower()} "
               f"({r[val]:.1f} {unit}) among active groups.")

two = st.columns(2)

# =============================================================================
# PAGE 1: EXECUTIVE OVERVIEW (Featuring all 4 required charts + KPIs)
# =============================================================================
if page == PAGES[0]:
    kpi_row()

    # SECTION 1: Required Visuals (Row 1)
    st.markdown('<div class="section-header"><h3>📈 Core Performance & Trend Insights</h3></div>', unsafe_allow_html=True)
    r1_col1, r1_col2 = st.columns(2)

    with r1_col1:
        # Required Visual 1: Monthly Trends Line Chart
        show(ch.monthly_trend(df))

    with r1_col2:
        # Required Visual 2: Delivery Time Distribution Histogram
        show(ch.histogram(df, T))

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # SECTION 2: Required Visuals (Row 2)
    st.markdown('<div class="section-header"><h3>🚦 SLA Failure Risk & Territory Fleet Breakdown</h3></div>', unsafe_allow_html=True)
    r2_col1, r2_col2 = st.columns(2)

    with r2_col1:
        # Required Visual 3: % of late deliveries by traffic or weather
        late_criteria = st.radio(
            "Select condition dimension for Late SLA Analysis:",
            ["Traffic Congestion", "Weather Conditions"],
            horizontal=True,
            key="overview_late_toggle"
        )
        col_to_use = "Traffic" if "Traffic" in late_criteria else "Weather"
        show(ch.late_bar(df, col_to_use, f"% of Late Deliveries by {col_to_use}"))

    with r2_col2:
        # Required Visual 4: Agent count per area
        show(ch.agent_count_area(df))

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # SECTION 3: Automatically Generated Operational Insights
    st.markdown('<div class="section-header"><h3>🧠 Automated Operational Insights</h3></div>', unsafe_allow_html=True)
    for line in ins.generate(df):
        st.markdown(f"- {line}")

    st.caption(
        f"📌 **Statistical Reference:** Late Delivery Cutoff $T_{{late}} = \\mu + \\sigma = {fmt(mu_all, 2)} + {fmt(sd_all, 2)} = {fmt(T, 2)}$ min, "
        f"fixed on all {len(clean):,} cleaned records. All graph data labels display dark, high-contrast values with percentages."
    )

# =============================================================================
# PAGE 2: DELAY ANALYZER
# =============================================================================
elif page == PAGES[1]:
    kpi_row()
    show(ch.delay_analyzer(df))
    gt = calc.group_table(df, "Weather")
    pattern(gt, "Weather")
    
    with two[0]:
        show(ch.late_bar(df, "Traffic", "Late deliveries by Traffic (%)"))
    with two[1]:
        show(ch.late_bar(df, "Weather", "Late deliveries by Weather Condition (%)"))

    with st.expander("Detailed Weather and Traffic Statistics Table"):
        table(calc.group_table(df, ["Weather", "Traffic"]))

# =============================================================================
# PAGE 3: FLEET PERFORMANCE
# =============================================================================
elif page == PAGES[2]:
    kpi_row()
    vt = calc.group_table(df, "Vehicle")
    show(ch.vehicle_comparison(df))
    pattern(vt, "Vehicle", hi=False)

    with two[0]:
        show(ch.mean_bar(df, "Vehicle", "Order Distribution by Fleet Vehicle Type", "Orders"))
    with two[1]:
        show(ch.late_bar(df, "Vehicle", "Late deliveries by Fleet Vehicle Type (%)"))

    sort_by = st.selectbox("Sort Fleet Summary Table by", ["Mean", "Median", "Orders", "Late_%", "Std"])
    table(vt.sort_values(sort_by, ascending=sort_by in ("Mean", "Median", "Std")))

# =============================================================================
# PAGE 4: AGENT ANALYTICS
# =============================================================================
elif page == PAGES[3]:
    kpi_row()
    fig, sampled = ch.agent_scatter(df, T)
    show(fig)
    if sampled:
        st.caption("Chart shows a random sample of 1,500 points for smooth browser rendering. All metrics and calculations use every filtered record.")

    g = calc.group_table(df, "Agent_Age_Group").merge(
        df.groupby("Agent_Age_Group")["Agent_Rating"].mean().rename("Avg_Rating").reset_index()
    )
    with two[0]:
        show(ch.box_by(df, "Agent_Age_Group", "Delivery time by Agent Age Group", T))
    with two[1]:
        show(ch.late_bar(df, "Agent_Age_Group", "Late deliveries by Agent Age Group (%)"))

    table(g[["Agent_Age_Group", "Orders", "Share_%", "Avg_Rating", "Mean", "Median", "Late_%"]])

    if df["Agent_Rating"].nunique() > 1:
        corr_val = df["Agent_Rating"].corr(df["Delivery_Time"])
        st.caption(f"Pearson correlation between rating and turnaround speed: r = {corr_val:.2f}. (Descriptive association).")

# =============================================================================
# PAGE 5: REGIONAL INTELLIGENCE
# =============================================================================
elif page == PAGES[4]:
    kpi_row()
    show(ch.area_heatmap(df))
    at = calc.group_table(df, "Area")
    pattern(at, "Area")

    with two[0]:
        show(ch.agent_count_area(df))
    with two[1]:
        show(ch.late_bar(df, "Area", "Late deliveries by Area (%)"))

    show(ch.mean_bar(df, "Area", "Average delivery time by Territory Corridor (min)"))
    table(at.sort_values("Mean", ascending=False))

# =============================================================================
# PAGE 6: PRODUCT CATEGORIES
# =============================================================================
elif page == PAGES[5]:
    kpi_row()
    show(ch.category_box(df, T))
    ct = calc.group_table(df, "Category")
    pattern(ct, "Category")

    with two[0]:
        show(ch.mean_bar(df, "Category", "Average delivery time by Category (min)"))
    with two[1]:
        show(ch.mean_bar(df, "Category", "Order Volume & Share by Product Category", "Orders"))

    table(ct.sort_values("Mean", ascending=False))

# =============================================================================
# PAGE 7: DATA EXPLORER
# =============================================================================
elif page == PAGES[6]:
    q = st.text_input("🔍 Search all text columns", placeholder="e.g. Jam, Van, Metropolitan, Electronics…")
    view = df
    if q:
        txt = df.astype(str).apply(lambda s: s.str.contains(q, case=False, regex=False)).any(axis=1)
        view = df[txt]

    st.caption(f"Displaying **{len(view):,}** of **{len(df):,}** active records.")
    st.dataframe(view, use_container_width=True, hide_index=True, height=420)

    summ = pd.DataFrame({
        "Metric": list(S.keys()),
        "Value": [round(v, 4) if isinstance(v, float) else v for v in S.values()]
    })

    report_txt = (
        "Analyzing Last mile Delivery Data for Performance Insights\n"
        "Analytical Summary Report\n"
        + "\n".join(f"{k}: {fmt(v, 2)}" for k, v in S.items())
        + "\n\nOperational Insights\n"
        + "\n".join("- " + l.replace("**", "") for l in ins.generate(df))
    )

    c = st.columns(5)
    c[0].download_button("Cleaned dataset", csv_bytes(clean), "cleaned_dataset.csv", "text/csv", use_container_width=True)
    c[1].download_button("Filtered dataset", csv_bytes(df), "filtered_dataset.csv", "text/csv", use_container_width=True)
    c[2].download_button("Statistical summary", csv_bytes(summ), "statistical_summary.csv", "text/csv", use_container_width=True)
    c[3].download_button("Late deliveries", csv_bytes(df[df["Is_Late"]]), "late_deliveries.csv", "text/csv", use_container_width=True)
    c[4].download_button("Insights report", report_txt.encode("utf-8"), "analytical_summary.txt", "text/plain", use_container_width=True)

    st.markdown("### Statistical Summary (Active Slice)")
    table(summ)

# =============================================================================
# PAGE 8: METHODOLOGY & DATA QUALITY
# =============================================================================
else:
    r = report
    c = st.columns(5)
    kpi(c[0], "Raw records", f"{r['raw_rows']:,}", "", "Total rows loaded")
    kpi(c[1], "Duplicates removed", f"{r['duplicates']:,}", "", "Repeated Order_IDs")
    kpi(c[2], "Invalid time excluded", f"{r['invalid_time_dropped']:,}", "", "Null or non-positive times")
    kpi(c[3], "Cleaned records", f"{r['final_rows']:,}", "", "Active analysis rows")
    kpi(c[4], "Late Threshold (T_late)", f"{fmt(T, 2)}", "min", "μ + σ cutoff")

    st.markdown("### Data Cleaning Actions Log")
    if r["log"].empty:
        st.success("No anomalous rows detected.")
    else:
        table(r["log"])

    a, b = st.columns(2)
    with a:
        st.markdown("### Missing Values (Before → After Imputation)")
        table(pd.DataFrame({
            "Column": r["missing_before"].index,
            "Missing Before": r["missing_before"].values,
            "Missing After": r["missing_after"].values
        }))
    with b:
        st.markdown("### Feature Schema & Data Types")
        table(pd.DataFrame({
            "Feature Name": clean.columns,
            "Inferred Type": clean.dtypes.astype(str).values
        }))

    st.markdown("### Mathematical & Statistical Formulas")
    st.latex(r"\mu=\frac{1}{n}\sum_{i=1}^{n}t_i \qquad \sigma=\sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(t_i-\mu)^2} \qquad T_{late}=\mu+\sigma")
    st.latex(r"\text{Late \%}=\left(\frac{\text{Count}(t_i > T_{late})}{n}\right)\times 100 \qquad \text{IQR}=Q_3-Q_1")

    st.markdown(f"""
- **Sample Standard Deviation:** Computed with Bessel's correction ($n-1$). For this population: $\\mu = {fmt(mu_all, 2)}$ min, $\\sigma = {fmt(sd_all, 2)}$ min, $T_{{late}} = {fmt(T, 2)}$ min.
- **Late Threshold ($T_{{late}}$):** Fixed across the full cleaned dataset so the late classification remains constant as slicing filters are manipulated.
- **Percentages on All Visualizations:** All charts render percentage share or late breach percentage directly on data labels with high-contrast `#0B1F3A` dark typography.
- **Filter Change Detection:** Automatically tracks adjustments across 7 filter dimensions and alerts dispatchers via toast and pop-up cards.
- **Zero-Blank-Screen Guarantee:** Adaptive Micro-Simulation ensures that even when hyper-narrow filter selections result in 0 historical records, a calibrated benchmark cohort is automatically synthesized so all visualizations render without crashing.
""")
