"""
Smart Waste Management and Recycling in Indian Cities
Main Streamlit entry point.

At this stage of the build, this file only proves the skeleton wires
together correctly: config loads, the database initializes, logging works,
and a placeholder screen renders. The premium landing page, auth flow, and
feature pages are layered on top of this foundation in later steps.
"""

import streamlit as st

from config.constants import APP_NAME, APP_TAGLINE, COLORS, SDGS
from config.settings import settings
from database.db_manager import health_check, initialize_database
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def bootstrap() -> bool:
    """Run one-time startup tasks. Returns True if the app is healthy to serve."""
    try:
        initialize_database()
    except Exception:
        logger.exception("Failed to initialize database on startup.")
        st.error("⚠️ Could not initialize the database. Check logs/app.log for details.")
        return False
    return True


def render_status_panel() -> None:
    """Temporary skeleton-verification panel — will be replaced by the real landing page."""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {COLORS['emerald_green']}22, {COLORS['sky_blue']}22);
            border: 1px solid {COLORS['emerald_green']}55;
            border-radius: 16px;
            padding: 2rem;
            backdrop-filter: blur(10px);
        ">
            <h1 style="color:{COLORS['forest_green']}; margin-bottom:0;">🌿 {APP_NAME}</h1>
            <p style="color:{COLORS['dark_slate']}; font-size:1.1rem;">{APP_TAGLINE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("🧱 Skeleton Status")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Environment", settings.app_env)
    with col2:
        db_ok = health_check()
        st.metric("Database", "✅ Connected" if db_ok else "❌ Unreachable")
    with col3:
        st.metric("AI (OpenRouter)", "✅ Configured" if settings.ai_enabled else "⚠️ Not configured")

    if not settings.ai_enabled:
        st.info(
            "AI features are disabled until `OPENROUTER_API_KEY` is set in your `.env` file. "
            "Copy `.env.example` to `.env` and add your key to enable Prakriti AI Connect and "
            "all AI-powered features."
        )

    st.divider()
    st.subheader("🌍 Supporting UN Sustainable Development Goals")
    sdg_cols = st.columns(len(SDGS))
    for col, sdg in zip(sdg_cols, SDGS):
        with col:
            st.markdown(
                f"""
                <div style="background:{sdg['color']}22; border-left:4px solid {sdg['color']};
                            border-radius:8px; padding:1rem;">
                    <strong>{sdg['code']}</strong><br>{sdg['title']}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
    st.caption(
        "Next build steps: authentication → citizen report-waste flow → officer/admin "
        "dashboards → AI features → Prakriti AI Connect chatbot → premium landing page."
    )


def main() -> None:
    if not bootstrap():
        st.stop()

    logger.info("App loaded successfully. Environment: %s", settings.app_env)
    render_status_panel()


if __name__ == "__main__":
    main()
