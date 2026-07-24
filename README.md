# 🌿 Smart Waste Management and Recycling in Indian Cities

**AI-powered Smart City Platform for Sustainable Waste Management**

Final portfolio project — 1M1B Green Skills & Applied AI Internship.
Supports **SDG 11** (Sustainable Cities), **SDG 12** (Responsible Consumption), **SDG 13** (Climate Action).

---

## 📁 Project Structure

```
smart-waste-mgmt/
├── app.py                     # Main Streamlit entry point (landing + router)
├── requirements.txt           # Python dependencies
├── .env.example                # Template for environment variables
├── .gitignore
├── README.md
│
├── config/
│   ├── settings.py            # Loads & validates env vars, app-wide config
│   └── constants.py           # Waste categories, roles, statuses, colors, etc.
│
├── database/
│   ├── schema.sql              # Full SQLite schema (DDL)
│   ├── db_manager.py           # Connection handling, migrations, query execution
│   └── models.py                # Data access objects (Users, Complaints, etc.)
│
├── backend/
│   ├── auth/
│   │   └── auth_service.py     # Registration, login, password hashing, sessions
│   └── services/
│       ├── ai_service.py        # OpenRouter/IBM Granite wrapper (all AI calls)
│       ├── complaint_service.py # Complaint CRUD + business logic
│       ├── analytics_service.py # Dashboard Generator: parsing, KPIs, charts
│       └── search_service.py    # Smart search (fuzzy/semantic/no-zero-results)
│
├── chatbot/
│   └── prakriti_ai.py          # Prakriti AI Connect chatbot logic
│
├── utils/
│   ├── logger.py                # Centralized logging setup
│   ├── validators.py            # Input validation (email, phone, files, etc.)
│   └── helpers.py               # Shared utility functions
│
├── components/
│   └── ui_components.py         # Reusable Streamlit UI (cards, nav, glassmorphism CSS)
│
├── pages/                       # Streamlit multipage app (one file per page)
│
├── assets/
│   ├── css/styles.css           # Global glassmorphism / theme styles
│   └── images/
│
├── reports/                      # Generated PDF/Excel/CSV reports land here
│
└── .streamlit/
    └── config.toml               # Theme configuration
```

## 🚀 Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in your real keys
streamlit run app.py
```

## 🔐 Environment Variables

All secrets live in `.env` (never committed — see `.gitignore`). See `.env.example`
for the full list: OpenRouter API key/base URL/model, app secret key, DB path, log level.

## 🧱 Build Status

This is the **project skeleton**: folder structure, config loading, DB schema, and
core scaffolding are in place. Feature modules (auth, report waste, AI classification,
dashboards, chatbot, landing page) are built incrementally on top of this foundation.

## 🌍 Tech Stack

Python · Streamlit · SQLite · Pandas · Plotly · OpenRouter API (IBM Granite) · ReportLab
