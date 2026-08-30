"""
DIGITALTWIN.AI — Main Streamlit Application Entrypoint.
35-Station Manufacturing Digital Twin Control Center.
"""

import streamlit as st
import data.adapter as adapter
from config.styles import CUSTOM_CSS
from components.sidebar import render_sidebar
from views.overview import render_overview_page
from views.bottleneck import render_bottleneck_page
from views.quality import render_quality_page
from views.analytics import render_analytics_page

# Try importing streamlit-autorefresh if installed
try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

# Page Configuration
st.set_page_config(
    page_title="DIGITALTWIN.AI | 35-Station Assembly Control Center",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Dark Industrial Theme CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Session State Initialization
if "active_page" not in st.session_state:
    st.session_state["active_page"] = "overview"

if "selected_station" not in st.session_state:
    st.session_state["selected_station"] = None

if "drawer_open" not in st.session_state:
    st.session_state["drawer_open"] = False

if "speed_multiplier" not in st.session_state:
    st.session_state["speed_multiplier"] = "1×"

# Controlled Live Auto-Refresh (~1 Hz for smooth interaction)
sim_state = adapter.get_simulation_state()
if sim_state["status"] == "RUNNING":
    if HAS_AUTOREFRESH:
        st_autorefresh(interval=1000, key="dt_live_tick_autorefresh")

# Render Permanent Left Sidebar & Simulation Controls
render_sidebar()

# Page Router
curr_page = st.session_state.get("active_page", "overview")

if curr_page == "overview":
    render_overview_page()
elif curr_page == "bottleneck":
    render_bottleneck_page()
elif curr_page == "quality":
    render_quality_page()
elif curr_page == "analytics":
    render_analytics_page()
else:
    render_overview_page()
