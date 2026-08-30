"""
DIGITALTWIN.AI — KPI Cards Component
Renders top KPI summary widgets using REAL simulator metrics.
"""

import streamlit as st
import data.adapter as adapter

def render_kpi_cards():
    sim_state = adapter.get_simulation_state()
    
    released = sim_state.get("total_released_vehicles", 0)
    completed = sim_state.get("total_completed_vehicles", 0)
    active = sim_state.get("active_vehicle_count", 0)
    throughput = sim_state.get("throughput_jph", 0.0)
    takt = sim_state.get("line_takt_min", 10.0)
    
    bottleneck = sim_state.get("current_bottleneck")
    if bottleneck:
        b_id = bottleneck["id"]
        b_name = bottleneck["name"]
        b_status = bottleneck["status"]
        b_text = f"{b_id} — {b_name}"
        b_class = "critical" if b_status == "BLOCKED" else ("warning" if b_status in ("DOWN", "MAINTENANCE") else "info")
    else:
        b_text = "None (Nominal Flow)"
        b_class = "success"

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.markdown(
            f"""
            <div class="kpi-card success">
                <div class="kpi-label">Vehicles Released</div>
                <div class="kpi-value">{released}</div>
                <div class="kpi-subtext">Total released to S01</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="kpi-card success">
                <div class="kpi-label">Vehicles Completed</div>
                <div class="kpi-value">{completed}</div>
                <div class="kpi-subtext">Passed S35 Buyoff</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Active Vehicles</div>
                <div class="kpi-value">{active}</div>
                <div class="kpi-subtext">Currently on line</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Throughput (JPH)</div>
                <div class="kpi-value">{throughput}</div>
                <div class="kpi-subtext">Jobs Per Hour</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col5:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Line Takt</div>
                <div class="kpi-value">{takt} <span style="font-size:12px; font-weight:400; color:#64748B;">min</span></div>
                <div class="kpi-subtext">Target pace</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col6:
        st.markdown(
            f"""
            <div class="kpi-card {b_class}">
                <div class="kpi-label">Current Bottleneck</div>
                <div class="kpi-value" style="font-size:14px; line-height:1.3; font-weight:700;">{b_text}</div>
                <div class="kpi-subtext">Constrained station</div>
            </div>
            """,
            unsafe_allow_html=True
        )
