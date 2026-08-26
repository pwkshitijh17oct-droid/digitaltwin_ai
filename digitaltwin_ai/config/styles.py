"""
Industrial Dark Control-Center CSS Design System for DigitalTwin.ai.
"""

CUSTOM_CSS = """
<style>
/* -------------------------------------------------------------
   GLOBAL INDUSTRIAL DARK THEME & RESET
   ------------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-main: #0B0E14;
    --bg-card: #121824;
    --bg-card-hover: #1A2234;
    --bg-card-active: #222C42;
    --border-subtle: #1E293B;
    --border-bright: #334155;
    --border-active: #38BDF8;
    
    --text-primary: #F8FAFC;
    --text-secondary: #94A3B8;
    --text-muted: #64748B;
    
    --status-normal: #10B981;
    --status-normal-bg: rgba(16, 185, 129, 0.12);
    --status-normal-border: rgba(16, 185, 129, 0.3);
    
    --status-warning: #F59E0B;
    --status-warning-bg: rgba(245, 158, 11, 0.15);
    --status-warning-border: rgba(245, 158, 11, 0.4);
    
    --status-critical: #EF4444;
    --status-critical-bg: rgba(239, 68, 68, 0.2);
    --status-critical-border: rgba(239, 68, 68, 0.5);
    
    --status-idle: #64748B;
    --status-idle-bg: rgba(100, 116, 139, 0.12);
    --status-idle-border: rgba(100, 116, 139, 0.3);
    
    --status-maint: #3B82F6;
    --status-maint-bg: rgba(59, 130, 246, 0.15);
    --status-maint-border: rgba(59, 130, 246, 0.4);
    
    --accent-cyan: #06B6D4;
    --accent-blue: #38BDF8;
    --accent-indigo: #6366F1;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: var(--text-primary);
}

.stApp {
    background-color: var(--bg-main);
}

/* Hide Default Streamlit Multipage Navigation */
[data-testid="stSidebarNav"], 
div[data-testid="stSidebarNav"], 
ul[data-testid="stSidebarNavItems"] {
    display: none !important;
}

/* =============================================================
   PERMANENT SIDEBAR & REMOVE ALL COLLAPSE / EXPAND BUTTONS
   ============================================================= */

/* Remove the expand and collapse buttons completely */
[data-testid="stSidebarCollapseButton"],
button[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
div[data-testid="stSidebarCollapsedControl"],
button[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* Lock sidebar permanently open */
section[data-testid="stSidebar"] {
    display: block !important;
    transform: none !important;
    margin-left: 0 !important;
    visibility: visible !important;
    background-color: #07090E !important;
    border-right: 1px solid var(--border-subtle);
    min-width: 320px !important;
    max-width: 340px !important;
    position: relative !important;
}

section[data-testid="stSidebar"] div.stButton > button {
    width: 100%;
    text-align: left;
    background: #111622;
    color: #CBD5E1;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 0.5rem 0.8rem;
    font-weight: 500;
    transition: all 0.15s ease;
}

section[data-testid="stSidebar"] div.stButton > button:hover {
    background: #1E293B;
    color: #38BDF8;
    border-color: #38BDF8;
}

/* Control Room Header */
.dt-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0 16px 0;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 16px;
}

.dt-logo-icon {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, #06B6D4, #38BDF8, #6366F1);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 16px;
    color: #FFFFFF;
    box-shadow: 0 0 12px rgba(6, 182, 212, 0.4);
}

.dt-brand-title {
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 0.05em;
    background: linear-gradient(90deg, #FFFFFF, #94A3B8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

.dt-brand-subtitle {
    font-size: 10px;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-family: 'JetBrains Mono', monospace;
}

/* Status Indicator Dot with Pulse */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
}

.status-pill.live {
    background: rgba(16, 185, 129, 0.15);
    color: #10B981;
    border: 1px solid rgba(16, 185, 129, 0.4);
}

.status-pill.paused {
    background: rgba(245, 158, 11, 0.15);
    color: #F59E0B;
    border: 1px solid rgba(245, 158, 11, 0.4);
}

.status-pill.stopped {
    background: rgba(100, 116, 139, 0.15);
    color: #94A3B8;
    border: 1px solid rgba(100, 116, 139, 0.4);
}

.pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}

.pulse-dot.green {
    background-color: #10B981;
    box-shadow: 0 0 8px #10B981;
    animation: pulse-green 1.8s infinite;
}

.pulse-dot.yellow {
    background-color: #F59E0B;
    box-shadow: 0 0 6px #F59E0B;
}

.pulse-dot.red {
    background-color: #EF4444;
    box-shadow: 0 0 8px #EF4444;
    animation: pulse-red 1.2s infinite;
}

.pulse-dot.grey {
    background-color: #64748B;
}

.pulse-dot.blue {
    background-color: #3B82F6;
    box-shadow: 0 0 6px #3B82F6;
}

@keyframes pulse-green {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

@keyframes pulse-red {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.8); }
    70% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

/* Industrial KPI Cards */
.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 14px 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    position: relative;
    overflow: hidden;
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 3px;
    height: 100%;
    background: var(--accent-blue);
}

.kpi-card.warning::before { background: var(--status-warning); }
.kpi-card.critical::before { background: var(--status-critical); }
.kpi-card.success::before { background: var(--status-normal); }

.kpi-label {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}

.kpi-value {
    font-size: 22px;
    font-weight: 700;
    color: var(--text-primary);
    font-family: 'JetBrains Mono', monospace;
    line-height: 1.2;
}

.kpi-subtext {
    font-size: 11px;
    color: var(--text-secondary);
    margin-top: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Global Alert Banner */
.alert-banner {
    background: linear-gradient(90deg, rgba(239, 68, 68, 0.15), rgba(245, 158, 11, 0.1));
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-left: 4px solid #EF4444;
    border-radius: 6px;
    padding: 10px 16px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 14px rgba(239, 68, 68, 0.15);
}

.alert-title {
    font-size: 13px;
    font-weight: 700;
    color: #FCA5A5;
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
}

.alert-desc {
    font-size: 12px;
    color: #E2E8F0;
    margin: 2px 0 0 0;
}

/* Assembly Line Shop Containers */
.shop-section {
    background: rgba(18, 24, 36, 0.6);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 12px;
}

.shop-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(30, 41, 59, 0.8);
}

.shop-title {
    font-size: 12px;
    font-weight: 700;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-family: 'JetBrains Mono', monospace;
}

.shop-badge {
    font-size: 10px;
    color: #64748B;
    background: #0B0E14;
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid #1E293B;
}

/* Station Nodes Flow Layout */
.stations-flow-grid {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
}

/* Streamlit Button override for Station Nodes */
div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
    background: #111622;
    border: 1px solid #1E293B;
    color: #E2E8F0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    padding: 4px 8px;
    border-radius: 6px;
    transition: all 0.15s ease;
    min-height: 38px;
}

div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
    border-color: #38BDF8;
    background: #1E293B;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.25);
    transform: translateY(-1px);
}

/* Selected Active Station */
.station-btn-active {
    border-color: #38BDF8 !important;
    background: rgba(56, 189, 248, 0.15) !important;
    box-shadow: 0 0 12px rgba(56, 189, 248, 0.4) !important;
}

/* Station Drawer / Panel */
.drawer-container {
    background: var(--bg-card);
    border: 1px solid var(--border-bright);
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
}

.drawer-header {
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 12px;
    margin-bottom: 14px;
}

.drawer-station-id {
    font-size: 20px;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    color: #38BDF8;
    margin: 0;
}

.drawer-station-name {
    font-size: 14px;
    font-weight: 600;
    color: #F1F5F9;
    margin: 2px 0 6px 0;
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    margin-bottom: 14px;
}

.metric-box {
    background: #0B0E14;
    border: 1px solid var(--border-subtle);
    border-radius: 6px;
    padding: 8px 10px;
}

.metric-box-label {
    font-size: 10px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.metric-box-val {
    font-size: 15px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-primary);
    margin-top: 2px;
}

.params-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
    margin-bottom: 14px;
}

.param-card {
    background: rgba(11, 14, 20, 0.8);
    border: 1px solid var(--border-subtle);
    border-radius: 6px;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.param-name {
    font-size: 10px;
    color: #94A3B8;
    margin-bottom: 2px;
}

.param-val {
    font-size: 13px;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    color: #F8FAFC;
}

.param-badge {
    align-self: flex-start;
    font-size: 9px;
    padding: 1px 5px;
    border-radius: 3px;
    margin-top: 4px;
    font-family: 'JetBrains Mono', monospace;
}

.param-badge.normal { background: rgba(16, 185, 129, 0.15); color: #10B981; }
.param-badge.warning { background: rgba(245, 158, 11, 0.2); color: #F59E0B; }
.param-badge.critical { background: rgba(239, 68, 68, 0.25); color: #EF4444; }

.risk-card {
    border-radius: 6px;
    padding: 10px 12px;
    margin-bottom: 10px;
    border: 1px solid var(--border-subtle);
}

.risk-card.high {
    background: rgba(239, 68, 68, 0.1);
    border-color: rgba(239, 68, 68, 0.3);
}

.risk-card.med {
    background: rgba(245, 158, 11, 0.1);
    border-color: rgba(245, 158, 11, 0.3);
}

.risk-card.low {
    background: rgba(16, 185, 129, 0.08);
    border-color: rgba(16, 185, 129, 0.2);
}

/* Quality Intelligence Checklist */
.adaptive-test-card {
    background: #0F172A;
    border: 1px solid #38BDF8;
    border-radius: 8px;
    padding: 14px;
    box-shadow: 0 0 16px rgba(56, 189, 248, 0.15);
}

.test-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 0;
    border-bottom: 1px solid rgba(30, 41, 59, 0.6);
    font-size: 12px;
    color: #E2E8F0;
}

.test-item:last-child {
    border-bottom: none;
}

/* Clean decorations */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
