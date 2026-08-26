"""
Station Detail Drawer / Panel for DigitalTwin.ai.
Renders on the right side when a station is clicked while keeping the assembly line visible.
Dynamically renders sensor/process parameters according to adapter specifications.
"""

import streamlit as st
from data.data_adapter import get_station_data

def render_station_drawer(station_id: str):
    """Render detailed inspection drawer for the chosen station."""
    st_data = get_station_data(station_id)
    if not st_data:
        st.warning(f"Station {station_id} telemetry not found.")
        return

    status = st_data["status"]
    status_color = "#10B981" if status == "NORMAL" else ("#F59E0B" if status == "WARNING" else "#EF4444")
    
    st.markdown(f"""
    <div class="drawer-container">
        <div class="drawer-header">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <h2 class="drawer-station-id">{st_data['id']}</h2>
                <span style="background: {status_color}22; color: {status_color}; border: 1px solid {status_color}66; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace;">
                    {status}
                </span>
            </div>
            <div class="drawer-station-name">{st_data['name']}</div>
            <div style="font-size: 11px; color: #64748B;">Shop: {st_data['shop']} | Type: {st_data['category']}</div>
        </div>
        
        <!-- Process Information Grid -->
        <p style="font-size: 11px; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">Process Information</p>
        <div class="metric-grid">
            <div class="metric-box">
                <div class="metric-box-label">Cycle Time</div>
                <div class="metric-box-val">{st_data['cycle_time']} <span style="font-size: 11px; color: #64748B;">min</span></div>
            </div>
            <div class="metric-box">
                <div class="metric-box-label">CT Deviation</div>
                <div class="metric-box-val" style="color: {'#EF4444' if st_data['cycle_time_dev'] > 20 else ('#F59E0B' if st_data['cycle_time_dev'] > 10 else '#10B981')};">
                    {'+' if st_data['cycle_time_dev'] > 0 else ''}{st_data['cycle_time_dev']}%
                </div>
            </div>
            <div class="metric-box">
                <div class="metric-box-label">Queue Length</div>
                <div class="metric-box-val">{st_data['queue_length']} <span style="font-size: 11px; color: #64748B;">/ {st_data['buffer_capacity']}</span></div>
            </div>
            <div class="metric-box">
                <div class="metric-box-label">Utilization</div>
                <div class="metric-box-val">{st_data['utilization']}%</div>
            </div>
        </div>
        
        <!-- Dynamic Sensor / Process Parameters -->
        <p style="font-size: 11px; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; margin: 12px 0 6px 0;">Live Process Parameters</p>
        <div class="params-grid">
    """, unsafe_allow_html=True)
    
    # Dynamically render parameters
    params = st_data.get("parameters", [])
    for p in params:
        p_status = p.get("status", "NORMAL")
        p_cls = "normal" if p_status == "NORMAL" else ("warning" if p_status == "WARNING" else "critical")
        st.markdown(f"""
        <div class="param-card">
            <div>
                <div class="param-name">{p['name']}</div>
                <div class="param-val">{p['value']} <span style="font-size: 10px; color: #94A3B8;">{p['unit']}</span></div>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 4px;">
                <span class="param-badge {p_cls}">{p_status}</span>
                <span style="font-size: 9px; color: #64748B; font-family: monospace;">{p.get('nominal', '')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Bottleneck Risk Card
    b_risk = st_data.get("bottleneck_risk", 10.0)
    b_level = st_data.get("bottleneck_level", "LOW")
    b_card_cls = "high" if b_level == "CRITICAL" else ("med" if b_level == "WARNING" else "low")
    
    st.markdown(f"""
    <div class="risk-card {b_card_cls}">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span style="font-size: 11px; font-weight: 700; color: #CBD5E1;">BOTTLENECK PREDICTION</span>
            <span style="font-size: 12px; font-weight: 800; font-family: monospace;">{b_risk}% ({b_level})</span>
        </div>
        <div style="font-size: 11px; color: #94A3B8; margin-top: 4px;">
            Estimated time to critical threshold: <strong style="color: #F8FAFC;">{st_data.get('bottleneck_predicted_time', 'Stable')}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quality Risk Card
    q_risk = st_data.get("quality_risk", 5.0)
    q_level = st_data.get("quality_level", "LOW")
    q_card_cls = "high" if q_level == "HIGH" else ("med" if q_level == "MODERATE" else "low")
    
    st.markdown(f"""
    <div class="risk-card {q_card_cls}">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span style="font-size: 11px; font-weight: 700; color: #CBD5E1;">QUALITY DEFECT RISK</span>
            <span style="font-size: 12px; font-weight: 800; font-family: monospace;">{q_risk}% ({q_level})</span>
        </div>
        <div style="font-size: 11px; color: #94A3B8; margin-top: 4px;">
            Predicted issue: <strong style="color: #F8FAFC;">{st_data.get('predicted_defect', 'None')}</strong>
        </div>
    </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Action Buttons
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊 View Analytics", key="drawer_btn_analytics", use_container_width=True):
            st.session_state.current_page = "Analytics"
            st.session_state.analytics_station_filter = station_id
            st.rerun()
    with c2:
        if st.button("✖ Close Drawer", key="drawer_btn_close", use_container_width=True):
            st.session_state.selected_station_id = None
            st.rerun()
