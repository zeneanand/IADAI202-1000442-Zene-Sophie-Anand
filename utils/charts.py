"""Plotly figures. Every function returns None when there is not enough valid data."""
import pandas as pd
import plotly.express as px
from . import calculations as calc

NAVY, TEAL, CORAL, GREY = "#0B1F3A", "#0F9D93", "#D9644A", "#B8C4D0"
SEQ = ["#0F9D93", "#5CC2B8", "#F0B44C", "#D9644A", "#7A5C99", "#3C6E9E"]
TEAL_SCALE = ["#EAF6F5", "#9BD6D0", "#0F9D93", "#0B4F5C"]
LBL = {"Delivery_Time": "Delivery time (min)", "Agent_Rating": "Agent rating (stars)", "Agent_Age_Group": "Age group",
       "Avg": "Avg delivery time (min)", "Late_%": "Late deliveries (%)", "Orders": "Orders"}


def _style(fig, title, height=420):
    fig.update_layout(
        template="plotly_white", height=height, title=dict(text=title, x=0, font=dict(size=16, color=NAVY)),
        font=dict(family="Inter, Segoe UI, Helvetica, Arial, sans-serif", color=NAVY, size=13),
        margin=dict(l=10, r=10, t=60, b=10), legend=dict(orientation="h", y=-0.2, title_text=""),
        paper_bgcolor="white", plot_bgcolor="white", hoverlabel=dict(bgcolor="white", font_size=13))
    fig.update_xaxes(gridcolor="#EEF1F4", linecolor="#D5DCE3")
    fig.update_yaxes(gridcolor="#EEF1F4", linecolor="#D5DCE3")
    return fig


def _thr(fig, T, axis="y", label="Late threshold"):
    if pd.notna(T):
        (fig.add_hline if axis == "y" else fig.add_vline)(
            **{axis: T}, line_dash="dash", line_color=CORAL, annotation_text=f"{label} ({T:.1f} min)",
            annotation_font_color=CORAL)
    return fig


def _avg(df, by):
    return df.groupby(by).agg(Avg=("Delivery_Time", "mean"), Orders=("Delivery_Time", "count")).reset_index()


def delay_analyzer(df):  # Visualisation 1
    if df.empty: return None
    g, tr = _avg(df, ["Weather", "Traffic"]), calc.ordered(df, "Traffic")
    fig = px.bar(g, x="Weather", y="Avg", color="Traffic", barmode="group", text_auto=".1f", labels=LBL,
                 category_orders={"Traffic": tr, "Weather": calc.ordered(df, "Weather")}, color_discrete_sequence=SEQ,
                 hover_data={"Orders": True, "Avg": ":.1f"})
    fig.update_layout(yaxis_title="Average delivery time (min)", xaxis_title="Weather condition")
    return _style(fig, "Average delivery time by weather and traffic")


def vehicle_comparison(df):  # Visualisation 2
    if df.empty: return None
    g = _avg(df, "Vehicle").sort_values("Avg")
    g["Highlight"] = ["Lowest average" if i == 0 else "Other vehicles" for i in range(len(g))]
    fig = px.bar(g, x="Vehicle", y="Avg", color="Highlight", text_auto=".1f", labels=LBL,
                 color_discrete_map={"Lowest average": TEAL, "Other vehicles": GREY},
                 category_orders={"Vehicle": g["Vehicle"].tolist()}, hover_data={"Orders": True, "Avg": ":.1f", "Highlight": False})
    fig.update_layout(yaxis_title="Average delivery time (min)", xaxis_title="Vehicle type")
    return _style(fig, "Average delivery time by vehicle type (sorted)")


def agent_scatter(df, T, max_points=1500):  # Visualisation 3
    if df.empty: return None, False
    sampled = len(df) > max_points
    d = df.sample(max_points, random_state=42) if sampled else df
    hover = [c for c in ["Order_ID", "Vehicle", "Area", "Traffic"] if c in d.columns]
    fig = px.scatter(d, x="Agent_Rating", y="Delivery_Time", color="Agent_Age_Group", opacity=.65, hover_data=hover,
                     category_orders={"Agent_Age_Group": calc.ordered(df, "Agent_Age_Group")}, labels=LBL,
                     color_discrete_sequence=[TEAL, "#F0B44C", "#7A5C99", GREY])
    return _style(_thr(fig, T), "Agent rating vs delivery time by age group"), sampled


def area_heatmap(df):  # Visualisation 4
    if df.empty: return None
    p = df.pivot_table(values="Delivery_Time", index="Area", columns="Traffic", aggfunc="mean")
    p = p[[c for c in calc.ordered(df, "Traffic") if c in p.columns]]
    fig = px.imshow(p, text_auto=".1f", aspect="auto", color_continuous_scale=TEAL_SCALE,
                    labels=dict(x="Traffic condition", y="Area", color="Avg (min)"))
    return _style(fig, "Average delivery time by area and traffic (min)")


def category_box(df, T):  # Visualisation 5
    if df.empty: return None
    fig = px.box(df, x="Category", y="Delivery_Time", color="Category", points="outliers", labels=LBL,
                 category_orders={"Category": calc.ordered(df, "Category")}, color_discrete_sequence=SEQ)
    fig.update_layout(showlegend=False)
    return _style(_thr(fig, T), "Delivery time distribution by product category")


def histogram(df, T):
    if df.empty: return None
    fig = px.histogram(df, x="Delivery_Time", color="Late_Status", nbins=35, labels=LBL, barmode="stack",
                       color_discrete_map={"Late": CORAL, "On-Time": TEAL}, category_orders={"Late_Status": ["On-Time", "Late"]})
    fig.update_layout(yaxis_title="Number of orders")
    return _style(_thr(fig, T, "x"), "Delivery time distribution", 380)


def late_bar(df, by, title, max_label=None):
    if df.empty: return None
    g = calc.group_table(df, by).sort_values("Late_%", ascending=False)
    fig = px.bar(g, x=by, y="Late_%", text_auto=".1f", labels=LBL, hover_data={"Orders": True, "Late_Orders": True, "Late_%": ":.1f"},
                 color_discrete_sequence=[TEAL], category_orders={by: g[by].tolist()})
    fig.update_layout(yaxis_title="Late deliveries (%)")
    return _style(fig, title, 380)


def mean_bar(df, by, title, value="Mean"):
    if df.empty: return None
    g = calc.group_table(df, by).sort_values(value, ascending=False)
    fig = px.bar(g, x=by, y=value, text_auto=".0f" if value == "Orders" else ".1f", labels={**LBL, "Mean": "Avg delivery time (min)", "Orders": "Orders"},
                 hover_data={"Orders": True}, color_discrete_sequence=[TEAL], category_orders={by: g[by].tolist()})
    return _style(fig, title, 380)


def box_by(df, by, title, T):
    if df.empty: return None
    fig = px.box(df, x=by, y="Delivery_Time", color=by, points="outliers", labels=LBL,
                 category_orders={by: calc.ordered(df, by)}, color_discrete_sequence=SEQ)
    fig.update_layout(showlegend=False)
    return _style(_thr(fig, T), title, 380)
