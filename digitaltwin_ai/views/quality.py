"""
DIGITALTWIN.AI — Quality Intelligence Page
Simulated Defect & Quality Monitoring Stream & Future ML Integration Architecture.
"""

import streamlit as st
import data.adapter as adapter

def render_quality_page():
    st.markdown(
        """
        <div style="margin-bottom:14px; border-bottom:1px solid #1E293B; padding-bottom:10px;">
            <h1 style="font-size:22px; font-weight:800; color:#F8FAFC; margin:0;">🧠 Quality Intelligence</h1>
            <div style="font-size:12px; color:#94A3B8;">Simulated defect monitoring stream & adaptive quality test protocols</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    q_data = adapter.get_quality_intelligence()
    vehicles = q_data["vehicles"]

    # Header Summary Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Monitored Telemetry Events</div>
                <div class="kpi-value">{q_data['monitored_count']}</div>
                <div class="kpi-subtext">Real-time defect evaluations</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="kpi-card warning">
                <div class="kpi-label">High Defect Risk Vehicles</div>
                <div class="kpi-value" style="color:#F59E0B;">{q_data['high_risk_count']}</div>
                <div class="kpi-subtext">Requiring adaptive test / hold</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            """
            <div class="kpi-card success">
                <div class="kpi-label">Quality Protocol Status</div>
                <div class="kpi-value" style="color:#10B981;">ACTIVE</div>
                <div class="kpi-subtext">DefectEngine evaluation active</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Simulated Quality Stream Table
    st.markdown("<div style='font-size:14px; font-weight:700; color:#F8FAFC; margin-bottom:8px;'>SIMULATED QUALITY MONITORING STREAM</div>", unsafe_allow_html=True)
    
    col_list, col_detail = st.columns([3, 2])
    
    with col_list:
        v_selected = st.session_state.get("selected_quality_vehicle", vehicles[0]["vehicle_id"] if vehicles else "V0128")
        
        table_rows = []
        for v in vehicles:
            table_rows.append({
                "Vehicle ID": v["vehicle_id"],
                "Station": f"{v['station_id']} — {v['station_name']}",
                "Defect Risk": f"{v['defect_probability']}%",
                "Risk Level": v["risk_level"],
                "Primary Cause": v["primary_cause"],
                "Buyoff Status": v["test_status"]
            })
            
        st.dataframe(
            table_rows,
            hide_index=True,
            use_container_width=True
        )
        
        # Vehicle Selector
        v_options = [v["vehicle_id"] for v in vehicles]
        selected_vid = st.selectbox(
            "Select Vehicle ID to Inspect Adaptive Test Protocol:",
            options=v_options,
            index=v_options.index(v_selected) if v_selected in v_options else 0,
            key="quality_v_select"
        )
        st.session_state["selected_quality_vehicle"] = selected_vid

    with col_detail:
        target_v = next((v for v in vehicles if v["vehicle_id"] == selected_vid), vehicles[0])
        
        v_risk = target_v["risk_level"]
        risk_color = "#EF4444" if v_risk == "HIGH" else ("#F59E0B" if v_risk == "MODERATE" else "#10B981")
        
        st.markdown(
            f"""
            <div class="adaptive-test-card">
                <div style="font-size:10px; font-weight:700; color:#38BDF8; letter-spacing:0.08em; text-transform:uppercase;">ADAPTIVE QUALITY TEST PROTOCOL</div>
                <div style="font-size:18px; font-weight:800; color:#F8FAFC; font-family:'JetBrains Mono'; margin-top:2px;">
                    {target_v['vehicle_id']} @ {target_v['station_id']}
                </div>
                
                <div style="margin-top:10px; background:#0B0E14; border:1px solid #1E293B; border-radius:6px; padding:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:11px; color:#94A3B8;">Defect Risk Score</span>
                        <span style="font-size:15px; font-weight:700; color:{risk_color}; font-family:'JetBrains Mono';">{target_v['defect_probability']}% ({v_risk})</span>
                    </div>
                    <div style="font-size:11px; color:#CBD5E1; margin-top:6px;">
                        <b>Primary Root Cause:</b> <code>{target_v['primary_cause']}</code>
                    </div>
                </div>

                <div style="margin-top:12px;">
                    <div style="font-size:11px; font-weight:700; color:#94A3B8; margin-bottom:6px;">AUTOMATED ADAPTIVE TEST SEQUENCE:</div>
                    
                    <div class="test-item">
                        <span>✅</span>
                        <span>Step 1: Telemetry Signal Drift Assessment</span>
                    </div>
                    <div class="test-item">
                        <span>{'⚠️' if target_v['defect_flag'] else '✅'}</span>
                        <span>Step 2: {target_v['adaptive_test']['test_name']}</span>
                    </div>
                    <div class="test-item">
                        <span>{'🔴' if target_v['defect_flag'] else '🟢'}</span>
                        <span>Step 3: Buyoff Decision — <b>{target_v['test_status']}</b></span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # Future ML Architecture Blueprint
    st.markdown(
        """
        <div style="background:#0F172A; border:1px solid #1E293B; border-radius:8px; padding:16px;">
            <div style="font-size:14px; font-weight:700; color:#38BDF8; margin-bottom:6px;">FUTURE ML MANAGER ARCHITECTURE</div>
            <div style="font-size:12px; color:#94A3B8; line-height:1.5;">
                The DIGITALTWIN.AI platform is designed to support station-specific machine learning models (S01 Model, S25 Model, S35 Model) without requiring frontend re-architecture:
            </div>
            <div style="font-family:'JetBrains Mono', monospace; font-size:11px; color:#E2E8F0; background:#0B0E14; border:1px solid #1E293B; border-radius:6px; padding:12px; margin-top:10px; line-height:1.6;">
                SIMULATOR SENSOR TELEMETRY<br>
                &nbsp;&nbsp;&nbsp;&nbsp;↓<br>
                DATA ADAPTER (get_quality_predictions)<br>
                &nbsp;&nbsp;&nbsp;&nbsp;↓<br>
                ML MANAGER (Model Router & Feature Normalizer)<br>
                &nbsp;&nbsp;&nbsp;&nbsp;├── S01 MODEL (Framing Weld Defect Model)<br>
                &nbsp;&nbsp;&nbsp;&nbsp;├── S25 MODEL (Powertrain Marriage Torque Drift Model)<br>
                &nbsp;&nbsp;&nbsp;&nbsp;└── S35 MODEL (Final Inspection Multimodal Quality Model)<br>
                &nbsp;&nbsp;&nbsp;&nbsp;↓<br>
                NORMALIZED QUALITY INTELLIGENCE DASHBOARD
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
