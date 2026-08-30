"""
DIGITALTWIN.AI — Overview Page
Main Control-Center Dashboard displaying live KPIs, 35-station assembly line, and detail drawer.
"""

import streamlit as st
import data.adapter as adapter
from components.kpi_cards import render_kpi_cards
from components.assembly_line import render_assembly_line
from components.station_drawer import render_station_drawer
from components.alerts import render_global_alerts

def render_overview_page():
    sim_state = adapter.get_simulation_state()
    stations = adapter.get_all_stations_data()
    
    # Header
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; border-bottom:1px solid #1E293B; padding-bottom:10px;">
            <div>
                <h1 style="font-size:22px; font-weight:800; color:#F8FAFC; margin:0;">DIGITALTWIN.AI</h1>
                <div style="font-size:12px; color:#94A3B8; font-weight:500;">Live 35-Station Assembly Digital Twin</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:12px; font-weight:700; color:#38BDF8; font-family:'JetBrains Mono';">{sim_state['simulation_time_formatted']}</div>
                <div style="font-size:10px; color:#64748B;">Status: <span style="color:#10B981; font-weight:600;">{sim_state['status']}</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Active Alerts
    render_global_alerts()

    # KPI Summary Cards
    render_kpi_cards()
    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # Check drawer state
    drawer_open = st.session_state.get("drawer_open", False)
    selected_sid = st.session_state.get("selected_station", None)

    if drawer_open and selected_sid:
        col_line, col_drawer = st.columns([3, 2])
        with col_line:
            render_assembly_line(stations, selected_station_id=selected_sid)
        with col_drawer:
            render_station_drawer(selected_sid)
    else:
        render_assembly_line(stations, selected_station_id=selected_sid)
