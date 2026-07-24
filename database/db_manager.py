"""
SQLite connection management.

Provides a context-managed connection helper and a one-time database
initializer that applies schema.sql. All data-access code (in
database/models.py) should go through `get_connection()` rather than
opening its own sqlite3 connections.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def _ensure_db_directory() -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """
    Context-managed SQLite connection.

    Usage:
        with get_connection() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (uid,))
            row = cursor.fetchone()

    Commits on clean exit, rolls back on exception, always closes.
    """
    _ensure_db_directory()
    conn = sqlite3.connect(settings.database_path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Database transaction rolled back due to an error.")
        raise
    finally:
        conn.close()


def initialize_database() -> None:
    """
    Apply schema.sql to create all tables if they don't already exist.
    Safe to call on every app startup (idempotent — uses CREATE TABLE IF NOT EXISTS).
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    _ensure_db_directory()
    with get_connection() as conn:
        conn.executescript(schema_sql)

    logger.info("Database initialized at %s", settings.database_path)


def health_check() -> bool:
    """Quick check that the DB is reachable and has expected tables."""
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users';"
            )
            return cursor.fetchone() is not None
    except Exception:
        logger.exception("Database health check failed.")
        return False
