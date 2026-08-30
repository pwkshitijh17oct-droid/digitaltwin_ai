"""
DIGITALTWIN.AI — Plotly Chart Visualizations Component
Industrial Dark Styled Visualizations for Bottlenecks, Telemetry, and Performance.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Any

DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(18, 24, 36, 0.8)",
    font=dict(color="#94A3B8", family="Inter, sans-serif", size=11),
    margin=dict(l=40, r=20, t=35, b=35),
    xaxis=dict(gridcolor="#1E293B", zerolinecolor="#1E293B"),
    yaxis=dict(gridcolor="#1E293B", zerolinecolor="#1E293B")
)

def build_cycle_time_chart(stations: List[Dict[str, Any]], line_takt: float) -> go.Figure:
    s_ids = [s["id"] for s in stations]
    cts = [s["current_cycle_time"] for s in stations]
    colors = [
        "#EF4444" if s["status"] == "BLOCKED" else ("#F59E0B" if s["current_cycle_time"] > line_takt else "#10B981")
        for s in stations
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=s_ids,
        y=cts,
        marker_color=colors,
        name="Actual Cycle Time",
        hovertemplate="<b>%{x}</b><br>Cycle Time: %{y:.2f} min<extra></extra>"
    ))

    fig.add_hline(
        y=line_takt,
        line_dash="dash",
        line_color="#38BDF8",
        annotation_text=f"Line Takt ({line_takt} min)",
        annotation_position="top right",
        annotation_font_color="#38BDF8"
    )

    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text="Plant-Wide Station Cycle Times vs Line Takt", font=dict(size=13, color="#F8FAFC")),
        xaxis_title="Station ID",
        yaxis_title="Cycle Time (min)"
    )
    return fig

def build_queue_accumulation_chart(stations: List[Dict[str, Any]]) -> go.Figure:
    s_ids = [s["id"] for s in stations]
    queues = [s["queue_length"] for s in stations]
    caps = [s["queue_capacity"] for s in stations]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=s_ids,
        y=queues,
        marker_color="#F59E0B",
        name="Current Queue Length",
        hovertemplate="<b>%{x}</b><br>Queue: %{y}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=s_ids,
        y=caps,
        mode="lines+markers",
        line=dict(color="#EF4444", width=2, dash="dot"),
        name="Queue Capacity",
        hovertemplate="<b>%{x}</b><br>Capacity: %{y}<extra></extra>"
    ))

    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text="Queue Accumulation vs Buffer Capacity", font=dict(size=13, color="#F8FAFC")),
        xaxis_title="Station ID",
        yaxis_title="Vehicles Waiting"
    )
    return fig

def build_bottleneck_ranking_chart(rankings: List[Dict[str, Any]]) -> go.Figure:
    top = rankings[:10]
    top_reversed = list(reversed(top))
    
    labels = [f"{s['id']} — {s['name']}" for s in top_reversed]
    scores = [s["pressure_score"] for s in top_reversed]
    colors = [
        "#EF4444" if s["pressure_score"] >= 80.0 else ("#F59E0B" if s["pressure_score"] >= 50.0 else "#3B82F6")
        for s in top_reversed
    ]

    fig = go.Figure(go.Bar(
        x=scores,
        y=labels,
        orientation="h",
        marker_color=colors,
        hovertemplate="<b>%{y}</b><br>Bottleneck Pressure Score: %{x}<extra></extra>"
    ))

    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text="Top 10 Bottleneck Pressure Rankings", font=dict(size=13, color="#F8FAFC")),
        xaxis_title="Bottleneck Pressure Score (0–100+)",
        yaxis_title=""
    )
    return fig

def build_equipment_health_chart(stations: List[Dict[str, Any]]) -> go.Figure:
    # Filter non-buffer stations
    maint_stations = [s for s in stations if s["family"] != "buffer"]
    s_ids = [s["id"] for s in maint_stations]
    healths = [s["equipment_health_pct"] for s in maint_stations]
    
    colors = [
        "#10B981" if h >= 85.0 else ("#F59E0B" if h >= 70.0 else "#EF4444")
        for h in healths
    ]

    fig = go.Figure(go.Bar(
        x=s_ids,
        y=healths,
        marker_color=colors,
        hovertemplate="<b>%{x}</b><br>Equipment Health: %{y:.1f}%<extra></extra>"
    ))

    fig.add_hline(
        y=70.0,
        line_dash="dash",
        line_color="#EF4444",
        annotation_text="Degradation Threshold (70%)",
        annotation_position="bottom right",
        annotation_font_color="#EF4444"
    )

    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text="Equipment Health Profile Across Equipment-Driven Stations", font=dict(size=13, color="#F8FAFC")),
        xaxis_title="Station ID",
        yaxis_title="Equipment Health (%)",
        yaxis_range=[50, 105]
    )
    return fig

def build_telemetry_trend_chart(df: pd.DataFrame, metric_col: str, title: str) -> go.Figure:
    fig = go.Figure()
    if df.empty or metric_col not in df.columns:
        fig.update_layout(**DARK_LAYOUT, title=dict(text=f"No telemetry data available for {title}", font=dict(size=13, color="#F8FAFC")))
        return fig

    time_col = "simulation_time_hours" if "simulation_time_hours" in df.columns else df.index

    fig.add_trace(go.Scatter(
        x=df[time_col],
        y=df[metric_col],
        mode="lines",
        line=dict(color="#38BDF8", width=2),
        name=title
    ))

    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text=title, font=dict(size=13, color="#F8FAFC")),
        xaxis_title="Simulation Time (Hours)",
        yaxis_title=metric_col.replace("_", " ").title()
    )
    return fig
