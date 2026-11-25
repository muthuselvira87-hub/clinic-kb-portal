import streamlit as st
from backend.config import CLINIC_NAME, CLINIC_PHONE, CLINIC_EMERGENCY_NUMBER, CLINIC_TIMINGS, CLINIC_LOCATION
from frontend.api_client import ClinicAPIClient
from frontend.pages_ui.chat_ui import render_chat_page
from frontend.pages_ui.kb_browse_ui import render_kb_browse_page
from frontend.pages_ui.admin_ui import render_admin_page
from frontend.pages_ui.analytics_ui import render_analytics_page

# Page configuration
st.set_page_config(
    page_title=f"{CLINIC_NAME} - Knowledge Base & Helpdesk",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Healthcare Styling
st.markdown("""
<style>
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0284c7;
    }
    /* Chat message styling */
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 8px;
    }
    /* Sidebar header */
    .sidebar-clinic-header {
        text-align: center;
        padding-bottom: 12px;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize API Client
client = ClinicAPIClient()

# Sidebar Navigation & System Status
with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-clinic-header">
            <h2>🏥 {CLINIC_NAME}</h2>
            <p style='color: #64748b; font-size: 13px;'>Patient Helpdesk & Knowledge Portal</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    nav_selection = st.radio(
        "Navigation",
        [
            "🩺 Patient Helpdesk Chat",
            "📚 Knowledge Base & Search",
            "🛠️ Admin Portal",
            "📊 Analytics & Insights"
        ],
        index=0
    )

    st.divider()

    # Clinic Quick Reference Info
    st.markdown("##### ℹ️ Clinic Information")
    st.markdown(f"📍 **Location**: {CLINIC_LOCATION}")
    st.markdown(f"🕒 **Hours**: {CLINIC_TIMINGS}")
    st.markdown(f"📞 **Helpdesk**: `{CLINIC_PHONE}`")
    st.markdown(f"🚨 **Emergency**: `{CLINIC_EMERGENCY_NUMBER}` (24/7)")

    st.divider()

    # System Status Indicator
    is_online = client.check_health()
    if is_online:
        st.success("🟢 API Backend: Connected")
    else:
        st.error("🔴 API Backend: Offline (Run FastAPI on port 8000)")


# Page Router
if nav_selection == "🩺 Patient Helpdesk Chat":
    render_chat_page(client)
elif nav_selection == "📚 Knowledge Base & Search":
    render_kb_browse_page(client)
elif nav_selection == "🛠️ Admin Portal":
    render_admin_page(client)
elif nav_selection == "📊 Analytics & Insights":
    render_analytics_page(client)
