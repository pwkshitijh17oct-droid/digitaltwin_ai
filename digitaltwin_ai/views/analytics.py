"""
DIGITALTWIN.AI — Analytics & Telemetry Page
Historical telemetry exploration, equipment health trends, and system architecture.
"""

import streamlit as st
import data.adapter as adapter
from components.charts import (
    build_equipment_health_chart,
    build_telemetry_trend_chart
)

def render_analytics_page():
    st.markdown(
        """
        <div style="margin-bottom:14px; border-bottom:1px solid #1E293B; padding-bottom:10px;">
            <h1 style="font-size:22px; font-weight:800; color:#F8FAFC; margin:0;">📊 Analytics & Telemetry</h1>
            <div style="font-size:12px; color:#94A3B8;">Historical production telemetry, equipment degradation, and digital twin system data-flow</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    stations = adapter.get_all_stations_data()
    st_ids = [s["id"] for s in stations]

    # Analytics Filters
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        shop_filter = st.selectbox("Shop Filter", options=["All Shops", "Body Shop", "Paint Shop", "General Assembly"], key="analytics_shop")
    with fcol2:
        station_options = ["All Stations"] + st_ids
        selected_st_filter = st.selectbox("Station Filter", options=station_options, key="analytics_station")
    with fcol3:
        metric_filter = st.selectbox("Metric Filter", options=["Cycle Time", "Queue Length", "Equipment Health", "Defect Probability"], key="analytics_metric")

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # Equipment Health Overview Chart
    fig_health = build_equipment_health_chart(stations)
    st.plotly_chart(fig_health, use_container_width=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # Historical Telemetry Trends
    filter_sid = None if selected_st_filter == "All Stations" else selected_st_filter
    df_telemetry = adapter.get_telemetry_dataframe(station_id=filter_sid, limit=500)

    tcol1, tcol2 = st.columns(2)
    with tcol1:
        metric_map = {
            "Cycle Time": "cycle_time_min",
            "Queue Length": "queue_length",
            "Equipment Health": "equipment_health",
            "Defect Probability": "defect_probability"
        }
        metric_col = metric_map.get(metric_filter, "cycle_time_min")
        fig_trend = build_telemetry_trend_chart(df_telemetry, metric_col, f"Historical Telemetry Trend: {metric_filter}")
        st.plotly_chart(fig_trend, use_container_width=True)

    with tcol2:
        st.markdown("<div style='font-size:14px; font-weight:700; color:#F8FAFC; margin-bottom:8px;'>Recent Telemetry Records</div>", unsafe_allow_html=True)
        if not df_telemetry.empty:
            display_cols = [c for c in ["simulation_time_hours", "station_id", "vehicle_id", "cycle_time_min", "equipment_health", "queue_length", "defect_probability"] if c in df_telemetry.columns]
            st.dataframe(
                df_telemetry[display_cols].tail(10),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No telemetry records logged yet. Start the simulation to generate telemetry.")

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # System & End-to-End Data Flow Architecture Diagram
    st.markdown("<div style='font-size:14px; font-weight:700; color:#38BDF8; margin-bottom:8px;'>DIGITAL TWIN SYSTEM ARCHITECTURE & DATA FLOW</div>", unsafe_allow_html=True)
    
    st.markdown(
        """
        <div style="background:#0F172A; border:1px solid #1E293B; border-radius:8px; padding:16px;">
            <div style="font-size:12px; color:#94A3B8; margin-bottom:12px;">
                End-to-end data pipeline connecting the physical simulator controller, data adapter layer, real-time control center, and future ML inference engines:
            </div>
            
            <pre style="background:#0B0E14; border:1px solid #1E293B; border-radius:6px; padding:12px; color:#38BDF8; font-family:'JetBrains Mono', monospace; font-size:11px; overflow-x:auto;">
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 INTEGRATED SIMULATOR                                   │
│            (Line Engine, Sensor Engine, Health Engine, Defect Engine, Telemetry)       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            v
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 DATA ADAPTER LAYER                                     │
│                (get_simulation_state, get_station_data, get_sensor_parameters)       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            v
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              DIGITALTWIN.AI CONTROL CENTER                             │
│                  (Streamlit Dashboard, Persistent Controller Singleton)                │
└──────────────┬────────────────────────────┬────────────────────────────┬───────────────┘
               │                            │                            │
               v                            v                            v
┌────────────────────────────┐┌───────────────────────────┐┌───────────────────────────┐
│     35-STATION OVERVIEW    ││  BOTTLENECK INTELLIGENCE  ││   QUALITY INTELLIGENCE    │
│  (Shop Nodes, Detail Drawer││ (Pressure Scores, Takt    ││ (Defect Engine, Adaptive  │
│   Health, Sensor Coverage) ││  Ratios, Queue Trends)    ││  Testing, ML Ready Router)│
└────────────────────────────┘└───────────────────────────┘└───────────────────────────┘
            </pre>
        </div>
        """,
        unsafe_allow_html=True
    )
