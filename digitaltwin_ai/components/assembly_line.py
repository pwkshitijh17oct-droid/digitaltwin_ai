"""
DIGITALTWIN.AI — 35-Station Assembly Line Component
Renders compact station nodes across 3 manufacturing shops.
"""

import streamlit as st
from typing import List, Dict, Any

STATUS_DOTS = {
    "RUNNING": "🟢",
    "RECOVERY": "🔵",
    "BLOCKED": "🔴",
    "STARVED": "⚪",
    "IDLE": "🟡",
    "DOWN": "🔴",
    "MAINTENANCE": "🔧"
}

def render_assembly_line(stations: List[Dict[str, Any]], selected_station_id: str = None):
    st.markdown("<div style='font-size:14px; font-weight:700; color:#F8FAFC; margin-bottom:10px; display:flex; align-items:center; justify-content:space-between;'><span>35-STATION VIRTUAL ASSEMBLY LINE</span><span style='font-size:11px; font-weight:400; color:#64748B;'>Click any station node to inspect details</span></div>", unsafe_allow_html=True)
    
    # Group stations by shop
    body_shop = [s for s in stations if s["shop"] == "Body Shop"]
    paint_shop = [s for s in stations if s["shop"] == "Paint Shop"]
    ga_shop = [s for s in stations if s["shop"] == "General Assembly"]
    
    shops = [
        ("BODY / BIW SHOP (S01–S10)", body_shop),
        ("PAINT SHOP (S11–S20)", paint_shop),
        ("GENERAL ASSEMBLY & EOL (S21–S35)", ga_shop)
    ]
    
    for shop_name, shop_stations in shops:
        st.markdown(
            f"""
            <div class="shop-section">
                <div class="shop-header">
                    <span class="shop-title">{shop_name}</span>
                    <span class="shop-badge">{len(shop_stations)} Stations</span>
                </div>
            """,
            unsafe_allow_html=True
        )
        
        # Render stations horizontally
        cols = st.columns(len(shop_stations))
        for idx, station in enumerate(shop_stations):
            sid = station["id"]
            name = station["name"]
            status = station["status"]
            ct = station["current_cycle_time"]
            q_len = station["queue_length"]
            q_cap = station["queue_capacity"]
            health_pct = station["equipment_health_pct"]
            
            dot = STATUS_DOTS.get(status, "🟢")
            
            # Tooltip preview
            tooltip_text = (
                f"{sid} — {name}\n"
                f"Status: {status}\n"
                f"Cycle Time: {ct} min\n"
                f"Queue: {q_len}/{q_cap}\n"
                f"Health: {health_pct}%"
            )
            
            is_selected = (selected_station_id == sid)
            btn_label = f"{dot} {sid}"
            
            with cols[idx]:
                if st.button(
                    btn_label,
                    key=f"stn_btn_{sid}",
                    help=tooltip_text,
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state["selected_station"] = sid
                    st.session_state["drawer_open"] = True
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
