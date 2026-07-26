"""
utils/certification_search.py
--------------------------------
Module 1: Certification Finder — fully independent live-search module.

This module has NO dependency on any local certification dataset. It
combines two kinds of sources on every search:

1. LIVE OFFICIAL API — Coursera's public Courses catalog API
   (api.coursera.org), which is unauthenticated and official. Returns
   real course titles, descriptions, and links.

2. OFFICIAL SEARCH ENDPOINTS — for providers that don't expose a public
   search API (IBM SkillsBuild, Microsoft Learn, Google Cloud Skills
   Boost, AWS Skill Builder, Cisco Skills For All, Oracle University,
   NPTEL, SWAYAM, edX, FutureLearn, LinkedIn Learning, Kaggle Learn,
   Hugging Face, FreeCodeCamp, GitHub Skills), we build a direct link to
   *that provider's own* documented search/catalog URL with the query
   pre-filled. This is navigation, not scraping — no third-party content
   is copied or displayed as if it were ours.

Design goals mirrored here:
  - Independent of Module 2 (job search) — no shared state/functions.
  - Cached (st.cache_data) + rate-limited so repeated identical searches
    don't hammer the upstream API.
  - Every network call is wrapped in try/except with a timeout — a failed
    or slow provider degrades silently instead of crashing the page.
  - Never returns an empty page: official search-endpoint cards render
    with zero network dependency, and an AI-generated "similar
    certifications" recommendation kicks in whenever live results are thin.
"""
import time
import logging
import difflib
import requests
import streamlit as st
from urllib.parse import quote

from utils.ai_client import chat_completion

logger = logging.getLogger("ecovision.certsearch")

REQUEST_TIMEOUT = 8
CACHE_TTL_SECONDS = 600
MIN_SECONDS_BETWEEN_LIVE_CALLS = 3

# ---------------------------------------------------------------------
# Providers without a public search API: link straight to their own
# official search/catalog page using each site's documented URL pattern.
# {q} is replaced with the URL-encoded search query.
# ---------------------------------------------------------------------
OFFICIAL_SEARCH_PROVIDERS = [
    {"name": "IBM SkillsBuild", "url_tpl": "https://skillsbuild.org/catalog-search?q={q}",
     "skills": ["ai", "cloud", "data", "cybersecurity", "sustainability"]},
    {"name": "Microsoft Learn", "url_tpl": "https://learn.microsoft.com/en-us/search/?terms={q}",
     "skills": ["azure", "cloud", "data", "ai", "power platform"]},
    {"name": "Google Cloud Skills Boost", "url_tpl": "https://www.cloudskillsboost.google/catalog?keywords={q}",
     "skills": ["cloud", "gcp", "data", "ai", "kubernetes"]},
    {"name": "Cisco Skills For All", "url_tpl": "https://skillsforall.com/search?q={q}",
     "skills": ["networking", "cybersecurity", "iot"]},
    {"name": "Oracle University", "url_tpl": "https://mylearn.oracle.com/ou/search?q={q}",
     "skills": ["cloud", "database", "java"]},
    {"name": "AWS Skill Builder", "url_tpl": "https://skillbuilder.aws/search?searchText={q}",
     "skills": ["cloud", "aws", "ai", "data"]},
    {"name": "NPTEL", "url_tpl": "https://nptel.ac.in/courses?search={q}",
     "skills": ["engineering", "sustainability", "environment", "science"]},
    {"name": "SWAYAM", "url_tpl": "https://swayam.gov.in/explorer?searchText={q}",
     "skills": ["sustainability", "environment", "management", "humanities"]},
    {"name": "edX", "url_tpl": "https://www.edx.org/search?q={q}",
     "skills": ["climate", "data", "business", "computer science"]},
    {"name": "FutureLearn", "url_tpl": "https://www.futurelearn.com/search?q={q}",
     "skills": ["sustainability", "health", "business"]},
    {"name": "LinkedIn Learning", "url_tpl": "https://www.linkedin.com/learning/search?keywords={q}",
     "skills": ["business", "leadership", "sustainability", "software"]},
    {"name": "Kaggle Learn", "url_tpl": "https://www.kaggle.com/search?q={q}",
     "skills": ["machine learning", "data", "python"]},
    {"name": "Hugging Face Courses", "url_tpl": "https://huggingface.co/learn",
     "skills": ["nlp", "machine learning", "ai"]},
    {"name": "FreeCodeCamp", "url_tpl": "https://www.freecodecamp.org/news/search/?query={q}",
     "skills": ["web development", "programming", "python", "javascript"]},
    {"name": "GitHub Skills", "url_tpl": "https://github.com/skills",
     "skills": ["git", "programming", "open source"]},
]


