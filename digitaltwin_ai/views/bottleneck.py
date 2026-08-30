"""
DIGITALTWIN.AI — Bottleneck Intelligence Page
Identifies real-time constraints, bottleneck rankings, and trend-based projections.
"""

import streamlit as st
import data.adapter as adapter
from components.charts import (
    build_cycle_time_chart,
    build_queue_accumulation_chart,
    build_bottleneck_ranking_chart
)

def render_bottleneck_page():
    st.markdown(
        """
        <div style="margin-bottom:14px; border-bottom:1px solid #1E293B; padding-bottom:10px;">
            <h1 style="font-size:22px; font-weight:800; color:#F8FAFC; margin:0;">⚠ Bottleneck Intelligence</h1>
            <div style="font-size:12px; color:#94A3B8;">Real-time line constraint tracking, pressure rankings & analytical projections</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    intel = adapter.get_bottleneck_intelligence()
    current_b = intel["current_bottleneck"]
    predicted_b = intel["predicted_bottleneck"]
    rankings = intel["rankings"]
    takt = intel["line_takt"]
    stations = adapter.get_all_stations_data()

    # Current Bottleneck Highlight
    col1, col2 = st.columns(2)
    with col1:
        if current_b:
            cb_id = current_b["id"]
            cb_name = current_b["name"]
            cb_status = current_b["status"]
            cb_ct = current_b["current_cycle_time"]
            cb_q = current_b["queue_length"]
            cb_cap = current_b["queue_capacity"]
            cb_score = current_b["pressure_score"]

            st.markdown(
                f"""
                <div style="background:#121824; border:1px solid #EF4444; border-left:4px solid #EF4444; border-radius:8px; padding:16px;">
                    <div style="font-size:11px; font-weight:700; color:#EF4444; text-transform:uppercase;">PRIMARY CURRENT BOTTLENECK</div>
                    <div style="font-size:20px; font-weight:800; color:#F8FAFC; font-family:'JetBrains Mono'; margin-top:2px;">
                        {cb_id} — {cb_name}
                    </div>
                    <div style="display:flex; gap:16px; margin-top:10px;">
                        <div>
                            <div style="font-size:10px; color:#64748B;">STATE</div>
                            <div style="font-size:13px; font-weight:700; color:#EF4444; font-family:'JetBrains Mono';">{cb_status}</div>
                        </div>
                        <div>
                            <div style="font-size:10px; color:#64748B;">CYCLE TIME</div>
                            <div style="font-size:13px; font-weight:700; color:#F8FAFC; font-family:'JetBrains Mono';">{cb_ct} min</div>
                        </div>
                        <div>
                            <div style="font-size:10px; color:#64748B;">LINE TAKT</div>
                            <div style="font-size:13px; font-weight:700; color:#38BDF8; font-family:'JetBrains Mono';">{takt} min</div>
                        </div>
                        <div>
                            <div style="font-size:10px; color:#64748B;">QUEUE</div>
                            <div style="font-size:13px; font-weight:700; color:#F59E0B; font-family:'JetBrains Mono';">{cb_q} / {cb_cap}</div>
                        </div>
                        <div>
                            <div style="font-size:10px; color:#64748B;">PRESSURE</div>
                            <div style="font-size:13px; font-weight:700; color:#EF4444; font-family:'JetBrains Mono';">{cb_score}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.info("No active bottleneck detected. Line operating at nominal pace.")

    with col2:
        if predicted_b:
            pb_id = predicted_b["id"]
            pb_name = predicted_b["name"]
            pb_status = predicted_b["status"]
            pb_ct = predicted_b["current_cycle_time"]
            pb_q = predicted_b["queue_length"]
            pb_score = predicted_b["pressure_score"]

            st.markdown(
                f"""
                <div style="background:#121824; border:1px solid #F59E0B; border-left:4px solid #F59E0B; border-radius:8px; padding:16px;">
                    <div style="font-size:11px; font-weight:700; color:#F59E0B; text-transform:uppercase;">TREND-BASED PROJECTION (SECONDARY CONSTRAINT)</div>
                    <div style="font-size:20px; font-weight:800; color:#F8FAFC; font-family:'JetBrains Mono'; margin-top:2px;">
                        {pb_id} — {pb_name}
                    </div>
                    <div style="display:flex; gap:16px; margin-top:10px;">
                        <div>
                            <div style="font-size:10px; color:#64748B;">STATE</div>
                            <div style="font-size:13px; font-weight:700; color:#F59E0B; font-family:'JetBrains Mono';">{pb_status}</div>
                        </div>
                        <div>
                            <div style="font-size:10px; color:#64748B;">CYCLE TIME</div>
                            <div style="font-size:13px; font-weight:700; color:#F8FAFC; font-family:'JetBrains Mono';">{pb_ct} min</div>
                        </div>
                        <div>
                            <div style="font-size:10px; color:#64748B;">QUEUE</div>
                            <div style="font-size:13px; font-weight:700; color:#F59E0B; font-family:'JetBrains Mono';">{pb_q} units</div>
                        </div>
                        <div>
                            <div style="font-size:10px; color:#64748B;">PRESSURE</div>
                            <div style="font-size:13px; font-weight:700; color:#F59E0B; font-family:'JetBrains Mono';">{pb_score}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Plotly Trend Visualizations
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        fig_ct = build_cycle_time_chart(stations, takt)
        st.plotly_chart(fig_ct, use_container_width=True)

    with chart_col2:
        fig_q = build_queue_accumulation_chart(stations)
        st.plotly_chart(fig_q, use_container_width=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Pressure Rankings & Ranking Chart
    rcol1, rcol2 = st.columns([1, 1])
    with rcol1:
        fig_rank = build_bottleneck_ranking_chart(rankings)
        st.plotly_chart(fig_rank, use_container_width=True)

    with rcol2:
        st.markdown("<div style='font-size:14px; font-weight:700; color:#F8FAFC; margin-bottom:8px;'>Station Pressure Table</div>", unsafe_allow_html=True)
        
        table_data = []
        for idx, s in enumerate(rankings[:8], 1):
            table_data.append({
                "Rank": f"#{idx}",
                "Station": s["id"],
                "Name": s["name"],
                "Shop": s["shop"],
                "State": s["status"],
                "CT (min)": s["current_cycle_time"],
                "Queue": f"{s['queue_length']}/{s['queue_capacity']}",
                "Pressure Score": s["pressure_score"]
            })
            
        st.dataframe(
            table_data,
            hide_index=True,
            use_container_width=True
        )

    # Analytical Methodology Note
    st.markdown(
        """
        <div style="background:#0B0E14; border:1px solid #1E293B; border-radius:6px; padding:12px; margin-top:16px; font-size:11px; color:#94A3B8;">
            <b>Methodology Note:</b> Bottleneck Pressure Score is calculated analytically from actual simulator parameters:
            <br><code>Score = (CT / Line Takt) × 40 + (Queue / Capacity) × 40 + (1.0 - Equipment Health) × 20 + State Penalties</code>
            <br><i>(This is an empirical trend-based projection. Future station-specific ML models can be seamlessly plugged into this data layer).</i>
        </div>
        """,
        unsafe_allow_html=True
    )
