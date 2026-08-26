"""
Interactive 35-station visual assembly line component for DigitalTwin.ai.
Displays stations across 3 shops: Body/BIW (S1-S10), Paint (S11-S20), GA+EOL (S21-S35).
CRITICAL RULES:
- Station node displays ONLY: status indicator dot and Station ID (e.g. 🟢 S23, 🟡 S25, 🔴 S30).
- NO cycle time on node.
- NO queue on node.
- NO sensor values on node.
- Hover shows complete tooltip.
- Click opens right-side Station Detail Drawer while keeping line visible.
"""

import streamlit as st
from typing import Dict, List, Any
from data.data_adapter import get_all_stations_data

def get_status_emoji_and_class(status: str) -> tuple[str, str]:
    if status == "NORMAL":
        return "🟢", "normal"
    elif status == "WARNING":
        return "🟡", "warning"
    elif status == "CRITICAL":
        return "🔴", "critical"
    elif status == "MAINTENANCE":
        return "🔵", "maint"
    else:
        return "⚪", "idle"

def render_shop_section(shop_name: str, stations: List[Dict[str, Any]], selected_id: str):
    """Render a single shop section with compact station nodes."""
    st.markdown(f"""
    <div class="shop-header">
        <div class="shop-title">{shop_name}</div>
        <div class="shop-badge">{len(stations)} Stations ({stations[0]['id']} → {stations[-1]['id']})</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render stations in a responsive horizontal grid of columns
    num_cols = len(stations)
    cols = st.columns(num_cols)
    
    for idx, s in enumerate(stations):
        sid = s["id"]
        status = s["status"]
        emoji, cls = get_status_emoji_and_class(status)
        is_selected = (selected_id == sid)
        
        # Tooltip text for hover
        tooltip = (
            f"{sid} — {s['name']}\n"
            f"Status: {status.title()}\n"
            f"Cycle Time: {s['cycle_time']} min (Nominal: {s['nominal_cycle_time']}m)\n"
            f"Queue: {s['queue_length']}/{s['buffer_capacity']}\n"
            f"Utilization: {s['utilization']}%"
        )
        
        # Label contains ONLY status dot and Station ID (e.g. 🟢 S23)
        btn_label = f"{emoji} {sid}"
        
        with cols[idx]:
            btn_type = "primary" if is_selected else "secondary"
            if st.button(btn_label, key=f"st_btn_{sid}", help=tooltip, type=btn_type, use_container_width=True):
                # Update selected station in session state
                if st.session_state.get("selected_station_id") == sid:
                    # Toggle close if already selected
                    st.session_state.selected_station_id = None
                else:
                    st.session_state.selected_station_id = sid
                st.rerun()

def render_assembly_line():
    """Render the full 35-station assembly line divided into 3 shops."""
    all_stations = get_all_stations_data()
    selected_id = st.session_state.get("selected_station_id", "")
    
    # 1. BIW / Body Construction (S1 - S10)
    biw_stations = [s for s in all_stations if s["shop"] == "BODY / BIW"]
    st.markdown('<div class="shop-section">', unsafe_allow_html=True)
    render_shop_section("BODY / BIW", biw_stations, selected_id)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Flow Connector
    st.markdown("<div style='text-align: center; color: #475569; font-size: 11px; margin: -6px 0 6px 0; font-family: monospace;'>▼ TRANSFER CONVEYOR & BUFFER (S10 → S11) ▼</div>", unsafe_allow_html=True)
    
    # 2. Paint Shop (S11 - S20)
    paint_stations = [s for s in all_stations if s["shop"] == "PAINT"]
    st.markdown('<div class="shop-section">', unsafe_allow_html=True)
    render_shop_section("PAINT SHOP", paint_stations, selected_id)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Flow Connector
    st.markdown("<div style='text-align: center; color: #475569; font-size: 11px; margin: -6px 0 6px 0; font-family: monospace;'>▼ PAINTED BODY ACCUMULATION BUFFER (S20 → S21) ▼</div>", unsafe_allow_html=True)
    
    # 3. General Assembly + EOL (S21 - S35)
    ga_stations = [s for s in all_stations if s["shop"] == "GENERAL ASSEMBLY + EOL"]
    st.markdown('<div class="shop-section">', unsafe_allow_html=True)
    render_shop_section("GENERAL ASSEMBLY + EOL", ga_stations, selected_id)
    st.markdown('</div>', unsafe_allow_html=True)