def _rate_limit_ok(key: str) -> bool:
    last = st.session_state.get(f"_cert_rl_{key}", 0)
    now = time.time()
    if now - last < MIN_SECONDS_BETWEEN_LIVE_CALLS:
        return False
    st.session_state[f"_cert_rl_{key}"] = now
    return True


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def _fetch_coursera(query: str, limit: int = 12):
    """
    Official, unauthenticated Coursera Courses catalog API.
    https://api.coursera.org/api/courses.v1
    Returns [] on any failure — never raises — so the caller can keep going.
    """
    try:
        resp = requests.get(
            "https://api.coursera.org/api/courses.v1",
            params={
                "q": "search",
                "query": query,
                "limit": limit,
                "fields": "name,description,photoUrl,slug,workload",
            },
            headers={"User-Agent": "EcoVisionAI/1.0 (+https://ecovision-ai.streamlit.app)"},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        logger.warning("Coursera API unavailable: %s", e)
        return []
    except (ValueError, KeyError) as e:
        logger.warning("Coursera API returned unexpected data: %s", e)
        return []

    results = []
    for c in data.get("elements", []):
        slug = c.get("slug")
        results.append({
            "title": c.get("name") or "Untitled Course",
            "provider": "Coursera",
            "description": (c.get("description") or "No description provided.")[:260],
            "level": "-",
            "duration": c.get("workload") or "-",
            "language": "-",
            "certificate": True,
            "free": None,  # audit-free availability varies per course; not exposed by this endpoint
            "url": f"https://www.coursera.org/learn/{slug}" if slug else "https://www.coursera.org/",
            "logo": c.get("photoUrl") or "",
            "last_updated": None,
            "source": "Coursera Official API",
        })
    return results


def _official_search_cards(query: str):
    """Zero-network fallback: direct links to each provider's own official search page."""
    q_lower = query.lower()
    scored = []
    for p in OFFICIAL_SEARCH_PROVIDERS:
        relevance = 1 if any(s in q_lower or q_lower in s for s in p["skills"]) else 0
        scored.append((relevance, p))
    scored.sort(key=lambda t: t[0], reverse=True)

    cards = []
    for relevance, p in scored:
        url = p["url_tpl"].format(q=quote(query or "sustainability"))
        cards.append({
            "title": f"Search '{query or 'certifications'}' on {p['name']}",
            "provider": p["name"],
            "description": "Official provider search page — live catalog results open directly on their site.",
            "level": "-", "duration": "-", "language": "-", "certificate": None, "free": None,
            "url": url, "logo": "", "last_updated": None,
            "source": "Official Search Endpoint",
            "_relevance": relevance,
        })
    return cards


def _apply_filters(results, level, duration_kw, language, certificate, free):
    def keep(r):
        if level != "Any" and r.get("level") not in ("-", level):
            return False
        if duration_kw and duration_kw.lower() not in str(r.get("duration", "")).lower():
            return False
        if language != "Any" and r.get("language") not in ("-", language):
            return False
        if certificate == "Yes" and r.get("certificate") is False:
            return False
        if certificate == "No" and r.get("certificate") is True:
            return False
        if free == "Free" and r.get("free") is False:
            return False
        if free == "Paid" and r.get("free") is True:
            return False
        return True
    return [r for r in results if keep(r)]


def _rank(results, query):
    def score(r):
        text = f"{r['title']} {r.get('description','')} {r['provider']}".lower()
        if query.lower() in text:
            return 1.0
        return difflib.SequenceMatcher(None, query.lower(), text).ratio()
    return sorted(results, key=score, reverse=True)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def _ai_recommend_similar(query: str):
    """AI-generated 'similar certifications' suggestion when live results are thin — no static dataset used."""
    prompt = (
        f"A learner searched for a free certification on '{query}' but we found few or no direct catalog "
        "matches. Suggest 4-5 well-known, genuinely free (or free-to-audit) certifications/courses close to "
        "this topic, each with the provider name, in one short bullet line each. Keep it factual and concise."
    )
    return chat_completion(
        [{"role": "system", "content": "You are a career/learning advisor recommending real, well-known free certification providers."},
         {"role": "user", "content": prompt}],
        temperature=0.4, max_tokens=350,
    )


def search_certifications(query: str, level="Any", duration_kw="", language="Any",
                           certificate="Any", free="Any"):
    """
    Main entry point for Module 1. Always returns a non-empty payload:
      {
        "live_results": [...],      # from Coursera official API (may be empty)
        "search_links": [...],      # official provider search-endpoint cards (never empty)
        "recommendation": str|None, # AI fallback text if live_results is thin
        "provider_status": {"Coursera": "ok"|"unavailable"|"rate_limited"},
      }
    """
    provider_status = {}
    live_results = []

    if query.strip():
        if _rate_limit_ok("coursera"):
            live_results = _fetch_coursera(query.strip())
            provider_status["Coursera"] = "ok" if live_results else "no_results_or_unavailable"
        else:
            provider_status["Coursera"] = "rate_limited (try again in a few seconds)"

    filtered_live = _apply_filters(live_results, level, duration_kw, language, certificate, free)
    ranked_live = _rank(filtered_live, query) if query.strip() else live_results

    search_links = _official_search_cards(query.strip())

    recommendation = None
    if query.strip() and len(ranked_live) < 3:
        try:
            recommendation = _ai_recommend_similar(query.strip())
        except Exception as e:
            logger.warning("AI recommendation fallback failed: %s", e)
            recommendation = None

    return {
        "live_results": ranked_live,
        "search_links": search_links,
        "recommendation": recommendation,
        "provider_status": provider_status,
    }
