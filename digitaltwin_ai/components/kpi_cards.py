"""
KPI Cards component for DigitalTwin.ai.
Strictly conforms to the requirement: DO NOT show OEE.
"""

import streamlit as st
from data.data_adapter import get_kpis

def render_kpi_cards():
    """Render top 4 compact KPI cards."""
    kpis = get_kpis()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card success">
            <div class="kpi-label">Production (Shift)</div>
            <div class="kpi-value">{kpis['production_actual']} <span style="font-size: 14px; color: #94A3B8;">/ {kpis['production_target']}</span></div>
            <div class="kpi-subtext">
                <span style="color: #10B981;">● {kpis['production_pct']}%</span> of shift plan
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Throughput Rate</div>
            <div class="kpi-value">{kpis['throughput_jph']} <span style="font-size: 13px; color: #94A3B8;">JPH</span></div>
            <div class="kpi-subtext">
                <span style="color: #38BDF8;">↗ {kpis['throughput_delta']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        b_class = kpis['current_bottleneck_class']
        st.markdown(f"""
        <div class="kpi-card {b_class}">
            <div class="kpi-label">Current Bottleneck</div>
            <div class="kpi-value" style="font-size: 16px; margin-top: 3px;">{kpis['current_bottleneck']}</div>
            <div class="kpi-subtext">
                <span style="color: {'#EF4444' if b_class == 'critical' else '#F59E0B'};">⚠ High cycle deviation</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="kpi-card {kpis['defect_risk_class']}">
            <div class="kpi-label">Overall Defect Risk</div>
            <div class="kpi-value">{kpis['overall_defect_risk']}</div>
            <div class="kpi-subtext">
                <span style="color: #F59E0B;">⚡ 2 Vehicles Flagged</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
