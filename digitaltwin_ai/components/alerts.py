"""
DIGITALTWIN.AI — Global Alert Banner Component
"""

import streamlit as st
import data.adapter as adapter

def render_global_alerts():
    alerts = adapter.get_global_alerts()
    if not alerts:
        return

    for alert in alerts[:2]:  # Show top 2 critical alerts
        aid = alert["id"]
        title = alert["title"]
        desc = alert["desc"]
        target = alert["target_station"]
        
        col_text, col_btn = st.columns([5, 1])
        with col_text:
            st.markdown(
                f"""
                <div class="alert-banner">
                    <div>
                        <div class="alert-title">{title}</div>
                        <div class="alert-desc">{desc}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_btn:
            if st.button(f"Inspect {target}", key=f"alert_btn_{aid}", use_container_width=True):
                st.session_state["selected_station"] = target
                st.session_state["drawer_open"] = True
                st.rerun()
