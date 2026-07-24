-- ============================================================
-- Smart Waste Management — SQLite Schema
-- Run via database/db_manager.py::initialize_database()
-- ============================================================

PRAGMA foreign_keys = ON;

-- ---------------- Users ----------------
CREATE TABLE IF NOT EXISTS users (
    user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name       TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    phone           TEXT,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('citizen', 'officer', 'admin')) DEFAULT 'citizen',
    city            TEXT DEFAULT 'Gurugram',
    ward_number     TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    green_points     INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ---------------- Complaints ----------------
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    citizen_id      INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    ai_summary      TEXT,
    waste_category  TEXT CHECK (
                        waste_category IN (
                            'plastic','organic','paper','glass','metal',
                            'mixed','e_waste','biomedical','construction'
                        )
                    ),
    priority        TEXT NOT NULL CHECK (priority IN ('low','medium','high')) DEFAULT 'medium',
    status          TEXT NOT NULL CHECK (
                        status IN ('submitted','acknowledged','assigned','in_progress','resolved','rejected')
                    ) DEFAULT 'submitted',
    image_path      TEXT,
    latitude        REAL,
    longitude       REAL,
    address         TEXT,
    ward_number     TEXT,
    assigned_officer_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    resolution_notes TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at     TEXT
);

CREATE INDEX IF NOT EXISTS idx_complaints_citizen ON complaints(citizen_id);
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_ward ON complaints(ward_number);
CREATE INDEX IF NOT EXISTS idx_complaints_created ON complaints(created_at);

-- ---------------- Complaint status history (audit trail) ----------------
CREATE TABLE IF NOT EXISTS complaint_status_history (
    history_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id    INTEGER NOT NULL REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    old_status      TEXT,
    new_status      TEXT NOT NULL,
    changed_by      INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    note            TEXT,
    changed_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------- Recycling centres ----------------
CREATE TABLE IF NOT EXISTS recycling_centres (
    centre_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    accepted_categories TEXT NOT NULL,   -- comma-separated WasteCategory values
    address         TEXT NOT NULL,
    city            TEXT NOT NULL DEFAULT 'Gurugram',
    latitude        REAL,
    longitude       REAL,
    contact_phone   TEXT,
    operating_hours TEXT,
    is_govt_authorized INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------- Rewards / Green Points ledger ----------------
CREATE TABLE IF NOT EXISTS reward_transactions (
    transaction_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    points          INTEGER NOT NULL,
    reason          TEXT NOT NULL,
    related_complaint_id INTEGER REFERENCES complaints(complaint_id) ON DELETE SET NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------- Carbon footprint entries ----------------
CREATE TABLE IF NOT EXISTS carbon_footprint_entries (
    entry_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    transportation_score REAL DEFAULT 0,
    electricity_score    REAL DEFAULT 0,
    plastic_score        REAL DEFAULT 0,
    water_score           REAL DEFAULT 0,
    food_score             REAL DEFAULT 0,
    waste_score             REAL DEFAULT 0,
    total_carbon_score      REAL NOT NULL,
    ai_suggestions          TEXT,
    created_at              TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------- Chatbot conversation history ----------------
CREATE TABLE IF NOT EXISTS chatbot_conversations (
    conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    session_id      TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('user','assistant')),
    message         TEXT NOT NULL,
    language        TEXT DEFAULT 'English',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chatbot_session ON chatbot_conversations(session_id);

-- ---------------- Uploaded datasets (Dashboard Generator) ----------------
CREATE TABLE IF NOT EXISTS uploaded_datasets (
    dataset_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    uploaded_by     INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    file_name       TEXT NOT NULL,
    file_type       TEXT NOT NULL,        -- csv, xlsx, sql
    row_count       INTEGER,
    column_count    INTEGER,
    storage_path    TEXT NOT NULL,
    ai_insights     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------- Search history ----------------
CREATE TABLE IF NOT EXISTS search_history (
    search_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    query           TEXT NOT NULL,
    search_type     TEXT,                  -- e.g. 'certification', 'job', 'general'
    result_count    INTEGER,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------- Seed: default admin (password set via app first-run, NOT here) ----------------
-- Intentionally left empty. Seeding real credentials into schema.sql is a security
-- anti-pattern; the app provisions the first admin interactively on first run.
