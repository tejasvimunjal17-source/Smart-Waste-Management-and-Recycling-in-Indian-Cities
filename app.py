"""
app.py
--------
EcoVision AI — Smart Waste Management & Recycling in Indian Cities
Main entry point: premium landing page (logged out) / role-based
redirect hint (logged in). Streamlit auto-builds sidebar navigation
from the numbered files inside pages/.
"""
import streamlit as st
from utils.helpers import load_css, init_session_state
from config import settings

# session_state already carries over from the previous rerun (if any), so
# we can read it BEFORE set_page_config() and pass Streamlit's own
# initial_sidebar_state accordingly. This matters: initial_sidebar_state is
# applied by Streamlit natively as part of the page's own initial render,
# not via a CSS block injected mid-script — so for the common case (a
# logged-out visitor hitting Home) it prevents the native sidebar from ever
# flashing "expanded" before load_css()'s CSS arrives. It is a defensive
# second layer, not a replacement for that CSS (which still runs below).
is_public_landing = not st.session_state.get("user")

st.set_page_config(
    page_title="EcoVision AI | Smart Waste Management",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed" if is_public_landing else "expanded",
)

init_session_state()  # guarded internally so init_db() only runs once per session

# Public landing page = visitor is not logged in yet. Authenticated users
# viewing this same app.py (Home) keep the exact original header/nav/hero
# behavior below; only the logged-out view is simplified.
is_public_landing = not st.session_state.get("user")

load_css(show_sidebar_toggle=not is_public_landing)

# ---------------------------------------------------------------
# Top nav bar (approximated with columns — Streamlit has no fixed
# navbar, so we keep it compact and always at the top of the page)
# ---------------------------------------------------------------
if is_public_landing:
    st.markdown('<div class="eco-brand-center">🌿 EcoVision AI</div>', unsafe_allow_html=True)
else:
    nav_l, nav_r = st.columns([3, 2])
    with nav_l:
        st.markdown("### 🌿 EcoVision AI")
    with nav_r:
        u = st.session_state["user"]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**👋 {u['full_name'].split()[0]}** &nbsp;·&nbsp; `{u['role'].title()}`")
        with c2:
            if st.button("Logout", use_container_width=True):
                from utils.helpers import logout
                logout()
                st.rerun()

    st.divider()

