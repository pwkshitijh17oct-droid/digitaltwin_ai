"""
Page 1 — Overview (Digital Twin Line & Plant Operations).
Default landing page showing the current state of the complete 35-station virtual assembly line.
"""

import streamlit as st
from components.alerts import render_global_alerts
from components.kpi_cards import render_kpi_cards
from components.assembly_line import render_assembly_line
from components.station_drawer import render_station_drawer

def render_overview_page():
    """Render Overview page with live assembly line and drawer interaction."""
    # Top Global Alert Area
    render_global_alerts()
    
    # Top KPI Section (No OEE!)
    render_kpi_cards()
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Check if station drawer should be displayed side-by-side
    selected_id = st.session_state.get("selected_station_id")
    
    if selected_id:
        # Split layout: 65% assembly line, 35% detail drawer
        col_line, col_drawer = st.columns([7, 5], gap="medium")
        with col_line:
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 13px; font-weight: 700; color: #F8FAFC; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'JetBrains Mono', monospace;">
                    35-Station Virtual Assembly Line
                </span>
                <span style="font-size: 11px; color: #64748B;">Click any station node to inspect details</span>
            </div>
            """, unsafe_allow_html=True)
            render_assembly_line()
            
        with col_drawer:
            render_station_drawer(selected_id)
    else:
        # Full width assembly line
        st.markdown("""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-size: 13px; font-weight: 700; color: #F8FAFC; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'JetBrains Mono', monospace;">
                35-Station Virtual Assembly Line
            </span>
            <span style="font-size: 11px; color: #64748B;">💡 Click any station node to open the Right-Side Inspection Drawer</span>
        </div>
        """, unsafe_allow_html=True)
        render_assembly_line()
