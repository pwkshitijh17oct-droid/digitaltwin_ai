"""
Global persistent sidebar for DigitalTwin.ai.
Always accessible across all pages with simulation controls and navigation.
"""

import streamlit as st
from data.data_adapter import (
    get_simulation_state, 
    set_simulation_running, 
    set_simulation_speed, 
    reset_simulation,
    step_simulation
)

def render_sidebar():
    """Render the persistent global sidebar."""
    with st.sidebar:
        # Brand & Header
        st.markdown("""
        <div class="dt-brand">
            <div class="dt-logo-icon">DT</div>
            <div>
                <h1 class="dt-brand-title">DIGITALTWIN.AI</h1>
                <div class="dt-brand-subtitle">Assembly Line Control Center</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation
        st.markdown("<p style='font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.1em; margin: 12px 0 6px 0;'>Navigation</p>", unsafe_allow_html=True)
        
        pages = [
            ("🏭 Overview", "Overview"),
            ("⚠ Bottleneck Intelligence", "Bottleneck Intelligence"),
            ("🧠 Quality Intelligence", "Quality Intelligence"),
            ("📊 Analytics", "Analytics")
        ]
        
        curr_page = st.session_state.get("current_page", "Overview")
        
        for label, page_key in pages:
            is_active = (curr_page == page_key)
            # Render a custom button styled for navigation
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{page_key}", type=btn_type, use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()

        st.markdown("<hr style='border-color: #1E293B; margin: 18px 0 14px 0;'>", unsafe_allow_html=True)
        
        # Simulation Control Section
        sim_state = get_simulation_state()
        
        st.markdown("<p style='font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;'>Simulation Control</p>", unsafe_allow_html=True)
        
        status_cls = sim_state["status_class"]
        status_lbl = sim_state["status_label"]
        dot_color = "green" if status_cls == "live" else ("yellow" if status_cls == "paused" else "grey")
        
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: space-between; background: #111622; padding: 8px 12px; border-radius: 6px; border: 1px solid #1E293B; margin-bottom: 12px;">
            <span style="font-size: 12px; color: #94A3B8; font-weight: 600;">Status:</span>
            <div class="status-pill {status_cls}">
                <span class="pulse-dot {dot_color}"></span>
                {status_lbl}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Run / Pause / Reset Control Buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("▶️ Run", key="btn_sim_run", use_container_width=True):
                set_simulation_running(True)
                st.session_state.sim_running = True
                st.rerun()
        with col2:
            if st.button("⏸ Pause", key="btn_sim_pause", use_container_width=True):
                set_simulation_running(False)
                st.session_state.sim_running = False
                st.rerun()
        with col3:
            if st.button("↻ Reset", key="btn_sim_reset", use_container_width=True):
                reset_simulation()
                st.session_state.sim_running = False
                st.rerun()

        # Speed Multiplier
        st.markdown("<p style='font-size: 11px; color: #94A3B8; margin: 12px 0 4px 0; font-weight: 600;'>Simulation Speed</p>", unsafe_allow_html=True)
        speed_col1, speed_col2, speed_col3 = st.columns(3)
        curr_speed = sim_state["speed"]
        
        with speed_col1:
            if st.button("1x", key="spd_1x", type="primary" if curr_speed == 1 else "secondary", use_container_width=True):
                set_simulation_speed(1)
                st.rerun()
        with speed_col2:
            if st.button("2x", key="spd_2x", type="primary" if curr_speed == 2 else "secondary", use_container_width=True):
                set_simulation_speed(2)
                st.rerun()
        with speed_col3:
            if st.button("5x", key="spd_5x", type="primary" if curr_speed == 5 else "secondary", use_container_width=True):
                set_simulation_speed(5)
                st.rerun()
                
        # Mini system telemetry footer
        st.markdown(f"""
        <div style="margin-top: 24px; padding: 10px; background: #0B0E14; border: 1px solid #1E293B; border-radius: 6px; font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #64748B;">
            <div>LINE: 35 STATIONS (ONLINE)</div>
            <div>TICK: #{sim_state['tick']}</div>
            <div>ADAPTER: MOCK DATA LAYER</div>
            <div>LATENCY: 12ms</div>
        </div>
        """, unsafe_allow_html=True)
