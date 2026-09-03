"""utils/helpers.py — shared UI/session helpers used across pages."""
import streamlit as st
from pathlib import Path
from datetime import datetime

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def load_css(show_sidebar_toggle: bool = True):
    """
    The native Streamlit header/toolbar is always hidden, on every page,
    unconditionally — that part is not configurable (see
    frontend.custom_sidebar._hide_streamlit_header()).

    show_sidebar_toggle: whether THIS page shows the EcoVision 🌎 custom
    drawer toggle + sidebar. Defaults to True, which is the original,
    unchanged behavior — every existing page keeps calling load_css()
    with no arguments and is unaffected. Pass False only from the public
    landing page and the standalone Login/Register pages.
    """
    css_path = ASSETS_DIR / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

    # Collapsible left drawer sidebar (reused/rebranded from LearnMate AI —
    # see frontend/custom_sidebar.py). This only repositions/animates
    # Streamlit's own native, auto-generated page-nav sidebar via CSS; it
    # does not add, remove, or reorder any pages/routes.
    from frontend.custom_sidebar import render_custom_sidebar_controls
    render_custom_sidebar_controls(show_toggle=show_sidebar_toggle)


def init_session_state():
    # --- DB safety net ---------------------------------------------------
    # Streamlit multipage apps only execute app.py's top-level code when the
    # user lands on the Home page. If someone opens /Register or any other
    # page directly (a fresh tab, a bookmark, a shared link, Streamlit
    # Cloud's cold start, etc.), app.py's init_db() call never runs and the
    # "users" table won't exist yet -> sqlite3.OperationalError on
    # registration/login. Every page calls init_session_state() (directly
    # or via require_login()), so initializing the DB here — guarded by a
    # session-state flag so it only runs once per session — guarantees the
    # schema exists no matter which page is opened first.
    if not st.session_state.get("_db_initialized"):
        from database.db import init_db
        init_db()
        st.session_state["_db_initialized"] = True

    defaults = {
        "user": None,
        "theme": "dark",
        "chat_history": [],
        "chat_session_id": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
        "show_chat": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def require_login(allowed_roles=None):
    """Call at the top of a protected page. Stops rendering if unauthorized.

    Every protected page calls this BEFORE load_css() (so an unauthorized
    visitor never sees more of the page than the warning below). But
    load_css() is also what hides Streamlit's native header/toolbar and the
    full native page-list sidebar — and require_login() can st.stop() before
    load_css() ever runs. That left a real gap: a logged-out or wrong-role
    visitor hitting a protected page directly briefly saw Streamlit's raw
    native chrome, including the full auto-generated sidebar listing every
    page (Admin/Officer dashboards included), before anything was hidden.
    Hiding it here too — first thing, before any st.stop() — closes that
    gap. It's the same CSS load_css() applies later, so it's harmless/
    idempotent for the success path.
    """
    init_session_state()
    from frontend.custom_sidebar import _hide_streamlit_header, _hide_sidebar_no_toggle_css
    _hide_streamlit_header()
    _hide_sidebar_no_toggle_css()
    if not st.session_state.get("user"):
        st.warning("🔒 Please log in to access this page.")
        st.page_link("pages/1_🔐_Login.py", label="Go to Login", icon="🔐")
        st.stop()
    if allowed_roles and st.session_state["user"]["role"] not in allowed_roles:
        st.error("⛔ You don't have permission to view this page.")
        st.stop()


def logout():
    st.session_state["user"] = None
    st.session_state["chat_history"] = []


def status_badge(status: str) -> str:
    colors = {
        "Submitted": "#64748b", "Under Review": "#f59e0b", "Assigned": "#3b82f6",
        "In Progress": "#8b5cf6", "Resolved": "#10b981", "Rejected": "#ef4444",
    }
    color = colors.get(status, "#64748b")
    return f'<span style="background:{color}22;color:{color};padding:4px 12px;border-radius:20px;font-weight:600;font-size:0.85em;border:1px solid {color}55;">{status}</span>'


def priority_badge(priority: str) -> str:
    colors = {"Low": "#10b981", "Medium": "#f59e0b", "High": "#ef4444"}
    color = colors.get(priority, "#64748b")
    return f'<span style="background:{color}22;color:{color};padding:4px 12px;border-radius:20px;font-weight:600;font-size:0.85em;border:1px solid {color}55;">{priority}</span>'


def toast(message: str, icon: str = "✅"):
    st.toast(message, icon=icon)


def format_datetime(dt_str):
    if not dt_str:
        return "-"
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return dt_str
