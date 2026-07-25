"""
config/settings.py
--------------------
Loads all environment variables in one place so the rest of the app
never touches os.environ directly. Fails loudly (with a friendly
Streamlit error) if required secrets are missing, instead of crashing
deep inside a request.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# ---- OpenRouter ----
OPENROUTER_API_KEY = _get("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = _get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = _get("OPENROUTER_MODEL", "meta-llama/llama-3.2-11b-vision-instruct:free")
OPENROUTER_TEXT_MODEL = _get("OPENROUTER_TEXT_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
OPENROUTER_SITE_URL = _get("OPENROUTER_SITE_URL", "https://ecovision-ai.streamlit.app")
OPENROUTER_APP_NAME = _get("OPENROUTER_APP_NAME", "EcoVision AI")

# ---- Security ----
APP_SECRET_KEY = _get("APP_SECRET_KEY", "dev-secret-change-me")
SESSION_TIMEOUT_MINUTES = int(_get("SESSION_TIMEOUT_MINUTES", "60") or 60)

# ---- Database ----
DATABASE_PATH = str(BASE_DIR / _get("DATABASE_PATH", "database/ecovision.db"))

# ---- Branding ----
MUNICIPALITY_NAME = _get("MUNICIPALITY_NAME", "Municipal Corporation of Gurugram (MCG)")
SUPPORT_EMAIL = _get("SUPPORT_EMAIL", "support@ecovision-ai.example.in")
SUPPORT_PHONE = _get("SUPPORT_PHONE", "+91-9999999999")

APP_NAME = "EcoVision AI"
APP_TAGLINE = "AI-powered Smart City Platform for Sustainable Waste Management"

WASTE_CATEGORIES = [
    "Plastic", "Organic", "Paper", "Glass", "Metal",
    "Mixed", "E-Waste", "Biomedical", "Construction",
]

PRIORITY_LEVELS = ["Low", "Medium", "High"]

COMPLAINT_STATUSES = ["Submitted", "Under Review", "Assigned", "In Progress", "Resolved", "Rejected"]

REWARD_POINTS = {
    "complaint_submitted": 10,
    "complaint_resolved_bonus": 20,
    "correct_segregation": 15,
    "referral": 25,
}


def is_ai_configured() -> bool:
    """True once a real (non-placeholder) OpenRouter key is present."""
    return bool(OPENROUTER_API_KEY) and "your_openrouter_api_key_here" not in OPENROUTER_API_KEY