# ---------------------------------------------------------------
# HERO
# ---------------------------------------------------------------
st.markdown(
    """
    <div class="eco-hero">
        <div class="eco-float" style="font-size:3rem;">🌍♻️🌱</div>
        <h1>Smart Waste Management & Recycling in Indian Cities</h1>
        <p>An AI-powered Smart City platform that empowers citizens and municipal corporations
        to report waste, improve recycling, monitor cleanliness, and build sustainable
        communities using Artificial Intelligence.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if is_public_landing:
    gs_l, gs_c, gs_r = st.columns([1, 1, 1])
    with gs_c:
        if st.button("🚀 Get Started", use_container_width=True, type="primary", key="get_started_landing"):
            st.switch_page("pages/2_📝_Register.py")
else:
    hc1, hc2, hc3, hc4 = st.columns(4)
    with hc1:
        if st.button("🚀 Get Started", use_container_width=True, type="primary"):
            st.switch_page("pages/2_📝_Register.py")
    with hc2:
        st.page_link("pages/12_📈_Dashboard_Generator.py", label="📊 View Dashboard Demo", use_container_width=True)
    with hc3:
        st.page_link("pages/9_🤖_Prakriti_AI_Connect.py", label="🌿 Talk to Prakriti AI", use_container_width=True)
    with hc4:
        if st.button("▶ Explore Features", use_container_width=True):
            st.session_state["_scroll_features"] = True

st.markdown("---")

# ---------------------------------------------------------------
# FEATURES
# ---------------------------------------------------------------
st.markdown('<div class="eco-section-title">🌱 Platform Features</div>', unsafe_allow_html=True)
st.markdown('<div class="eco-section-sub">Everything a Smart City needs for sustainable waste management, in one platform.</div>', unsafe_allow_html=True)

features = [
    ("📢", "AI Waste Reporting", "Report waste issues in seconds with photo, location & AI-assisted description."),
    ("🤖", "AI Waste Classification", "Upload a photo — AI identifies plastic, organic, e-waste and more instantly."),
    ("♻️", "Recycling Guide", "Category-wise disposal & recycling guidance tailored for Indian households."),
    ("📍", "Complaint Tracking", "Track every complaint from submission to resolution in real time."),
    ("🌿", "Prakriti AI Connect", "24×7 bilingual AI sustainability assistant, on every page."),
    ("📊", "Dashboard Generator", "Upload any CSV/Excel and auto-generate KPI cards, charts & AI insights."),
    ("📈", "Smart Analytics", "Ward-wise, category-wise and time-series analytics for officers & admins."),
    ("🏆", "Green Rewards", "Earn points for responsible reporting and climb the city leaderboard."),
    ("📄", "AI Reports", "Generate citizen, officer and municipality reports in PDF/Excel."),
    ("🗺️", "Recycling Centre Locator", "Find the nearest authorized recycling & e-waste centres."),
    ("🌍", "Carbon Calculator", "Estimate your personal carbon footprint and get reduction tips."),
    ("🧑‍💼", "Officer Dashboard", "Complaint management, worker assignment & performance analytics."),
]

for row_start in range(0, len(features), 4):
    cols = st.columns(4)
    for col, (icon, title, desc) in zip(cols, features[row_start:row_start + 4]):
        with col:
            st.markdown(
                f"""<div class="eco-card">
                        <div style="font-size:2rem;">{icon}</div>
                        <div style="font-weight:700;margin:0.3rem 0;">{title}</div>
                        <div style="color:#94a3b8;font-size:0.88rem;">{desc}</div>
                    </div>""",
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------
# WHY CHOOSE US
# ---------------------------------------------------------------
st.markdown('<div class="eco-section-title">💡 Why Choose Our Platform</div>', unsafe_allow_html=True)
why = ["AI Powered", "Fast Complaint Resolution", "Interactive Dashboards", "Smart Analytics",
       "Citizen Engagement", "Smart City Ready", "Secure", "Scalable", "Cloud Hosted"]
cols = st.columns(3)
for i, w in enumerate(why):
    with cols[i % 3]:
        st.markdown(f'<span class="eco-pill">✔ {w}</span>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------
# SDG SECTION
# ---------------------------------------------------------------
st.markdown('<div class="eco-section-title">🌎 Supporting the UN Sustainable Development Goals</div>', unsafe_allow_html=True)
sdg1, sdg2, sdg3 = st.columns(3)
with sdg1:
    st.markdown('<div class="eco-card" style="border-left:4px solid #FD9D24;"><h3>🏙️ SDG 11</h3><b>Sustainable Cities & Communities</b><p style="color:#94a3b8;">Cleaner, more resilient urban neighborhoods through smart complaint resolution.</p></div>', unsafe_allow_html=True)
with sdg2:
    st.markdown('<div class="eco-card" style="border-left:4px solid #BF8B2E;"><h3>♻️ SDG 12</h3><b>Responsible Consumption & Production</b><p style="color:#94a3b8;">Better segregation, recycling and reduced landfill burden.</p></div>', unsafe_allow_html=True)
with sdg3:
    st.markdown('<div class="eco-card" style="border-left:4px solid #3F7E44;"><h3>🌡️ SDG 13</h3><b>Climate Action</b><p style="color:#94a3b8;">Carbon tracking and awareness to reduce each citizen\'s footprint.</p></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------
# STATISTICS
# ---------------------------------------------------------------
st.markdown('<div class="eco-section-title">📊 Platform Impact</div>', unsafe_allow_html=True)
stats = [("10,000+", "Complaints Managed"), ("95%", "AI Classification Accuracy"),
         ("50+", "Recycling Centres"), ("100%", "Cloud Powered"),
         ("24×7", "AI Assistant"), ("10×", "Faster Analytics")]
cols = st.columns(6)
for col, (num, label) in zip(cols, stats):
    with col:
        st.markdown(f'<div class="eco-stat"><div class="num">{num}</div><div class="label">{label}</div></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------
# PRAKRITI AI PREVIEW
# ---------------------------------------------------------------
st.markdown('<div class="eco-section-title">🤖 Meet Prakriti AI Connect</div>', unsafe_allow_html=True)
p1, p2 = st.columns([1, 2])
with p1:
    st.markdown('<div style="font-size:5rem;text-align:center;" class="eco-float">🌿🤖</div>', unsafe_allow_html=True)
with p2:
    st.markdown(
        """<div class="eco-card">
        <div class="chat-bubble-user">🧑 How should I dispose of old batteries?</div>
        <div class="chat-bubble-ai">🌿 Old batteries are hazardous e-waste — never put them in your household bin.
        Drop them off at your nearest MCG e-waste collection centre, or hand them to an authorized
        e-waste collector. Want me to find the nearest centre for you?</div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.page_link("pages/9_🤖_Prakriti_AI_Connect.py", label="💬 Start chatting with Prakriti AI Connect", icon="🌿")

# ---------------------------------------------------------------
# GREEN IMPACT (animated-style counters)
# ---------------------------------------------------------------
st.markdown('<div class="eco-section-title">🌿 Green Impact</div>', unsafe_allow_html=True)
impact = [("18.2 tons", "Plastic Waste Reduced"), ("3,400+", "Trees Saved (Est.)"),
          ("12,500+", "Citizens Registered"), ("9,800+", "Complaints Resolved"),
          ("68%", "Recycling Rate"), ("410 tons", "Carbon Reduction (Est.)")]
cols = st.columns(3)
for i, (num, label) in enumerate(impact):
    with cols[i % 3]:
        st.markdown(f'<div class="eco-stat"><div class="num">{num}</div><div class="label">{label}</div></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------
# TESTIMONIALS
# ---------------------------------------------------------------
st.markdown('<div class="eco-section-title">⭐ What People Say</div>', unsafe_allow_html=True)
testimonials = [
    ("👩", "Priya Sharma", "Citizen, Sector 45", "I reported an overflowing bin and it was cleared within a day. The AI chatbot even told me how to compost my kitchen waste!"),
    ("👮", "R. Kumar", "MCG Sanitation Officer", "The dashboard makes it so much easier to prioritize high-risk complaints like biomedical waste across wards."),
    ("🧑‍🤝‍🧑", "Green Earth NGO", "Volunteer Partner", "The awareness generator helps us create campaign material for schools in minutes."),
]
cols = st.columns(3)
for col, (avatar, name, role, quote) in zip(cols, testimonials):
    with col:
        st.markdown(
            f"""<div class="eco-card">
                <div style="font-size:2rem;">{avatar}</div>
                <p style="color:#cbd5e1;font-style:italic;">"{quote}"</p>
                <b>{name}</b><br><span style="color:#94a3b8;font-size:0.85rem;">{role}</span>
            </div>""",
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------
st.markdown('<div class="eco-section-title">❓ Frequently Asked Questions</div>', unsafe_allow_html=True)
faqs = [
    ("How do I report waste?", "Register or log in as a citizen, go to 'Report Waste', upload a photo and location — our AI will classify it and generate a description automatically."),
    ("How does AI classify waste?", "We use a vision-capable AI model via OpenRouter to analyze your photo and predict the waste category with a confidence score."),
    ("Is my location secure?", "Location data is only used to route your complaint to the correct ward officer and is never shared publicly."),
    ("How does Prakriti AI Connect work?", "It's a bilingual (English/Hindi) AI chatbot available on every page to answer sustainability and waste-related questions."),
    ("Can I download reports?", "Yes — citizens, officers and admins can export PDF, Excel, CSV and HTML reports from their dashboards."),
]
for q, a in faqs:
    with st.expander(q):
        st.write(a)

# ---------------------------------------------------------------
# CONTACT + FOOTER
# ---------------------------------------------------------------
st.markdown('<div class="eco-section-title">📞 Contact Us</div>', unsafe_allow_html=True)
cc1, cc2, cc3 = st.columns(3)
with cc1:
    st.markdown(f'<div class="eco-card">📧 <b>Email</b><br>{settings.SUPPORT_EMAIL}</div>', unsafe_allow_html=True)
with cc2:
    st.markdown(f'<div class="eco-card">📱 <b>Phone</b><br>{settings.SUPPORT_PHONE}</div>', unsafe_allow_html=True)
with cc3:
    st.markdown(f'<div class="eco-card">🏢 <b>Office</b><br>{settings.MUNICIPALITY_NAME}</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="eco-footer">
        🌿 <b>EcoVision AI</b> — Designed with ❤️ for Smart Sustainable Cities<br>
        Powered by Python · Streamlit · OpenRouter AI<br>
        © 2026 EcoVision AI. All rights reserved. ·
        <a href="#" style="color:#64748b;">Privacy Policy</a> ·
        <a href="#" style="color:#64748b;">Terms</a>
    </div>
    """,
    unsafe_allow_html=True,
)
