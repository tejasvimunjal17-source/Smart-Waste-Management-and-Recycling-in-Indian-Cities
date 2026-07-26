import streamlit as st
import difflib
from urllib.parse import quote
from utils.ai_client import generate_resume_content, chat_completion
from utils.helpers import load_css, init_session_state
from config import settings

# The certification directory normally lives in assets/data/certifications.py.
# On some deployments that file/folder can go missing (e.g. GitHub's web
# upload UI silently skips empty files, and empty directories aren't tracked
# by git at all) which previously crashed this whole page with
# `ModuleNotFoundError: No module named 'assets.data'`. We now fail
# gracefully to a small built-in fallback dataset instead, so the page
# always renders — see README/DEPLOYMENT notes for the file to re-add.
try:
    from assets.data.certifications import CERTIFICATIONS
except ModuleNotFoundError:
    st.warning(
        "⚠️ Couldn't load the full certification directory (assets/data/certifications.py "
        "is missing from this deployment) — showing a smaller built-in list instead. "
        "Re-add that file to your repo to restore the full directory."
    )
    CERTIFICATIONS = [
        {"title": "AI Fundamentals", "provider": "IBM SkillsBuild", "skill": "Artificial Intelligence",
         "level": "Beginner", "duration": "4-6 hrs", "language": "English", "certificate": True,
         "url": "https://skillsbuild.org/"},
        {"title": "Google Cloud Digital Leader", "provider": "Google Cloud Skills Boost", "skill": "Cloud Computing",
         "level": "Beginner", "duration": "10 hrs", "language": "English", "certificate": True,
         "url": "https://www.cloudskillsboost.google/"},
        {"title": "AWS Cloud Practitioner Essentials", "provider": "AWS Skill Builder", "skill": "Cloud Computing",
         "level": "Beginner", "duration": "6 hrs", "language": "English", "certificate": True,
         "url": "https://skillbuilder.aws/"},
        {"title": "Environmental Science & Sustainability", "provider": "NPTEL", "skill": "Sustainability",
         "level": "Intermediate", "duration": "12 weeks", "language": "English", "certificate": True,
         "url": "https://nptel.ac.in/"},
        {"title": "Responsive Web Design", "provider": "FreeCodeCamp", "skill": "Web Development",
         "level": "Beginner", "duration": "300 hrs (self-paced)", "language": "English", "certificate": True,
         "url": "https://www.freecodecamp.org/"},
    ]

st.set_page_config(page_title="Certifications & Green Jobs | EcoVision AI", page_icon="🎓", layout="wide")
init_session_state()
load_css()

st.markdown('<div class="eco-hero"><h1>🎓 Free Certifications & 🌱 Green Job Search</h1>'
            '<p>Build sustainability skills and find green careers.</p></div>', unsafe_allow_html=True)

st.info(
    "ℹ️ Certification listings are a curated directory linking to official provider pages "
    "(catalogs change constantly, so we link out rather than scrape). Job search below builds "
    "live search links to major job boards using your filters — we don't scrape those sites directly."
)

tab_certs, tab_jobs, tab_resume = st.tabs(["🎓 Certification Finder", "🌱 Green Job Search", "📄 AI Resume Generator"])

