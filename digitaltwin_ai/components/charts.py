"""
Plotly Chart Visualizers for DigitalTwin.ai.
Dark industrial aesthetic with responsive formatting.
"""

import plotly.graph_objects as go
from typing import List, Dict, Any

DARK_LAYOUT = dict(
    paper_bgcolor='rgba(18, 24, 36, 0.7)',
    plot_bgcolor='rgba(11, 14, 20, 0.8)',
    font=dict(family="Inter, sans-serif", color="#94A3B8", size=11),
    margin=dict(l=40, r=20, t=35, b=35),
    xaxis=dict(
        gridcolor="#1E293B",
        zerolinecolor="#334155",
        tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#64748B")
    ),
    yaxis=dict(
        gridcolor="#1E293B",
        zerolinecolor="#334155",
        tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#64748B")
    ),
    legend=dict(
        font=dict(size=10, color="#CBD5E1"),
        bgcolor="rgba(11, 14, 20, 0.6)",
        bordercolor="#1E293B",
        borderwidth=1
    )
)

def create_cycle_time_trend_chart(timestamps: List[str], s25_times: List[float], s18_times: List[float], s5_times: List[float]) -> go.Figure:
    """Create Cycle Time Trend chart highlighting S25 degradation vs Control Limits."""
    fig = go.Figure()
    
    # Upper Control Limit (UCL) threshold
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=[15.5] * len(timestamps),
        mode="lines",
        name="UCL Threshold (15.5m)",
        line=dict(color="#EF4444", width=1.5, dash="dash")
    ))
    
    # S25 Marriage (Degrading)
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=s25_times,
        mode="lines+markers",
        name="S25 (Marriage Integration)",
        line=dict(color="#F59E0B", width=3),
        marker=dict(size=6, color="#F59E0B")
    ))
    
    # S18 Baking Oven
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=s18_times,
        mode="lines",
        name="S18 (Paint Oven)",
        line=dict(color="#38BDF8", width=1.8)
    ))
    
    # S5 Main Body Framing
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=s5_times,
        mode="lines",
        name="S5 (Body Framing)",
        line=dict(color="#10B981", width=1.5)
    ))
    
    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text="Station Cycle Time Progression (Minutes)", font=dict(size=13, color="#F8FAFC")),
        yaxis_title="Cycle Time (min)",
        hovermode="x unified"
    )
    return fig

def create_queue_growth_chart(timestamps: List[str], s25_queues: List[int], s18_queues: List[int]) -> go.Figure:
    """Create Queue Growth over time chart."""
    fig = go.Figure()
    
    # S25 Buffer Limit
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=[5] * len(timestamps),
        mode="lines",
        name="S25 Buffer Limit (5 units)",
        line=dict(color="#EF4444", width=1, dash="dot")
    ))
    
    # S25 Queue Growth (Filled)
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=s25_queues,
        mode="lines+markers",
        name="S25 Queue Length",
        fill="tozeroy",
        fillcolor="rgba(245, 158, 11, 0.15)",
        line=dict(color="#F59E0B", width=2.5),
        marker=dict(size=5)
    ))
    
    # S18 Queue Growth
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=s18_queues,
        mode="lines",
        name="S18 Queue Length",
        fill="tozeroy",
        fillcolor="rgba(56, 189, 248, 0.1)",
        line=dict(color="#38BDF8", width=1.5)
    ))
    
    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text="Queue Accumulation vs Buffer Capacity (Units)", font=dict(size=13, color="#F8FAFC")),
        yaxis_title="Queue (units)",
        hovermode="x unified"
    )
    return fig

def create_throughput_trend_chart(timestamps: List[str], throughput: List[float]) -> go.Figure:
    """Create Throughput Trend chart (JPH)."""
    fig = go.Figure()
    
    # Target Line
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=[42.0] * len(timestamps),
        mode="lines",
        name="Target JPH (42.0)",
        line=dict(color="#10B981", width=1.5, dash="dash")
    ))
    
    # Actual Throughput
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=throughput,
        mode="lines+markers",
        name="Actual Throughput",
        line=dict(color="#06B6D4", width=2.5),
        marker=dict(size=5, color="#06B6D4"),
        fill="tozeroy",
        fillcolor="rgba(6, 182, 212, 0.1)"
    ))
    
    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text="Line Throughput Trend (Jobs Per Hour)", font=dict(size=13, color="#F8FAFC")),
        yaxis_title="JPH",
        hovermode="x unified"
    )
    return fig

def create_bottleneck_ranking_bar(rankings: List[Dict[str, Any]]) -> go.Figure:
    """Create horizontal bar chart of bottleneck risk rankings."""
    stations = [f"{r['id']} ({r['name'][:18]}...)" for r in reversed(rankings)]
    risks = [r['risk_score'] for r in reversed(rankings)]
    colors = [
        "#EF4444" if r >= 80 else ("#F59E0B" if r >= 50 else "#10B981")
        for r in reversed(risks)
    ]
    
    fig = go.Figure(go.Bar(
        x=risks,
        y=stations,
        orientation="h",
        marker=dict(color=colors, line=dict(color="#1E293B", width=1)),
        text=[f"{r}%" for r in risks],
        textposition="auto",
        textfont=dict(family="JetBrains Mono", size=10, color="#FFFFFF")
    ))
    
    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text="Station Bottleneck Risk Ranking (%)", font=dict(size=13, color="#F8FAFC")),
        xaxis=dict(range=[0, 100], gridcolor="#1E293B", title="Risk Score (%)"),
        yaxis=dict(tickfont=dict(size=10))
    )
    return fig
