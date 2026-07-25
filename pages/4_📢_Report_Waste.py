import streamlit as st
from pathlib import Path
from datetime import datetime
from backend.complaints import create_complaint
from utils.ai_client import classify_waste_image, generate_complaint_description, predict_priority
from utils.helpers import load_css, require_login, toast
from config import settings

st.set_page_config(page_title="Report Waste | EcoVision AI", page_icon="📢", layout="wide")
require_login(allowed_roles=["citizen"])
load_css()

user = st.session_state["user"]
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "assets" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

st.markdown('<div class="eco-hero"><h1>📢 Report a Waste Issue</h1><p>Upload a photo — our AI will classify the waste and help you write the complaint.</p></div>', unsafe_allow_html=True)

if not settings.is_ai_configured():
    st.warning("⚠️ AI classification is running in **demo mode** — add a real `OPENROUTER_API_KEY` to `.env` for live results.")

st.markdown('<div class="eco-section-title">Step 1 · Upload Photo</div>', unsafe_allow_html=True)
image_file = st.file_uploader("Upload a clear photo of the waste", type=["jpg", "jpeg", "png"])

ai_result = None
if image_file:
    col_img, col_result = st.columns([1, 1])
    with col_img:
        st.image(image_file, caption="Uploaded photo", use_container_width=True)
    with col_result:
        if st.button("🤖 Classify with AI", type="primary", use_container_width=True):
            with st.spinner("Analyzing image with AI..."):
                image_bytes = image_file.getvalue()
                ai_result = classify_waste_image(image_bytes, mime_type=image_file.type or "image/jpeg")
                st.session_state["_ai_result"] = ai_result
        ai_result = st.session_state.get("_ai_result")
        if ai_result:
            st.markdown(
                f"""<div class="eco-card">
                <b>Predicted Category:</b> {ai_result.get('category','Unknown')}<br>
                <b>Confidence:</b> {ai_result.get('confidence',0)}%<br>
                <b>Recycling Method:</b> {ai_result.get('recycling_method','-')}<br>
                <b>Disposal Guide:</b> {ai_result.get('disposal_guide','-')}<br>
                <b>Environmental Impact:</b> {ai_result.get('environmental_impact','-')}
                </div>""",
                unsafe_allow_html=True,
            )
            if ai_result.get("note"):
                st.caption(ai_result["note"])

st.markdown('<div class="eco-section-title">Step 2 · Complaint Details</div>', unsafe_allow_html=True)

with st.form("complaint_form"):
    default_category = st.session_state.get("_ai_result", {}).get("category", "Mixed") if st.session_state.get("_ai_result") else "Mixed"
    idx = settings.WASTE_CATEGORIES.index(default_category) if default_category in settings.WASTE_CATEGORIES else 5
    category = st.selectbox("Waste Category", settings.WASTE_CATEGORIES, index=idx)
    ward = st.text_input("Ward / Sector", value=user.get("ward") or "")
    address_text = st.text_input("Landmark / Address", value=user.get("address") or "")
    raw_notes = st.text_area("Describe the issue (optional — AI can help write this)")

    gen_ai_desc = st.form_submit_button("✍️ Generate AI Description")
    submitted = st.form_submit_button("✅ Submit Complaint", type="primary", use_container_width=True)

if gen_ai_desc:
    with st.spinner("Writing a professional description..."):
        st.session_state["_ai_desc"] = generate_complaint_description(category, ward, raw_notes)

if st.session_state.get("_ai_desc"):
    st.info(f"**AI-generated description:**\n\n{st.session_state['_ai_desc']}")

if submitted:
    final_description = raw_notes.strip() or st.session_state.get("_ai_desc", "") or f"{category} waste reported at {ward or 'unspecified location'}."
    with st.spinner("Submitting complaint..."):
        priority = predict_priority(category, final_description)
        image_path = ""
        if image_file:
            ext = Path(image_file.name).suffix or ".jpg"
            image_path = str(UPLOAD_DIR / f"complaint_{user['id']}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{ext}")
            Path(image_path).write_bytes(image_file.getvalue())

        ai_res = st.session_state.get("_ai_result") or {}
        complaint_id = create_complaint(
            user_id=user["id"],
            category=category,
            description=final_description,
            ai_description=st.session_state.get("_ai_desc", ""),
            ai_predicted_category=ai_res.get("category", ""),
            ai_confidence=ai_res.get("confidence"),
            priority=priority,
            image_path=image_path,
            ward=ward,
            address_text=address_text,
        )
    toast(f"Complaint #{complaint_id} submitted! +10 reward points 🎉")
    st.success(f"✅ Complaint #{complaint_id} submitted successfully with **{priority}** priority!")
    st.session_state.pop("_ai_result", None)
    st.session_state.pop("_ai_desc", None)
    st.balloons()
    st.page_link("pages/5_📜_Complaint_History.py", label="View Complaint History", icon="📜")