# ---------------- CERTIFICATION FINDER ----------------
with tab_certs:
    query = st.text_input("Search certifications (skill, provider, or keyword)", key="cert_q")
    c1, c2, c3 = st.columns(3)
    with c1:
        level_f = st.selectbox("Level", ["All", "Beginner", "Intermediate", "Advanced"])
    with c2:
        cert_f = st.selectbox("Certificate required?", ["All", "Yes", "No"])
    with c3:
        sort_by = st.selectbox("Sort by", ["Relevance", "Title A-Z", "Provider A-Z"])

    results = CERTIFICATIONS
    if query:
        # Fuzzy + substring matching so we never show zero results abruptly
        def score(item):
            text = f"{item['title']} {item['provider']} {item['skill']}".lower()
            if query.lower() in text:
                return 1.0
            return difflib.SequenceMatcher(None, query.lower(), text).ratio()
        results = sorted(CERTIFICATIONS, key=score, reverse=True)
        results = [r for r in results if score(r) > 0.25] or CERTIFICATIONS[:5]

    if level_f != "All":
        results = [r for r in results if r["level"] == level_f] or results
    if cert_f != "All":
        want = cert_f == "Yes"
        filtered = [r for r in results if r["certificate"] == want]
        results = filtered or results

    if sort_by == "Title A-Z":
        results = sorted(results, key=lambda r: r["title"])
    elif sort_by == "Provider A-Z":
        results = sorted(results, key=lambda r: r["provider"])

    st.caption(f"Showing {len(results)} result(s)" + (" (closest matches shown)" if query else ""))
    for r in results:
        st.markdown(
            f"""<div class="eco-card">
                <b>{r['title']}</b> — <span style="color:#38bdf8;">{r['provider']}</span><br>
                🏷️ {r['skill']} · 📈 {r['level']} · ⏱️ {r['duration']} · 🌐 {r['language']} ·
                {'🎓 Certificate' if r['certificate'] else '📘 No certificate'}<br>
                <a href="{r['url']}" target="_blank" style="color:#34d399;">Visit provider →</a>
            </div>""",
            unsafe_allow_html=True,
        )

# ---------------- GREEN JOB SEARCH ----------------
with tab_jobs:
    jc1, jc2, jc3 = st.columns(3)
    with jc1:
        role_q = st.text_input("Role / Keyword", placeholder="e.g. Sustainability Analyst")
    with jc2:
        city_q = st.text_input("City", placeholder="e.g. Gurugram")
    with jc3:
        remote_f = st.selectbox("Work Mode", ["Any", "Remote", "Hybrid", "On-site"])

    if st.button("🔍 Search Green Jobs", type="primary"):
        q = quote(f"{role_q} sustainability green jobs".strip())
        loc = quote(city_q or "India")
        boards = [
            ("LinkedIn", f"https://www.linkedin.com/jobs/search/?keywords={q}&location={loc}"),
            ("Naukri", f"https://www.naukri.com/{quote((role_q or 'sustainability') + '-jobs')}-in-{quote(city_q or 'india')}"),
            ("Indeed", f"https://in.indeed.com/jobs?q={q}&l={loc}"),
            ("Internshala", f"https://internshala.com/internships/keywords-{quote(role_q or 'sustainability')}"),
            ("Foundit (Monster)", f"https://www.foundit.in/srp/results?query={q}&locations={loc}"),
            ("UN Careers", "https://careers.un.org/"),
        ]
        st.success("Here are live search links tailored to your filters — never zero results, since these open direct search queries on each board:")
        for name, url in boards:
            st.markdown(f'<div class="eco-card"><b>{name}</b><br><a href="{url}" target="_blank" style="color:#34d399;">Open search on {name} →</a></div>', unsafe_allow_html=True)

        with st.spinner("Getting AI learning-path recommendation..."):
            tip = chat_completion(
                [{"role": "system", "content": "You are a green-careers advisor for the Indian job market."},
                 {"role": "user", "content": f"Suggest a short learning path and 3 in-demand skills for someone targeting a '{role_q or 'sustainability'}' role in India's green economy."}],
                temperature=0.5, max_tokens=300,
            )
        st.markdown(f'<div class="eco-card">🎯 <b>AI Career Tip</b><br>{tip}</div>', unsafe_allow_html=True)

# ---------------- RESUME GENERATOR ----------------
with tab_resume:
    kind = st.selectbox("Generate", ["resume", "cover_letter", "portfolio", "linkedin"],
                         format_func=lambda k: {"resume": "Resume", "cover_letter": "Cover Letter",
                                                 "portfolio": "Portfolio Summary", "linkedin": "LinkedIn Summary"}[k])
    profile = st.text_area("Paste your details (education, experience, skills, target role)", height=200,
                            placeholder="e.g. B.Tech Environmental Engineering, 2 internships in waste management, skilled in GIS and data analysis, targeting a Sustainability Analyst role...")
    if st.button("✨ Generate", type="primary", key="resume_gen"):
        if not profile.strip():
            st.warning("Please add some profile details first.")
        else:
            with st.spinner("Writing..."):
                content = generate_resume_content(kind, profile)
            st.markdown(content)
            st.download_button("Download as text", content.encode(), f"{kind}.md")
