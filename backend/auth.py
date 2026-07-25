"""
backend/auth.py
------------------
Secure authentication: PBKDF2-HMAC-SHA256 password hashing with a
per-user random salt (no plaintext, no reversible encryption),
registration, login with basic rate limiting, and a security-question
based password reset flow (no SMTP server available in this
environment, so reset works locally without email dependency).
"""
import os
import hashlib
import binascii
import re
import logging
from datetime import datetime, timedelta

from database.db import get_connection, fetch_one, fetch_all, execute

logger = logging.getLogger("ecovision.auth")

PBKDF2_ITERATIONS = 260_000
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 15

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or binascii.hexlify(os.urandom(16)).decode()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS)
    return binascii.hexlify(dk).decode(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    check, _ = hash_password(password, salt)
    return check == password_hash


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must include at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must include at least one number."
    return True, ""


def register_user(full_name, email, phone, password, ward="", address="",
                   role="citizen", security_question="", security_answer=""):
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    ok, msg = validate_password_strength(password)
    if not ok:
        return False, msg
    if fetch_one("SELECT id FROM users WHERE email=?", (email,)):
        return False, "An account with this email already exists."

    pw_hash, salt = hash_password(password)
    ans_hash, _ = hash_password(security_answer.strip().lower(), salt) if security_answer else (None, salt)

    try:
        user_id = execute(
            """INSERT INTO users (full_name, email, phone, password_hash, salt, role, ward,
                                   address, security_question, security_answer_hash)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (full_name.strip(), email, phone.strip(), pw_hash, salt, role, ward, address,
             security_question, ans_hash),
        )
        _log_audit(user_id, "register", f"role={role}")
        return True, user_id
    except Exception as e:
        logger.exception("Registration failed")
        return False, f"Registration failed: {e}"


def _recent_failed_attempts(email: str) -> int:
    since = (datetime.utcnow() - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    row = fetch_one(
        "SELECT COUNT(*) as c FROM login_attempts WHERE email=? AND success=0 AND created_at >= ?",
        (email, since),
    )
    return row["c"] if row else 0


def login_user(email: str, password: str):
    """Returns (success: bool, user_dict_or_message)."""
    email = email.strip().lower()

    if _recent_failed_attempts(email) >= MAX_FAILED_ATTEMPTS:
        return False, f"Too many failed attempts. Please try again in {LOCKOUT_WINDOW_MINUTES} minutes."

    user = fetch_one("SELECT * FROM users WHERE email=?", (email,))
    if not user or not user["is_active"]:
        execute("INSERT INTO login_attempts (email, success) VALUES (?,0)", (email,))
        return False, "Invalid email or password."

    if not verify_password(password, user["password_hash"], user["salt"]):
        execute("INSERT INTO login_attempts (email, success) VALUES (?,0)", (email,))
        return False, "Invalid email or password."

    execute("INSERT INTO login_attempts (email, success) VALUES (?,1)", (email,))
    execute("UPDATE users SET last_login=datetime('now') WHERE id=?", (user["id"],))
    _log_audit(user["id"], "login", "")
    user.pop("password_hash", None)
    user.pop("salt", None)
    return True, user


def get_security_question(email: str):
    user = fetch_one("SELECT security_question FROM users WHERE email=?", (email.strip().lower(),))
    return user["security_question"] if user else None


def reset_password(email: str, security_answer: str, new_password: str):
    email = email.strip().lower()
    user = fetch_one("SELECT * FROM users WHERE email=?", (email,))
    if not user:
        return False, "No account found with this email."

    ans_hash, _ = hash_password(security_answer.strip().lower(), user["salt"])
    if ans_hash != user["security_answer_hash"]:
        return False, "Security answer is incorrect."

    ok, msg = validate_password_strength(new_password)
    if not ok:
        return False, msg

    pw_hash, salt = hash_password(new_password)
    execute("UPDATE users SET password_hash=?, salt=? WHERE id=?", (pw_hash, salt, user["id"]))
    _log_audit(user["id"], "password_reset", "")
    return True, "Password reset successfully. You can now log in."


def _log_audit(user_id, action, details):
    try:
        execute("INSERT INTO audit_log (user_id, action, details) VALUES (?,?,?)",
                (user_id, action, details))
    except Exception:
        logger.warning("Audit log write failed", exc_info=True)
