"""database.py — SQLite persistence + auth for Enterprise RAG with RBAC.
Author: Avatar Putra Sigit | GitHub: qurrrrsebastian-prog
"""
import os
import sqlite3
from datetime import datetime
from typing import List, Optional

import pandas as pd

from security import hash_password, verify_password

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

# Role privilege ranking (higher == more access).
ROLE_RANK = {"Intern": 1, "Staff": 2, "Admin": 3}

DEFAULT_USERS = [
    ("admin", "admin123", "Admin", "Administrator", "admin@ava.group"),
    ("staff", "staff123", "Staff", "Staff Member", "staff@ava.group"),
    ("intern", "intern123", "Intern", "Intern User", "intern@ava.group"),
]


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row access by name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables and seed default users."""
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE,
            password_hash TEXT, role TEXT CHECK(role IN ('Admin','Staff','Intern')),
            full_name TEXT, email TEXT, created_at TEXT, last_login TEXT,
            is_active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS access_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT,
            username TEXT, role TEXT, action TEXT, question TEXT,
            answer_preview TEXT, documents_accessed TEXT);
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT,
            content_preview TEXT, content TEXT, doc_role_access TEXT,
            upload_time TEXT, file_size INTEGER);
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, user TEXT,
            action TEXT, details TEXT);
        """
    )
    conn.commit()
    # Seed default users if none exist.
    n = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    if n == 0:
        now = datetime.now().isoformat(timespec="seconds")
        for username, pw, role, full_name, email in DEFAULT_USERS:
            conn.execute(
                """INSERT INTO users
                   (username, password_hash, role, full_name, email, created_at, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, 1)""",
                (username, hash_password(pw), role, full_name, email, now),
            )
        conn.commit()
    conn.close()


def add_log(action: str, details: str = "", user: str = "system") -> None:
    """Append an entry to the audit log."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_log (timestamp, user, action, details) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), user, action, details),
    )
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------- #
# Authentication & users
# --------------------------------------------------------------------------- #
def authenticate(username: str, password: str) -> Optional[dict]:
    """Return the user dict on success (and stamp last_login), else None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)
    ).fetchone()
    if row and verify_password(password, row["password_hash"]):
        conn.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now().isoformat(timespec="seconds"), row["id"]),
        )
        conn.commit()
        user = dict(row)
        conn.close()
        return user
    conn.close()
    return None


def get_users() -> pd.DataFrame:
    """Return all users (without password hashes)."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, username, role, full_name, email, created_at, last_login, "
        "is_active FROM users ORDER BY id",
        conn,
    )
    conn.close()
    return df


def create_user(username: str, password: str, role: str, full_name: str,
                email: str) -> bool:
    """Create a new user. Returns False if the username already exists."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO users
               (username, password_hash, role, full_name, email, created_at, is_active)
               VALUES (?, ?, ?, ?, ?, ?, 1)""",
            (username, hash_password(password), role, full_name, email,
             datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_user(user_id: int, role: str, full_name: str, email: str,
                is_active: int) -> None:
    """Update a user's role, name, email and active flag."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET role=?, full_name=?, email=?, is_active=? WHERE id=?",
        (role, full_name, email, is_active, user_id),
    )
    conn.commit()
    conn.close()


def delete_user(user_id: int) -> None:
    """Delete a user by id."""
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def change_password(username: str, old_pw: str, new_pw: str) -> bool:
    """Change a user's password after verifying the old one."""
    conn = get_connection()
    row = conn.execute(
        "SELECT password_hash FROM users WHERE username = ?", (username,)
    ).fetchone()
    if not row or not verify_password(old_pw, row["password_hash"]):
        conn.close()
        return False
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (hash_password(new_pw), username),
    )
    conn.commit()
    conn.close()
    return True


# --------------------------------------------------------------------------- #
# Access log
# --------------------------------------------------------------------------- #
def log_access(username: str, role: str, action: str, question: str = "",
               answer_preview: str = "", documents_accessed: str = "") -> None:
    """Record an access-trail entry (every Q&A)."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO access_log
           (timestamp, username, role, action, question, answer_preview, documents_accessed)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (datetime.now().isoformat(timespec="seconds"), username, role, action,
         question, answer_preview[:300], documents_accessed),
    )
    conn.commit()
    conn.close()


def get_access_log(limit: int = 500) -> pd.DataFrame:
    """Return the access log, newest first."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM access_log ORDER BY id DESC LIMIT ?", conn, params=[limit]
    )
    conn.close()
    return df


# --------------------------------------------------------------------------- #
# Documents (uploaded, role-gated)
# --------------------------------------------------------------------------- #
def add_document(filename: str, content: str, doc_role_access: str) -> None:
    """Store an uploaded document with a minimum-role access level."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO documents
           (filename, content_preview, content, doc_role_access, upload_time, file_size)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (filename, content[:300], content, doc_role_access,
         datetime.now().isoformat(timespec="seconds"), len(content.encode("utf-8"))),
    )
    conn.commit()
    conn.close()


def list_documents() -> pd.DataFrame:
    """Return metadata for all uploaded documents."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, filename, doc_role_access, upload_time, file_size, "
        "content_preview FROM documents ORDER BY id DESC",
        conn,
    )
    conn.close()
    return df


def get_documents_for_role(role: str) -> List[dict]:
    """Return uploaded documents accessible to the given role (with content)."""
    rank = ROLE_RANK.get(role, 0)
    conn = get_connection()
    rows = conn.execute(
        "SELECT filename, content, doc_role_access FROM documents"
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        if rank >= ROLE_RANK.get(r["doc_role_access"], 99):
            out.append({"source": r["filename"], "content": r["content"]})
    return out


def delete_document(doc_id: int) -> None:
    """Delete an uploaded document by id."""
    conn = get_connection()
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------- #
# Analytics
# --------------------------------------------------------------------------- #
def questions_per_role() -> pd.DataFrame:
    """Return a count of questions asked per role."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT role, COUNT(*) AS questions FROM access_log "
        "WHERE action = 'query' GROUP BY role",
        conn,
    )
    conn.close()
    return df
