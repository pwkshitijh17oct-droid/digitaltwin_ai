"""
Page 2 — Bottleneck Intelligence.
Shows where bottlenecks are occurring and where they are predicted to occur.
"""

import streamlit as st
from data.data_adapter import get_bottleneck_predictions, get_analytics_data
from components.charts import (
    create_cycle_time_trend_chart, 
    create_queue_growth_chart, 
    create_bottleneck_ranking_bar
)

def render_bottleneck_page():
    """Render Bottleneck Intelligence dashboard."""
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <h2 style="font-size: 20px; font-weight: 800; color: #F8FAFC; margin: 0; letter-spacing: 0.02em;">
            ⚠ Bottleneck Intelligence
        </h2>
        <div style="font-size: 12px; color: #94A3B8; margin-top: 2px;">
            Real-time constraint detection & predictive cycle-time degradation modeling
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    b_data = get_bottleneck_predictions()
    curr_b = b_data["current_bottleneck"]
    pred_b = b_data["predicted_bottleneck"]
    
    # Top 2 Sections: Current Bottleneck & Predicted Bottleneck
    col_curr, col_pred = st.columns(2)
    
    with col_curr:
        status_color = "#EF4444" if curr_b["status"] == "CRITICAL" else "#F59E0B"
        st.markdown(f"""
        <div class="kpi-card critical" style="min-height: 190px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <div class="kpi-label" style="color: #F87171;">CURRENT BOTTLENECK</div>
                <span class="status-pill critical" style="background: rgba(239, 68, 68, 0.2); color: #EF4444; border-color: rgba(239, 68, 68, 0.4);">
                    {curr_b['risk_level']} ({curr_b['risk_score']}%)
                </span>
            </div>
            <div style="font-size: 18px; font-weight: 800; color: #FFFFFF; font-family: 'JetBrains Mono', monospace;">
                {curr_b['id']} — {curr_b['name']}
            </div>
            
            <div class="metric-grid" style="margin-top: 12px; margin-bottom: 0;">
                <div class="metric-box">
                    <div class="metric-box-label">Cycle Time</div>
                    <div class="metric-box-val" style="color: #EF4444;">{curr_b['cycle_time']} <span style="font-size: 10px; color: #64748B;">min (+{curr_b['cycle_time_dev']}%)</span></div>
                </div>
                <div class="metric-box">
                    <div class="metric-box-label">Queue Accumulation</div>
                    <div class="metric-box-val">{curr_b['queue_length']} <span style="font-size: 10px; color: #64748B;">units</span></div>
                </div>
                <div class="metric-box">
                    <div class="metric-box-label">Station Utilization</div>
                    <div class="metric-box-val">{curr_b['utilization']}%</div>
                </div>
                <div class="metric-box">
                    <div class="metric-box-label">Impact</div>
                    <div class="metric-box-val" style="color: #F59E0B; font-size: 12px;">LINE PACING REDUCED</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_pred:
        st.markdown(f"""
        <div class="kpi-card warning" style="min-height: 190px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <div class="kpi-label" style="color: #FBBF24;">PREDICTED FUTURE BOTTLENECK</div>
                <span class="status-pill paused" style="background: rgba(245, 158, 11, 0.2); color: #F59E0B; border-color: rgba(245, 158, 11, 0.4);">
                    {pred_b['risk_level']} ({pred_b['risk_score']}%)
                </span>
            </div>
            <div style="font-size: 18px; font-weight: 800; color: #FFFFFF; font-family: 'JetBrains Mono', monospace;">
                {pred_b['id']} — {pred_b['name']}
            </div>
            
            <div class="metric-grid" style="margin-top: 12px; margin-bottom: 0;">
                <div class="metric-box">
                    <div class="metric-box-label">Time to Critical</div>
                    <div class="metric-box-val" style="color: #F59E0B;">{pred_b['predicted_time']}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-box-label">Forecast Cycle Time</div>
                    <div class="metric-box-val">{pred_b['cycle_time']} <span style="font-size: 10px; color: #64748B;">min</span></div>
                </div>
                <div class="metric-box">
                    <div class="metric-box-label">Buffer Queue</div>
                    <div class="metric-box-val">{pred_b['queue_length']} <span style="font-size: 10px; color: #64748B;">units</span></div>
                </div>
                <div class="metric-box">
                    <div class="metric-box-label">Proactive Action</div>
                    <div class="metric-box-val" style="color: #38BDF8; font-size: 12px;">PRE-VENT OVEN ZONE 2</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Third & Fourth Sections: Cycle Time Trend and Queue Growth
    analytics_data = get_analytics_data()
    ts = analytics_data["timestamps"]
    s25_cts = analytics_data["cycle_times"]["S25"]
    s18_cts = analytics_data["cycle_times"]["S18"]
    s5_cts = analytics_data["cycle_times"]["S5"]
    s25_qs = analytics_data["queues"]["S25"]
    s18_qs = analytics_data["queues"]["S18"]
    
    col_ct, col_q = st.columns(2)
    with col_ct:
        fig_ct = create_cycle_time_trend_chart(ts, s25_cts, s18_cts, s5_cts)
        st.plotly_chart(fig_ct, use_container_width=True, config={"displayModeBar": False})
        
    with col_q:
        fig_q = create_queue_growth_chart(ts, s25_qs, s18_qs)
        st.plotly_chart(fig_q, use_container_width=True, config={"displayModeBar": False})

    # Fifth Section: Bottleneck Ranking
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 13px; font-weight: 700; color: #F8FAFC; text-transform: uppercase; letter-spacing: 0.08em; font-family: monospace;'>Station Bottleneck Risk Ranking</p>", unsafe_allow_html=True)
    
    col_rank_chart, col_rank_table = st.columns([1, 1])
    
    with col_rank_chart:
        fig_bar = create_bottleneck_ranking_bar(b_data["rankings"])
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
        
    with col_rank_table:
        for r in b_data["rankings"]:
            r_color = "#EF4444" if r["risk_level"] == "CRITICAL" else ("#F59E0B" if r["risk_level"] == "WARNING" else "#10B981")
            st.markdown(f"""
            <div style="background: #121824; border: 1px solid #1E293B; border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 12px; font-weight: 800; font-family: monospace; color: #64748B;">#{r['rank']}</span>
                    <div>
                        <div style="font-size: 13px; font-weight: 700; color: #F8FAFC; font-family: monospace;">{r['id']} — {r['name']}</div>
                        <div style="font-size: 10px; color: #64748B;">Shop: {r['shop']} | CT: {r['cycle_time']}m | Queue: {r['queue_length']}</div>
                    </div>
                </div>
                <span style="background: {r_color}22; color: {r_color}; border: 1px solid {r_color}66; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; font-family: monospace;">
                    {r['risk_score']}% ({r['risk_level']})
                </span>
            </div>
            """, unsafe_allow_html=True)
