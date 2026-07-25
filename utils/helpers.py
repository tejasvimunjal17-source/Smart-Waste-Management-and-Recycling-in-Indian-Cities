"""utils/helpers.py — shared UI/session helpers used across pages."""
import streamlit as st
from pathlib import Path
from datetime import datetime

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def load_css():
    css_path = ASSETS_DIR / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def init_session_state():
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
    """Call at the top of a protected page. Stops rendering if unauthorized."""
    init_session_state()
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
