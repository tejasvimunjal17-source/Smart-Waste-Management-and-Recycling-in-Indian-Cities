"""
database/db.py
----------------
Thin SQLite access layer. Every query goes through get_connection()
so we get consistent foreign-key enforcement, row-dict access, and a
single place to add logging or swap databases later.

SQL Injection protection: every query in this codebase uses
parameterized placeholders ("?") — never f-string / .format() query
building with untrusted input.
"""
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ecovision.db")


def _row_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


@contextmanager
def get_connection():
    Path(settings.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.DATABASE_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = _row_factory
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Database error — transaction rolled back")
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables if they don't exist yet, and seed defaults."""
    schema_path = Path(__file__).parent / "schema.sql"
    with get_connection() as conn:
        conn.executescript(schema_path.read_text())
    _seed_categories()
    _seed_recycling_centres()
    _seed_admin()


def execute(query: str, params: tuple = ()):
    with get_connection() as conn:
        cur = conn.execute(query, params)
        return cur.lastrowid


def fetch_one(query: str, params: tuple = ()):
    with get_connection() as conn:
        cur = conn.execute(query, params)
        return cur.fetchone()


def fetch_all(query: str, params: tuple = ()):
    with get_connection() as conn:
        cur = conn.execute(query, params)
        return cur.fetchall()


def _seed_categories():
    defaults = [
        ("Plastic", "Plastic bottles, bags, wrappers, containers", "🧴",
         "Rinse and place in the dry-waste bin; drop bulk plastic at an authorized recycler."),
        ("Organic", "Food scraps, garden waste, biodegradable matter", "🍂",
         "Compost at home or place in the wet-waste (green) bin for municipal composting."),
        ("Paper", "Newspaper, cardboard, cartons, office paper", "📄",
         "Flatten and keep dry; place in the dry-waste bin or sell to a kabadiwala."),
        ("Glass", "Bottles, jars, broken glassware", "🍾",
         "Wrap broken pieces safely, place in dry-waste bin marked 'glass'."),
        ("Metal", "Cans, foil, scrap metal, utensils", "🔩",
         "Place in dry-waste bin; scrap metal can be sold to authorized scrap dealers."),
        ("Mixed", "Non-segregated general waste", "🗑️",
         "Please segregate at source; mixed waste delays processing and recycling."),
        ("E-Waste", "Batteries, electronics, wires, appliances", "🔋",
         "Never mix with household waste — drop at an authorized MCG e-waste collection centre."),
        ("Biomedical", "Medical/clinical waste, sharps, PPE", "🩺",
         "Requires special handling — contact MCG health department or an authorized biomedical waste handler."),
        ("Construction", "Debris, rubble, bricks, concrete", "🧱",
         "Book a municipal C&D waste pickup; do not dump on roads or drains."),
    ]
    with get_connection() as conn:
        for name, desc, icon, guide in defaults:
            conn.execute(
                "INSERT OR IGNORE INTO categories (name, description, icon, disposal_guide) VALUES (?,?,?,?)",
                (name, desc, icon, guide),
            )


def _seed_recycling_centres():
    centres = [
        ("MCG Material Recovery Facility - Sector 39", "Dry Waste MRF", "Sector 39, Gurugram",
         "Sector 39", 28.4501, 77.0424, "+91-124-2222222", "Plastic,Paper,Metal,Glass"),
        ("MCG E-Waste Collection Centre - Sector 14", "E-Waste", "Sector 14, Gurugram",
         "Sector 14", 28.4699, 77.0266, "+91-124-2333333", "E-Waste,Batteries"),
        ("Composting Unit - Sector 52", "Organic/Composting", "Sector 52, Gurugram",
         "Sector 52", 28.4177, 77.0729, "+91-124-2444444", "Organic"),
        ("Scrap & Metal Recyclers - Udyog Vihar", "Scrap/Metal", "Udyog Vihar Phase 3, Gurugram",
         "Udyog Vihar", 28.5017, 77.0881, "+91-124-2555555", "Metal,Glass"),
    ]
    with get_connection() as conn:
        existing = conn.execute("SELECT COUNT(*) as c FROM recycling_centres").fetchone()["c"]
        if existing == 0:
            for row in centres:
                conn.execute(
                    """INSERT INTO recycling_centres
                       (name, type, address, ward, latitude, longitude, contact, materials_accepted)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    row,
                )


def _seed_admin():
    """Create one default admin account on first run (dev convenience)."""
    from backend.auth import hash_password
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE role='admin' LIMIT 1").fetchone()
        if not existing:
            pw_hash, salt = hash_password("Admin@12345")
            conn.execute(
                """INSERT INTO users (full_name, email, phone, password_hash, salt, role, ward)
                   VALUES (?,?,?,?,?,?,?)""",
                ("System Administrator", "admin@ecovision.local", "9999999999",
                 pw_hash, salt, "admin", "HQ"),
            )
            logger.info("Seeded default admin: admin@ecovision.local / Admin@12345 (change immediately)")
