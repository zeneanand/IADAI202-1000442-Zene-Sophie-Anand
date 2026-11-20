"""Plotly chart builders with high-contrast, dark, visible values and percentages.
Resilient to small datasets and single-record slices (N >= 1).
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

TEAL = "#0F9D93"
DARK_TEAL = "#0B6F68"
LIGHT_TEAL = "#E8F5F4"
WARM_GRAY = "#334155"        # Darkened for crisp contrast
NAVY = "#0B1F3A"             # Dark navy for high visibility text
DARK_TEXT = "#0B1F3A"        # Guaranteed dark text for graph values
CORAL = "#D9534F"
DARK_CORAL = "#B52B27"
GRID = "#D5DDE5"
BG = "#FFFFFF"

PALETTE = [TEAL, "#2A7B9B", "#F39C12", "#E74C3C", "#8E44AD", "#16A085", "#2C3E50"]


def _base_layout(fig, title="", height=360):
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(family="Inter, Segoe UI, sans-serif", size=14, color=NAVY),
            x=0,
            y=0.98
        ),
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        margin=dict(l=45, r=25, t=48, b=42),
        height=height,
        font=dict(family="Inter, Segoe UI, sans-serif", size=11, color=NAVY),
        hoverlabel=dict(bgcolor=NAVY, font=dict(color="#fff", size=11)),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        linecolor=GRID,
        tickfont=dict(color=NAVY, size=11, family="Inter, sans-serif"),
        title_font=dict(color=NAVY, size=12, family="Inter, sans-serif")
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        linecolor=GRID,
        tickfont=dict(color=NAVY, size=11, family="Inter, sans-serif"),
        title_font=dict(color=NAVY, size=12, family="Inter, sans-serif")
    )
    return fig


def monthly_trend(df):
    """Line chart tracking delivery time progression across months with % changes."""
    if df.empty or "Delivery_Time" not in df.columns:
        return None

    date_col = None
    for c in ["Order_Date", "YearMonth", "Month"]:
        if c in df.columns:
            date_col = c
            break

    if date_col is None:
        d = df.copy()
        d["Month_Label"] = "Mar 2022"
        d["Period"] = "2022-03"
    elif date_col == "Order_Date":
        d = df.dropna(subset=["Order_Date", "Delivery_Time"]).copy()
        d["Order_Date"] = pd.to_datetime(d["Order_Date"], errors="coerce")
        d["Period"] = d["Order_Date"].dt.to_period("M").astype(str).fillna("2022-03")
        d["Month_Label"] = d["Order_Date"].dt.strftime("%b %Y").fillna("Mar 2022")
    else:
        d = df.dropna(subset=["Delivery_Time"]).copy()
        d["Period"] = d[date_col].astype(str)
        d["Month_Label"] = d[date_col].astype(str)

    monthly = d.groupby(["Period", "Month_Label"]).agg(
        Mean=("Delivery_Time", "mean"),
        Orders=("Delivery_Time", "count")
    ).reset_index().sort_values("Period")

    if monthly.empty:
        return None

    total_orders = monthly["Orders"].sum()
    monthly["Share_%"] = (monthly["Orders"] / total_orders) * 100.0 if total_orders > 0 else 100.0
    monthly["Pct_Change"] = monthly["Mean"].pct_change() * 100.0

    labels = []
    for idx, row in monthly.iterrows():
        val_str = f"<b>{row['Mean']:.1f}m</b>"
        if pd.notna(row["Pct_Change"]):
            val_str += f" ({row['Pct_Change']:+.1f}%)"
        else:
            val_str += f" ({row['Share_%']:.0f}% vol)"
        labels.append(val_str)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["Month_Label"],
        y=monthly["Mean"],
        mode="lines+markers+text" if len(monthly) > 1 else "markers+text",
        name="Avg Delivery Time",
        line=dict(color=TEAL, width=3),
        marker=dict(size=12, color=DARK_TEAL, line=dict(color="#ffffff", width=2)),
        text=labels,
        textposition="top center",
        textfont=dict(color=DARK_TEXT, size=12, family="Inter, sans-serif"),
        hovertemplate="<b>%{x}</b><br>Avg Delivery Time: <b>%{y:.1f} mins</b><br>Orders: %{customdata[0]:,} (%{customdata[1]:.1f}% of total)<extra></extra>",
        customdata=np.stack((monthly["Orders"], monthly["Share_%"]), axis=-1),
    ))

    _base_layout(fig, "Monthly Trends: Average Delivery Time by Month (min)", height=350)
    fig.update_yaxes(title="Avg Delivery Time (minutes)", rangemode="tozero")
    fig.update_xaxes(title="Timeline Month")
    return fig


def histogram(df, late_threshold):
    """Histogram of delivery times with visible dark labels and SLA % annotations."""
    if df.empty or "Delivery_Time" not in df.columns:
        return None

    t = df["Delivery_Time"].dropna()
    total_orders = len(t)
    if total_orders == 0:
        return None

    late_count = int((t > late_threshold).sum())
    on_time_count = total_orders - late_count
    late_pct = (late_count / total_orders) * 100.0 if total_orders > 0 else 0.0
    on_time_pct = (on_time_count / total_orders) * 100.0 if total_orders > 0 else 100.0

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=t,
        nbinsx=max(10, min(35, total_orders)),
        marker=dict(color=TEAL, line=dict(color="#ffffff", width=0.5)),
        name="Deliveries",
        hovertemplate="Delivery time: <b>%{x} min</b><br>Count: <b>%{y:,}</b><extra></extra>",
    ))

    fig.add_vline(
        x=late_threshold,
        line=dict(color=DARK_CORAL, width=2.5, dash="dash"),
        annotation=dict(
            text=f"<b>Late SLA Cutoff ({late_threshold:.1f} min)</b><br>Late: <b>{late_pct:.1f}%</b> ({late_count:,})<br>On-Time: <b>{on_time_pct:.1f}%</b> ({on_time_count:,})",
            font=dict(color=DARK_TEXT, size=11, family="Inter, sans-serif"),
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor=DARK_CORAL,
            borderwidth=1.5,
            xanchor="left",
            yanchor="top",
        ),
    )

    _base_layout(fig, f"Delivery Time Distribution (On-Time: {on_time_pct:.1f}% · Late: {late_pct:.1f}%)", height=350)
    fig.update_xaxes(title="Delivery Time (minutes)")
    fig.update_yaxes(title="Number of Deliveries")
    return fig


def late_bar(df, col, title, n_min=1):
    """Ranked bar chart showing % of late deliveries with dark, visible labels."""
    if df.empty or col not in df.columns:
        return None

    if "Is_Late" not in df.columns:
        df = df.copy()
        df["Is_Late"] = False

    g = df.groupby(col).agg(
        Orders=("Delivery_Time", "count"),
        Late=("Is_Late", "sum"),
    ).reset_index()
    g = g[g["Orders"] >= n_min]
    if g.empty:
        g = df.groupby(col).agg(Orders=("Delivery_Time", "count"), Late=("Is_Late", "sum")).reset_index()
    if g.empty:
        return None

    g["Late_%"] = 100.0 * g["Late"] / g["Orders"]
    total_orders = len(df)
    g["Share_%"] = (g["Orders"] / total_orders) * 100.0 if total_orders > 0 else 100.0

    if col == "Traffic":
        traffic_order = ["Low", "Medium", "High", "Jam"]
        g["sort_key"] = g[col].map(lambda x: traffic_order.index(x) if x in traffic_order else 99)
        g = g.sort_values("sort_key")
    else:
        g = g.sort_values("Late_%", ascending=False)

    text_labels = [f"<b>{v:.1f}%</b> ({orders:,})" for v, orders in zip(g["Late_%"], g["Orders"])]

    fig = go.Figure(go.Bar(
        x=g[col].astype(str),
        y=g["Late_%"],
        marker=dict(color=CORAL),
        text=text_labels,
        textposition="outside",
        textfont=dict(color=DARK_TEXT, size=12, family="Inter, sans-serif"),
        hovertemplate="<b>%{x}</b><br>Late Rate: <b>%{y:.1f}%</b><br>Late Orders: %{customdata[0]:,}<br>Total Slice Orders: %{customdata[1]:,} (%{customdata[2]:.1f}% share)<extra></extra>",
        customdata=np.stack((g["Late"], g["Orders"], g["Share_%"]), axis=-1),
    ))

    _base_layout(fig, title, height=340)
    fig.update_yaxes(title="% of Deliveries Late (> T_late)", rangemode="tozero")
    fig.update_xaxes(title=col)
    return fig


def agent_count_area(df):
    """Agent / Courier workforce count per territory with percentage breakdown."""
    if df.empty or "Area" not in df.columns:
        return None

    if "Agent_ID" in df.columns:
        g = df.groupby("Area").agg(
            Agents=("Agent_ID", "nunique"),
            Orders=("Delivery_Time", "count")
        ).reset_index().sort_values("Agents", ascending=False)
        target_col = "Agents"
        target_label = "Unique Couriers"
    else:
        g = df.groupby("Area").agg(
            Orders=("Delivery_Time", "count")
        ).reset_index().sort_values("Orders", ascending=False)
        g["Agents"] = g["Orders"]
        target_col = "Agents"
        target_label = "Dispatched Fleet Orders"

    total_agents = g[target_col].sum()
    g["Share_%"] = (g[target_col] / total_agents) * 100.0 if total_agents > 0 else 100.0

    text_labels = [f"<b>{int(v):,}</b> ({pct:.1f}%)" for v, pct in zip(g[target_col], g["Share_%"])]

    fig = go.Figure(go.Bar(
        x=g["Area"].astype(str),
        y=g[target_col],
        marker=dict(color=TEAL),
        text=text_labels,
        textposition="outside",
        textfont=dict(color=DARK_TEXT, size=12, family="Inter, sans-serif"),
        hovertemplate="<b>%{x}</b><br>" + target_label + ": <b>%{y:,}</b><br>Workforce Share: <b>%{customdata[0]:.1f}%</b><br>Total Orders: %{customdata[1]:,}<extra></extra>",
        customdata=np.stack((g["Share_%"], g["Orders"]), axis=-1),
    ))

    _base_layout(fig, f"Agent Count per Area ({target_label} & % Share)", height=340)
    fig.update_yaxes(title=target_label, rangemode="tozero")
    fig.update_xaxes(title="Delivery Territory / Area")
    return fig


def mean_bar(df, col, title, metric="Mean", n_min=1):
    """Bar chart with visible dark values and percentages."""
    if df.empty or col not in df.columns:
        return None

    g = df.groupby(col)["Delivery_Time"].agg(
        Mean="mean", Median="median", Orders="count"
    ).reset_index()
    g = g[g["Orders"] >= n_min]
    if g.empty:
        g = df.groupby(col)["Delivery_Time"].agg(Mean="mean", Median="median", Orders="count").reset_index()
    if g.empty:
        return None

    total_orders = len(df)
    g["Share_%"] = (g["Orders"] / total_orders) * 100.0 if total_orders > 0 else 100.0
    g = g.sort_values(metric, ascending=False)

    if metric == "Orders":
        text_labels = [f"<b>{int(v):,}</b> ({pct:.1f}%)" for v, pct in zip(g[metric], g["Share_%"])]
        y_title = "Total Orders (% Share)"
    else:
        text_labels = [f"<b>{v:.1f}m</b> ({pct:.0f}% vol)" for v, pct in zip(g[metric], g["Share_%"])]
        y_title = f"{metric} Delivery Time (min)"

    fig = go.Figure(go.Bar(
        x=g[col].astype(str),
        y=g[metric],
        marker=dict(color=TEAL),
        text=text_labels,
        textposition="outside",
        textfont=dict(color=DARK_TEXT, size=12, family="Inter, sans-serif"),
        hovertemplate="<b>%{x}</b><br>" + metric + ": <b>%{y:.1f}</b><br>Orders: %{customdata[0]:,} (%{customdata[1]:.1f}% of total)<extra></extra>",
        customdata=np.stack((g["Orders"], g["Share_%"]), axis=-1),
    ))

    _base_layout(fig, title, height=330)
    fig.update_yaxes(title=y_title, rangemode="tozero")
    fig.update_xaxes(title=col)
    return fig


def delay_analyzer(df):
    """Heatmap showing average delivery time across Weather & Traffic combinations."""
    if df.empty or "Traffic" not in df.columns or "Weather" not in df.columns:
        return None

    pv = df.pivot_table(index="Traffic", columns="Weather", values="Delivery_Time", aggfunc="mean")
    if pv.empty:
        return None

    traffic_order = [t for t in ["Low", "Medium", "High", "Jam"] if t in pv.index]
    if traffic_order:
        pv = pv.reindex(traffic_order)

    z = pv.values
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=[str(c) for c in pv.columns],
        y=[str(r) for r in pv.index],
        colorscale=[[0, LIGHT_TEAL], [0.5, TEAL], [1, NAVY]],
        text=np.round(z, 1),
        texttemplate="<b>%{text}m</b>",
        textfont=dict(size=12, family="Inter, sans-serif"),
        hovertemplate="Traffic: <b>%{y}</b><br>Weather: <b>%{x}</b><br>Avg Time: <b>%{z:.1f} mins</b><extra></extra>",
        colorbar=dict(title=dict(text="min", side="top", font=dict(size=11, color=DARK_TEXT)), len=0.8),
    ))
    _base_layout(fig, "Delay Analyzer: Weather × Traffic Impact (min)", height=370)
    fig.update_xaxes(title="Weather Condition")
    fig.update_yaxes(title="Traffic Density")
    return fig


def vehicle_comparison(df):
    """Compare delivery speed and reliability across vehicle types with dark labels."""
    if df.empty or "Vehicle" not in df.columns:
        return None

    g = df.groupby("Vehicle").agg(
        Mean=("Delivery_Time", "mean"),
        Median=("Delivery_Time", "median"),
        Std=("Delivery_Time", "std"),
        Orders=("Delivery_Time", "count")
    ).reset_index().sort_values("Mean")

    total_orders = len(df)
    g["Share_%"] = (g["Orders"] / total_orders) * 100.0 if total_orders > 0 else 100.0

    mean_labels = [f"<b>{v:.1f}m</b> ({pct:.0f}%)" for v, pct in zip(g["Mean"], g["Share_%"])]
    median_labels = [f"<b>{v:.1f}m</b>" for v in g["Median"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["Vehicle"], y=g["Mean"], name="Mean", marker_color=TEAL,
        text=mean_labels, textposition="outside",
        textfont=dict(color=DARK_TEXT, size=11, family="Inter, sans-serif"),
        hovertemplate="<b>%{x}</b> (Mean): <b>%{y:.1f} min</b><br>Orders: %{customdata[0]:,} (%{customdata[1]:.1f}% mix)<extra></extra>",
        customdata=np.stack((g["Orders"], g["Share_%"]), axis=-1),
    ))
    fig.add_trace(go.Bar(
        x=g["Vehicle"], y=g["Median"], name="Median", marker_color="#2A7B9B",
        text=median_labels, textposition="outside",
        textfont=dict(color=DARK_TEXT, size=11, family="Inter, sans-serif"),
        hovertemplate="<b>%{x}</b> (Median): <b>%{y:.1f} min</b><extra></extra>",
    ))

    _base_layout(fig, "Vehicle Comparison: Mean & Median Delivery Time by Fleet Type", height=360)
    fig.update_layout(barmode="group", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_yaxes(title="Delivery Time (min)", rangemode="tozero")
    return fig


def agent_scatter(df, late_threshold, max_pts=1500):
    """Scatter plot correlating Agent Rating with Delivery Speed."""
    valid = df.dropna(subset=["Agent_Rating", "Delivery_Time"]).copy()
    if valid.empty:
        return None, False
    sampled = len(valid) > max_pts
    plot_df = valid.sample(max_pts, random_state=42) if sampled else valid

    fig = px.scatter(
        plot_df,
        x="Agent_Rating",
        y="Delivery_Time",
        color="Agent_Age_Group",
        color_discrete_map={"Below 25": "#2A7B9B", "25–40": TEAL, "Above 40": "#F39C12"},
        category_orders={"Agent_Age_Group": ["Below 25", "25–40", "Above 40"]},
        opacity=0.6,
        hover_data={"Agent_Rating": ":.2f", "Delivery_Time": ":.1f", "Vehicle": True, "Traffic": True},
    )
    fig.add_vline(x=4.0, line=dict(color=WARM_GRAY, width=1, dash="dot"))
    fig.add_hline(
        y=late_threshold,
        line=dict(color=DARK_CORAL, width=2, dash="dash"),
        annotation=dict(
            text=f"<b>Late Cutoff: {late_threshold:.1f}m</b>",
            font=dict(color=DARK_TEXT, size=11, family="Inter, sans-serif"),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=DARK_CORAL,
            borderwidth=1
        ),
    )
    _base_layout(fig, "Agent Rating vs. Delivery Speed (by Age Cohort)", height=400)
    fig.update_xaxes(title="Customer Rating (0–5 Stars)")
    fig.update_yaxes(title="Delivery Time (minutes)")
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""))
    return fig, sampled


def area_heatmap(df):
    """Matrix heatmap of delivery delays across Area and Traffic density."""
    if df.empty or "Area" not in df.columns or "Traffic" not in df.columns:
        return None

    pv = df.pivot_table(index="Area", columns="Traffic", values="Delivery_Time", aggfunc="mean")
    if pv.empty:
        return None

    traffic_order = [t for t in ["Low", "Medium", "High", "Jam"] if t in pv.columns]
    if traffic_order:
        pv = pv[traffic_order]

    z = pv.values
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=[str(c) for c in pv.columns],
        y=[str(r) for r in pv.index],
        colorscale=[[0, LIGHT_TEAL], [0.5, TEAL], [1, NAVY]],
        text=np.round(z, 1),
        texttemplate="<b>%{text}m</b>",
        textfont=dict(size=12, family="Inter, sans-serif"),
        hovertemplate="Area: <b>%{y}</b><br>Traffic: <b>%{x}</b><br>Mean Time: <b>%{z:.1f} mins</b><extra></extra>",
        colorbar=dict(title=dict(text="min", side="top", font=dict(size=11, color=DARK_TEXT)), len=0.8),
    ))
    _base_layout(fig, "Area Heatmap: Average Delivery Time by Area & Traffic Condition (min)", height=360)
    fig.update_xaxes(title="Traffic Density")
    fig.update_yaxes(title="Delivery Territory")
    return fig


def box_by(df, col, title, late_threshold=None):
    if df.empty or col not in df.columns:
        return None
    fig = px.box(
        df,
        x=col,
        y="Delivery_Time",
        color=col,
        color_discrete_sequence=PALETTE,
        points=False if len(df) > 5 else "all",
    )
    if late_threshold:
        fig.add_hline(
            y=late_threshold,
            line=dict(color=DARK_CORAL, width=1.5, dash="dash"),
            annotation=dict(text=f"Late SLA ({late_threshold:.1f}m)", font=dict(color=DARK_TEXT, size=10))
        )
    _base_layout(fig, title, height=330)
    fig.update_layout(showlegend=False)
    fig.update_yaxes(title="Delivery Time (min)")
    fig.update_xaxes(title="")
    return fig


def category_box(df, late_threshold):
    if df.empty or "Category" not in df.columns:
        return None
    order = df.groupby("Category")["Delivery_Time"].median().sort_values(ascending=False).index.tolist()
    fig = px.box(
        df,
        x="Category",
        y="Delivery_Time",
        category_orders={"Category": order},
        color="Category",
        color_discrete_sequence=PALETTE,
        points=False if len(df) > 5 else "all",
    )
    fig.add_hline(
        y=late_threshold,
        line=dict(color=DARK_CORAL, width=1.5, dash="dash"),
        annotation=dict(text=f"T_late = {late_threshold:.1f}m", font=dict(color=DARK_TEXT, size=10))
    )
    _base_layout(fig, "Category Spread: Delivery Time Distribution across Product Categories", height=380)
    fig.update_layout(showlegend=False)
    fig.update_yaxes(title="Delivery Time (min)")
    fig.update_xaxes(title="Product Category", tickangle=-30)
    return fig
