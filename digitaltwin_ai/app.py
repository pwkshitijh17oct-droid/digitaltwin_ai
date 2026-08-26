"""
DigitalTwin.ai — Main Streamlit Application Entrypoint.
Industrial Manufacturing Digital Twin Control Center.
"""

import streamlit as st
import time
from config.styles import CUSTOM_CSS
from components.sidebar import render_sidebar
from data.data_adapter import get_simulation_state, step_simulation
from views.overview import render_overview_page
from views.bottleneck import render_bottleneck_page
from views.quality import render_quality_page
from views.analytics import render_analytics_page

# Try importing streamlit-autorefresh if installed, else fallback to session state tick
try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

# Page Configuration - Force Initial Sidebar State Expanded
st.set_page_config(
    page_title="DigitalTwin.ai | Manufacturing Control Center",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Dark Industrial Theme CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Session State Initialization
if "current_page" not in st.session_state:
    st.session_state.current_page = "Overview"

if "selected_station_id" not in st.session_state:
    st.session_state.selected_station_id = None

if "selected_vehicle_id" not in st.session_state:
    st.session_state.selected_vehicle_id = "V128"

if "sim_running" not in st.session_state:
    st.session_state.sim_running = True

# Simulation Live Tick Handling
sim_state = get_simulation_state()
if sim_state["running"]:
    # Auto-refresh every 2000ms / speed
    interval_ms = max(500, int(2000 / sim_state["speed"]))
    if HAS_AUTOREFRESH:
        st_autorefresh(interval=interval_ms, key="sim_autorefresh_counter")
    step_simulation()

# Render Global Sidebar
render_sidebar()

# Page Router
curr_page = st.session_state.get("current_page", "Overview")

if curr_page == "Overview":
    render_overview_page()
elif curr_page == "Bottleneck Intelligence":
    render_bottleneck_page()
elif curr_page == "Quality Intelligence":
    render_quality_page()
elif curr_page == "Analytics":
    render_analytics_page()
else:
    render_overview_page()
