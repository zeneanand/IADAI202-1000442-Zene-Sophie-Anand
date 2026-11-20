"""Operational insights generator for FA-2.
Resilient to small datasets and single-record slices.
"""

MIN_GROUP = 1
MIN_TOTAL = 1

def generate(df):
    insights = []
    if df.empty:
        return ["No orders in this selection. Please widen filters."]
    
    n = len(df)
    
    # 1. Traffic insight
    if "Traffic" in df.columns:
        if "Is_Late" in df.columns:
            traffic_late = df.groupby("Traffic")["Is_Late"].mean() * 100
            if not traffic_late.empty:
                worst_traffic = traffic_late.idxmax()
                worst_traffic_val = traffic_late.max()
                insights.append(f"**Traffic Congestion Risk**: Orders under '{worst_traffic}' traffic experience a {worst_traffic_val:.1f}% late SLA rate in this cohort.")
        else:
            tr_counts = df["Traffic"].value_counts()
            if not tr_counts.empty:
                insights.append(f"**Traffic Context**: Primary congestion tier is '{tr_counts.index[0]}' ({tr_counts.iloc[0]:,} orders).")

    # 2. Weather insight
    if "Weather" in df.columns:
        if "Is_Late" in df.columns:
            weather_late = df.groupby("Weather")["Is_Late"].mean() * 100
            if not weather_late.empty:
                worst_weather = weather_late.idxmax()
                worst_weather_val = weather_late.max()
                insights.append(f"**Weather Impact**: Adverse weather condition '{worst_weather}' records a {worst_weather_val:.1f}% late delivery rate.")
        else:
            w_counts = df["Weather"].value_counts()
            if not w_counts.empty:
                insights.append(f"**Weather Context**: Dominant environmental condition is '{w_counts.index[0]}'.")

    # 3. Vehicle comparison
    if "Vehicle" in df.columns and "Delivery_Time" in df.columns:
        veh_mean = df.groupby("Vehicle")["Delivery_Time"].mean()
        if not veh_mean.empty:
            fastest_veh = veh_mean.idxmin()
            insights.append(f"**Fleet Agility**: '{fastest_veh}' recorded an average transit time of {veh_mean.min():.1f} mins.")

    # 4. Regional territory
    if "Area" in df.columns and "Delivery_Time" in df.columns:
        area_mean = df.groupby("Area")["Delivery_Time"].mean()
        if not area_mean.empty:
            slowest_area = area_mean.idxmax()
            insights.append(f"**Geographic Hotspot**: '{slowest_area}' corridor shows an average turnaround of {area_mean.max():.1f} mins.")

    if n < 10:
        insights.append(f"**Sample Density**: Micro-cohort of {n} order(s). Showing calibrated metrics for this specific operational slice.")

    return insights
