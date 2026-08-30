"""
DIGITALTWIN.AI — Permanent Sidebar & Simulation Controls Component
"""

import streamlit as st
import data.adapter as adapter

def render_sidebar():
    with st.sidebar:
        # Brand Header
        st.markdown(
            """
            <div class="dt-brand">
                <div class="dt-logo-icon">DT</div>
                <div>
                    <div class="dt-brand-title">DIGITALTWIN.AI</div>
                    <div class="dt-brand-subtitle">35-Station Assembly Line</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Navigation
        st.markdown("<div style='font-size:11px; font-weight:700; color:#64748B; letter-spacing:0.08em; margin-bottom:8px;'>NAVIGATION</div>", unsafe_allow_html=True)
        
        pages = [
            ("overview", "🏭 Overview"),
            ("bottleneck", "⚠ Bottleneck Intelligence"),
            ("quality", "🧠 Quality Intelligence"),
            ("analytics", "📊 Analytics")
        ]
        
        active_page = st.session_state.get("active_page", "overview")
        
        for key, label in pages:
            is_active = (active_page == key)
            button_style = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_btn_{key}", use_container_width=True, type=button_style):
                st.session_state["active_page"] = key
                st.rerun()

        st.markdown("<hr style='border-color:#1E293B; margin: 16px 0;'>", unsafe_allow_html=True)
        
        # Simulation Control Section
        st.markdown("<div style='font-size:11px; font-weight:700; color:#64748B; letter-spacing:0.08em; margin-bottom:8px;'>SIMULATION CONTROL</div>", unsafe_allow_html=True)
        
        sim_state = adapter.get_simulation_state()
        status = sim_state["status"]
        
        # Status Pill
        if status == "RUNNING":
            pill_html = '<div class="status-pill live"><span class="pulse-dot green"></span> RUNNING</div>'
        elif status == "PAUSED":
            pill_html = '<div class="status-pill paused"><span class="pulse-dot yellow"></span> PAUSED</div>'
        else:
            pill_html = '<div class="status-pill stopped"><span class="pulse-dot grey"></span> READY</div>'
            
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; background:#111622; padding:8px 10px; border-radius:6px; border:1px solid #1E293B;">
                <span style="font-size:11px; color:#94A3B8; font-weight:600;">Current state:</span>
                {pill_html}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Action Controls
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("▶ RUN", key="ctrl_run", use_container_width=True, disabled=(status == "RUNNING")):
                if status == "PAUSED":
                    adapter.resume_simulation()
                else:
                    adapter.start_simulation()
                st.rerun()
        with col2:
            if st.button("⏸ PAUSE", key="ctrl_pause", use_container_width=True, disabled=(status != "RUNNING")):
                adapter.pause_simulation()
                st.rerun()
        with col3:
            if st.button("↻ RESET", key="ctrl_reset", use_container_width=True):
                adapter.reset_simulation()
                st.rerun()

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # Simulation Speed Control
        st.markdown("<div style='font-size:11px; color:#94A3B8; font-weight:600; margin-bottom:4px;'>Simulation speed:</div>", unsafe_allow_html=True)
        speed_opts = ["1×", "2×", "5×"]
        curr_mult = st.session_state.get("speed_multiplier", "1×")
        selected_speed = st.radio(
            "Speed",
            options=speed_opts,
            index=speed_opts.index(curr_mult) if curr_mult in speed_opts else 0,
            horizontal=True,
            key="speed_radio",
            label_visibility="collapsed"
        )
        
        if selected_speed != curr_mult:
            st.session_state["speed_multiplier"] = selected_speed
            mult_val = float(selected_speed.replace("×", ""))
            adapter.set_simulation_speed(mult_val)
            st.rerun()

        # Simulation Time Readout
        sim_time_fmt = sim_state["simulation_time_formatted"]
        sim_hours = round(sim_state["simulation_time_hours"], 2)
        
        st.markdown(
            f"""
            <div style="margin-top:14px; background:#0B0E14; border:1px solid #1E293B; border-radius:6px; padding:10px; font-family:'JetBrains Mono', monospace;">
                <div style="font-size:10px; color:#64748B; text-transform:uppercase;">SIMULATION TIME</div>
                <div style="font-size:14px; font-weight:700; color:#38BDF8; margin-top:2px;">{sim_time_fmt}</div>
                <div style="font-size:10px; color:#94A3B8; margin-top:2px;">({sim_hours} sim hrs)</div>
            </div>
            """,
            unsafe_allow_html=True
        )
