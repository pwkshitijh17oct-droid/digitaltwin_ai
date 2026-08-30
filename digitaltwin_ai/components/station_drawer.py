"""
DIGITALTWIN.AI — Right-Side Station Detail Drawer Component
Displays operational metrics, equipment health, and dynamic sensor coverage.
"""

import streamlit as st
import data.adapter as adapter

def render_station_drawer(station_id: str):
    station = adapter.get_station_data(station_id)
    if not station:
        st.error(f"Station {station_id} not found.")
        return

    sid = station["id"]
    name = station["name"]
    status = station["status"]
    family = station["family"]
    shop = station["shop"]
    
    # Close button header
    col_title, col_close = st.columns([4, 1])
    with col_title:
        st.markdown(f"<div style='font-size:20px; font-weight:800; color:#38BDF8; font-family:\"JetBrains Mono\", monospace;'>{sid}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:14px; font-weight:700; color:#F8FAFC;'>{name}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:11px; color:#64748B;'>Shop: {shop} | Family: {family}</div>", unsafe_allow_html=True)
    with col_close:
        if st.button("✖ Close", key="btn_close_drawer", use_container_width=True):
            st.session_state["drawer_open"] = False
            st.rerun()

    st.markdown("<hr style='border-color:#1E293B; margin:10px 0;'>", unsafe_allow_html=True)

    # Operational State Badge
    state_color = "#10B981" if status == "RUNNING" else ("#F59E0B" if status in ("IDLE", "RECOVERY") else "#EF4444")
    st.markdown(
        f"""
        <div style="background:#0B0E14; border:1px solid #1E293B; border-radius:6px; padding:10px; margin-bottom:12px;">
            <div style="font-size:10px; color:#64748B; text-transform:uppercase;">OPERATIONAL STATE</div>
            <div style="font-size:16px; font-weight:700; color:{state_color}; font-family:'JetBrains Mono', monospace; margin-top:2px;">
                {status}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Operational Data
    st.markdown("<div style='font-size:12px; font-weight:700; color:#94A3B8; margin-bottom:6px;'>PROCESS / OPERATIONAL DATA</div>", unsafe_allow_html=True)
    
    base_ct = station["base_cycle_time"]
    curr_ct = station["current_cycle_time"]
    slowdown = station["health_slowdown"]
    q_len = station["queue_length"]
    q_cap = station["queue_capacity"]
    avg_wait = station["average_waiting_time"]
    processed = station["vehicles_processed"]

    mcol1, mcol2 = st.columns(2)
    with mcol1:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-box-label">Current Cycle Time</div>
                <div class="metric-box-val">{curr_ct} min</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div class="metric-box" style="margin-top:6px;">
                <div class="metric-box-label">Queue Length</div>
                <div class="metric-box-val">{q_len} / {q_cap}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div class="metric-box" style="margin-top:6px;">
                <div class="metric-box-label">Vehicles Processed</div>
                <div class="metric-box-val">{processed}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with mcol2:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-box-label">Base Cycle Time</div>
                <div class="metric-box-val">{base_ct} min</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div class="metric-box" style="margin-top:6px;">
                <div class="metric-box-label">CT Health Slowdown</div>
                <div class="metric-box-val">+{slowdown} min</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div class="metric-box" style="margin-top:6px;">
                <div class="metric-box-label">Avg Waiting Time</div>
                <div class="metric-box-val">{avg_wait} min</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<hr style='border-color:#1E293B; margin:12px 0;'>", unsafe_allow_html=True)

    # Equipment Health & Maintenance
    st.markdown("<div style='font-size:12px; font-weight:700; color:#94A3B8; margin-bottom:6px;'>EQUIPMENT HEALTH & MAINTENANCE</div>", unsafe_allow_html=True)
    
    if family == "buffer":
        st.markdown(
            """
            <div style="background:#0B0E14; border:1px solid #1E293B; border-radius:6px; padding:10px; color:#64748B; font-size:12px;">
                N/A — Buffer Station (No mechanical tool health modeled)
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        health_pct = station["equipment_health_pct"]
        health_color = "#10B981" if health_pct >= 85.0 else ("#F59E0B" if health_pct >= 70.0 else "#EF4444")
        tool_life = station["tool_life_vehicles"]
        since_last = station["vehicles_since_last_replacement"]
        auto_cnt = station["automatic_replacement_count"]
        manual_cnt = station["manual_replacement_count"]

        st.markdown(
            f"""
            <div style="background:#0B0E14; border:1px solid #1E293B; border-radius:6px; padding:10px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <span style="font-size:11px; color:#94A3B8;">Health Status</span>
                    <span style="font-size:14px; font-weight:700; color:{health_color}; font-family:'JetBrains Mono';">{health_pct}%</span>
                </div>
                <div style="background:#1E293B; height:6px; border-radius:3px; overflow:hidden;">
                    <div style="background:{health_color}; width:{health_pct}%; height:100%;"></div>
                </div>
                <div style="font-size:10px; color:#64748B; margin-top:6px;">
                    Tool life: {since_last} / {tool_life} vehicles processed
                </div>
                <div style="font-size:10px; color:#64748B;">
                    Replacements: {auto_cnt} Auto | {manual_cnt} Manual Reset
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("🔧 Trigger Operator Health Reset", key=f"btn_ht_reset_{sid}", use_container_width=True):
            res = adapter.trigger_operator_health_reset(sid)
            st.success(f"Health reset applied to {sid}: {res}")
            st.rerun()

    st.markdown("<hr style='border-color:#1E293B; margin:12px 0;'>", unsafe_allow_html=True)

    # Dynamic Sensor Coverage
    st.markdown("<div style='font-size:12px; font-weight:700; color:#94A3B8; margin-bottom:6px;'>DYNAMIC SENSOR COVERAGE</div>", unsafe_allow_html=True)
    
    sensor_info = adapter.get_sensor_parameters(sid)
    if sensor_info["has_sensor_coverage"]:
        st.markdown(
            """
            <div class="status-pill live" style="margin-bottom:8px;">
                ● SENSOR COVERAGE ACTIVE
            </div>
            """,
            unsafe_allow_html=True
        )
        params = sensor_info["parameters"]
        if params:
            scol1, scol2 = st.columns(2)
            for idx, p in enumerate(params):
                target_col = scol1 if idx % 2 == 0 else scol2
                with target_col:
                    st.markdown(
                        f"""
                        <div class="param-card">
                            <div class="param-name">{p['name']}</div>
                            <div class="param-val">{p['value']} <span style="font-size:10px; color:#64748B;">{p['unit']}</span></div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.markdown("<div style='font-size:11px; color:#64748B;'>No parameter values active.</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <div class="status-pill stopped" style="margin-bottom:8px;">
                ○ SENSOR COVERAGE NOT AVAILABLE
            </div>
            <div style="background:#0B0E14; border:1px solid #1E293B; border-radius:6px; padding:10px; color:#94A3B8; font-size:11px;">
                No IoT sensor coverage is configured for this station.<br>
                Process and operational telemetry remains fully available.
            </div>
            """,
            unsafe_allow_html=True
        )
