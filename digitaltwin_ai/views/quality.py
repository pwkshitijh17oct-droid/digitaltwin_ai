"""
Page 3 — Quality Intelligence.
Demonstrates ML-driven quality/defect prediction & Adaptive Quality Testing triggers.
"""

import streamlit as st
from data.data_adapter import get_quality_predictions, get_vehicle_quality_detail

def render_quality_page():
    """Render Quality Intelligence dashboard."""
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <h2 style="font-size: 20px; font-weight: 800; color: #F8FAFC; margin: 0; letter-spacing: 0.02em;">
            🧠 Quality Intelligence & Adaptive Testing
        </h2>
        <div style="font-size: 12px; color: #94A3B8; margin-top: 2px;">
            ML-driven anomaly detection & dynamic test protocol activation
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    q_data = get_quality_predictions()
    
    # Top KPIs
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Vehicles Monitored</div>
            <div class="kpi-value">{q_data['monitored_count']} <span style="font-size: 12px; color: #94A3B8;">active</span></div>
            <div class="kpi-subtext"><span style="color: #10B981;">● 100% Digital Line Coverage</span></div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card critical">
            <div class="kpi-label">High-Risk Vehicles</div>
            <div class="kpi-value" style="color: #EF4444;">{q_data['high_risk_count']} <span style="font-size: 12px; color: #94A3B8;">units</span></div>
            <div class="kpi-subtext"><span style="color: #EF4444;">⚠ Defect Probability > 70%</span></div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card warning">
            <div class="kpi-label">Adaptive Tests Activated</div>
            <div class="kpi-value" style="color: #F59E0B;">{q_data['tests_active_count']} <span style="font-size: 12px; color: #94A3B8;">sequences</span></div>
            <div class="kpi-subtext"><span style="color: #38BDF8;">⚡ Dynamic Protocol Triggered</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Vehicle Monitoring Table & Interactive Selection
    col_table, col_detail = st.columns([7, 5], gap="medium")
    
    selected_vid = st.session_state.get("selected_vehicle_id", "V128")
    
    with col_table:
        st.markdown("<p style='font-size: 12px; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; font-family: monospace;'>Active Vehicle Defect Risk Stream</p>", unsafe_allow_html=True)
        
        vehicles = q_data["vehicles"]
        for v in vehicles:
            vid = v["vehicle_id"]
            is_sel = (vid == selected_vid)
            r_color = "#EF4444" if v["risk_level"] == "HIGH" else ("#F59E0B" if v["risk_level"] == "MODERATE" else "#10B981")
            
            border_style = "border: 1px solid #38BDF8; background: #1A2234;" if is_sel else "border: 1px solid #1E293B; background: #121824;"
            
            st.markdown(f"""
            <div style="{border_style} border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 14px; font-weight: 800; font-family: 'JetBrains Mono', monospace; color: #38BDF8;">{vid}</span>
                        <span style="font-size: 11px; background: #0B0E14; border: 1px solid #1E293B; padding: 1px 6px; border-radius: 3px; color: #94A3B8; font-family: monospace;">
                            {v['station_id']} — {v['station_name']}
                        </span>
                    </div>
                    <span style="background: {r_color}22; color: {r_color}; border: 1px solid {r_color}66; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; font-family: monospace;">
                        {v['defect_prob']}% ({v['risk_level']})
                    </span>
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px; font-size: 11px; color: #CBD5E1;">
                    <div>Predicted Issue: <strong style="color: #F8FAFC;">{v['predicted_issue']}</strong></div>
                    <div style="color: {'#EF4444' if 'TEST' in v['recommended_action'] else '#10B981'}; font-weight: 600;">{v['recommended_action']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🔍 Inspect {vid} Signals & Test Log", key=f"btn_v_{vid}", use_container_width=True):
                st.session_state.selected_vehicle_id = vid
                st.rerun()

    # Detail Panel for Selected Vehicle
    with col_detail:
        v_detail = get_vehicle_quality_detail(selected_vid)
        if v_detail:
            r_color = "#EF4444" if v_detail["risk_level"] == "HIGH" else ("#F59E0B" if v_detail["risk_level"] == "MODERATE" else "#10B981")
            
            st.markdown(f"""
            <div class="drawer-container">
                <div class="drawer-header">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <h2 class="drawer-station-id" style="color: #38BDF8;">Vehicle {v_detail['vehicle_id']}</h2>
                        <span style="background: {r_color}22; color: {r_color}; border: 1px solid {r_color}66; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; font-family: monospace;">
                            {v_detail['risk_level']} RISK
                        </span>
                    </div>
                    <div class="drawer-station-name" style="font-size: 13px;">Location: {v_detail['station_id']} — {v_detail['station_name']}</div>
                </div>
                
                <!-- Defect Probability Visual Bar -->
                <div style="margin-bottom: 14px;">
                    <div style="display: flex; justify-content: space-between; font-size: 11px; color: #94A3B8; margin-bottom: 4px;">
                        <span>Defect Probability</span>
                        <span style="font-weight: 700; color: #F8FAFC; font-family: monospace;">{v_detail['defect_prob']}%</span>
                    </div>
                    <div style="background: #0B0E14; border-radius: 4px; height: 8px; overflow: hidden; border: 1px solid #1E293B;">
                        <div style="background: {r_color}; height: 100%; width: {v_detail['defect_prob']}%;"></div>
                    </div>
                </div>
                
                <!-- Sensor / Process Signals Contributing to Risk -->
                <p style="font-size: 11px; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">Contributing Process Signals</p>
                <div class="params-grid">
            """, unsafe_allow_html=True)
            
            for sig in v_detail.get("signals", []):
                s_status = sig.get("status", "NORMAL")
                s_cls = "normal" if s_status == "NORMAL" else ("warning" if s_status == "WARNING" else "critical")
                st.markdown(f"""
                <div class="param-card">
                    <div>
                        <div class="param-name">{sig['name']}</div>
                        <div class="param-val">{sig['value']}</div>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 4px;">
                        <span class="param-badge {s_cls}">{s_status}</span>
                        <span style="font-size: 9px; color: #64748B; font-family: monospace;">{sig.get('nominal', '')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Adaptive Quality Testing Section
            ad_test = v_detail.get("adaptive_test", {})
            if ad_test.get("active"):
                st.markdown(f"""
                <div class="adaptive-test-card" style="margin-top: 14px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-size: 11px; font-weight: 800; color: #38BDF8; text-transform: uppercase; letter-spacing: 0.08em;">
                            ⚡ ADAPTIVE QUALITY TEST ACTIVATED
                        </span>
                        <span class="status-pill live" style="font-size: 10px;">ACTIVE</span>
                    </div>
                    <div style="font-size: 11px; color: #94A3B8; margin-bottom: 10px;">
                        Trigger Rationale: <strong style="color: #F8FAFC;">{ad_test.get('trigger_reason')}</strong>
                    </div>
                    
                    <div style="background: #0B0E14; border: 1px solid #1E293B; border-radius: 6px; padding: 8px 10px;">
                        <div style="font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 6px;">Automated Test Suite</div>
                """, unsafe_allow_html=True)
                
                for item in ad_test.get("checklist", []):
                    icon = "✓" if item["status"] == "PASSED" else "✗"
                    i_color = "#10B981" if item["status"] == "PASSED" else ("#EF4444" if item["status"] == "FAILED" else "#F59E0B")
                    st.markdown(f"""
                    <div class="test-item">
                        <span style="color: {i_color}; font-weight: 800;">{icon}</span>
                        <span style="flex: 1;">{item['name']}</span>
                        <span style="color: {i_color}; font-weight: 700; font-family: monospace; font-size: 10px;">{item['status']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown(f"""
                    </div>
                    
                    <div style="margin-top: 10px; padding: 8px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 4px; display: flex; align-items: center; justify-content: space-between;">
                        <span style="font-size: 11px; color: #FCA5A5; font-weight: 600;">FINAL DISPOSITION:</span>
                        <span style="font-size: 12px; font-weight: 800; color: #EF4444; font-family: monospace;">{ad_test.get('result')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="margin-top: 14px; padding: 12px; background: #0B0E14; border: 1px solid #1E293B; border-radius: 6px;">
                    <div style="font-size: 11px; color: #94A3B8;">Adaptive testing not required. Status: <strong style="color: #10B981;">{ad_test.get('result')}</strong></div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("</div>", unsafe_allow_html=True)
