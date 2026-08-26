"""
Global alert banner component for high-priority bottleneck and defect events.
"""

import streamlit as st
from data.data_adapter import get_global_alerts

def render_global_alerts():
    """Render high priority alerts with quick jump button."""
    alerts = get_global_alerts()
    if not alerts:
        return
    
    for alert in alerts:
        col_text, col_btn = st.columns([5, 1])
        with col_text:
            st.markdown(f"""
            <div class="alert-banner">
                <div>
                    <div class="alert-title">{alert['title']}</div>
                    <div class="alert-desc">{alert['desc']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_btn:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            if st.button(f"🔍 Inspect {alert['target_station']}", key=f"alert_btn_{alert['id']}", use_container_width=True):
                st.session_state.current_page = "Overview"
                st.session_state.selected_station_id = alert["target_station"]
                st.rerun()
