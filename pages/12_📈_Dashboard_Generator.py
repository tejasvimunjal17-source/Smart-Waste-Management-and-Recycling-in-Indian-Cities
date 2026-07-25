import streamlit as st
import pandas as pd
import plotly.express as px
import io
from utils.ai_client import chat_completion
from utils.helpers import load_css, init_session_state
from config import settings

st.set_page_config(page_title="Dashboard Generator | EcoVision AI", page_icon="📈", layout="wide")
init_session_state()
load_css()

st.markdown('<div class="eco-hero"><h1>📈 Smart Analytics Dashboard Generator</h1><p>Upload any CSV or Excel file — get instant KPIs, auto-recommended charts, and AI insights.</p></div>', unsafe_allow_html=True)

file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx", "xls"])

if not file:
    st.info("👆 Upload a dataset to get started. Try any municipal, sales, or survey dataset.")
    st.stop()

try:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

st.markdown('<div class="eco-section-title">🔍 Data Overview</div>', unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f'<div class="eco-stat"><div class="num">{df.shape[0]}</div><div class="label">Rows</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="eco-stat"><div class="num">{df.shape[1]}</div><div class="label">Columns</div></div>', unsafe_allow_html=True)
with k3:
    missing = int(df.isnull().sum().sum())
    st.markdown(f'<div class="eco-stat"><div class="num">{missing}</div><div class="label">Missing Values</div></div>', unsafe_allow_html=True)
with k4:
    dupes = int(df.duplicated().sum())
    st.markdown(f'<div class="eco-stat"><div class="num">{dupes}</div><div class="label">Duplicate Rows</div></div>', unsafe_allow_html=True)

with st.expander("📋 Column Types & Preview"):
    dtype_df = pd.DataFrame({"Column": df.columns, "Type": [str(t) for t in df.dtypes],
                              "Missing": df.isnull().sum().values})
    st.dataframe(dtype_df, use_container_width=True)
    st.dataframe(df.head(20), use_container_width=True)

numeric_cols = df.select_dtypes(include="number").columns.tolist()
categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
datetime_cols = [c for c in df.columns if "date" in c.lower() or "time" in c.lower()]

st.markdown('<div class="eco-section-title">🎛️ Filters</div>', unsafe_allow_html=True)
filtered_df = df.copy()
if categorical_cols:
    filt_col = st.selectbox("Filter by column (optional)", ["None"] + categorical_cols)
    if filt_col != "None":
        options = ["All"] + sorted(df[filt_col].dropna().astype(str).unique().tolist())
        choice = st.selectbox(f"Value for {filt_col}", options)
        if choice != "All":
            filtered_df = filtered_df[filtered_df[filt_col].astype(str) == choice]

st.markdown('<div class="eco-section-title">📊 Auto-Generated Charts</div>', unsafe_allow_html=True)

charts_made = 0
if categorical_cols and numeric_cols:
    c1, c2 = st.columns(2)
    with c1:
        cat = categorical_cols[0]
        agg = filtered_df.groupby(cat)[numeric_cols[0]].sum().reset_index().head(15)
        fig = px.bar(agg, x=cat, y=numeric_cols[0], title=f"{numeric_cols[0]} by {cat}", color=cat)
        st.plotly_chart(fig, use_container_width=True)
        charts_made += 1
    with c2:
        fig = px.pie(agg, names=cat, values=numeric_cols[0], title=f"{cat} Distribution", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        charts_made += 1

if len(numeric_cols) >= 1:
    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(filtered_df, x=numeric_cols[0], title=f"Distribution of {numeric_cols[0]}", nbins=30)
        st.plotly_chart(fig, use_container_width=True)
        charts_made += 1
    with c2:
        if len(numeric_cols) >= 2:
            fig = px.scatter(filtered_df, x=numeric_cols[0], y=numeric_cols[1],
                              title=f"{numeric_cols[0]} vs {numeric_cols[1]}",
                              color=categorical_cols[0] if categorical_cols else None)
            st.plotly_chart(fig, use_container_width=True)
            charts_made += 1

if datetime_cols and numeric_cols:
    try:
        ts_df = filtered_df.copy()
        ts_df[datetime_cols[0]] = pd.to_datetime(ts_df[datetime_cols[0]], errors="coerce")
        ts_df = ts_df.dropna(subset=[datetime_cols[0]]).groupby(
            ts_df[datetime_cols[0]].dt.to_period("M"))[numeric_cols[0]].sum().reset_index()
        ts_df[datetime_cols[0]] = ts_df[datetime_cols[0]].astype(str)
        fig = px.line(ts_df, x=datetime_cols[0], y=numeric_cols[0], title="Time Series Trend", markers=True)
        st.plotly_chart(fig, use_container_width=True)
        charts_made += 1
    except Exception:
        pass

if len(numeric_cols) >= 2:
    corr = filtered_df[numeric_cols].corr()
    fig = px.imshow(corr, text_auto=".2f", title="Correlation Heatmap", color_continuous_scale="RdYlGn")
    st.plotly_chart(fig, use_container_width=True)
    charts_made += 1

if charts_made == 0:
    st.info("Couldn't auto-detect chartable columns — try a dataset with at least one numeric column.")

st.markdown('<div class="eco-section-title">🤖 AI-Generated Insights</div>', unsafe_allow_html=True)
if st.button("Generate AI Insights", type="primary"):
    summary_stats = filtered_df.describe(include="all").to_string()[:3000]
    prompt = (
        f"Here is a statistical summary of an uploaded dataset with columns {list(df.columns)}:\n"
        f"{summary_stats}\n\n"
        "Give 4-5 concise, non-obvious data insights and 2 recommendations, as bullet points."
    )
    with st.spinner("Analyzing dataset..."):
        insights = chat_completion(
            [{"role": "system", "content": "You are a data analyst generating executive insights."},
             {"role": "user", "content": prompt}],
            temperature=0.4, max_tokens=500,
        )
    st.markdown(f'<div class="eco-card">{insights}</div>', unsafe_allow_html=True)

st.markdown('<div class="eco-section-title">⬇️ Download</div>', unsafe_allow_html=True)
d1, d2, d3 = st.columns(3)
with d1:
    st.download_button("Download CSV", filtered_df.to_csv(index=False).encode(), "dashboard_data.csv", "text/csv")
with d2:
    buf = io.BytesIO()
    filtered_df.to_excel(buf, index=False, engine="openpyxl")
    st.download_button("Download Excel", buf.getvalue(), "dashboard_data.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
with d3:
    html = filtered_df.to_html(index=False)
    st.download_button("Download HTML", html.encode(), "dashboard_data.html", "text/html")

st.caption("Tip: use each chart's built-in camera icon (top-right of the chart) to download it as PNG.")
