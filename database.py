"""
Database layer for Smart AI Assistant.
Uses SQLite for user authentication, chat history, and session management.
"""

import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timedelta

import bcrypt

# Database file path (same directory as app)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smart_assistant.db")


def get_connection():
    """Get a SQLite connection with row_factory enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS session_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL DEFAULT 'New Chat',
            domain TEXT NOT NULL DEFAULT 'General',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
        CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_session_tokens_token ON session_tokens(token);
    """)

    conn.commit()
    conn.close()


# ─── User Management ───────────────────────────────────────────────────────────

def create_user(username: str, email: str, password: str, full_name: str) -> dict | None:
    """
    Register a new user. Returns user dict on success, None if username/email exists.
    Password is hashed with bcrypt before storage.
    """
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)",
            (username.strip().lower(), email.strip().lower(), password_hash, full_name.strip()),
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {
            "id": user_id,
            "username": username.strip().lower(),
            "email": email.strip().lower(),
            "full_name": full_name.strip(),
        }
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> dict | None:
    """
    Verify credentials. Returns user dict on success, None on failure.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, email, password_hash, full_name FROM users WHERE username = ?",
        (username.strip().lower(),),
    )
    row = cursor.fetchone()
    conn.close()

    if row and bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
        return {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "full_name": row["full_name"],
        }
    return None


def get_user_by_id(user_id: int) -> dict | None:
    """Fetch user by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, full_name FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


# ─── Session Token Management (Remember Me) ────────────────────────────────────

def create_session_token(user_id: int, days: int = 30) -> str:
    """
    Generate a secure session token for 'Remember Me' functionality.
    Token is valid for `days` days. Returns the token string.
    """
    token = secrets.token_urlsafe(64)
    expires_at = datetime.utcnow() + timedelta(days=days)

    conn = get_connection()
    cursor = conn.cursor()
    # Clean up any existing tokens for this user (limit to 5 active sessions)
    cursor.execute(
        "DELETE FROM session_tokens WHERE user_id = ? AND token NOT IN "
        "(SELECT token FROM session_tokens WHERE user_id = ? ORDER BY created_at DESC LIMIT 4)",
        (user_id, user_id),
    )
    cursor.execute(
        "INSERT INTO session_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at.isoformat()),
    )
    conn.commit()
    conn.close()
    return token


def validate_session_token(token: str) -> dict | None:
    """
    Validate a session token. Returns user dict if valid and not expired, else None.
    Expired tokens are cleaned up automatically.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Clean expired tokens
    cursor.execute("DELETE FROM session_tokens WHERE expires_at < ?", (datetime.utcnow().isoformat(),))
    conn.commit()

    cursor.execute(
        """SELECT u.id, u.username, u.email, u.full_name
           FROM session_tokens st
           JOIN users u ON st.user_id = u.id
           WHERE st.token = ? AND st.expires_at > ?""",
        (token, datetime.utcnow().isoformat()),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def delete_session_token(token: str):
    """Remove a session token (logout)."""
    conn = get_connection()
    conn.execute("DELETE FROM session_tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def delete_all_user_tokens(user_id: int):
    """Remove all session tokens for a user (logout everywhere)."""
    conn = get_connection()
    conn.execute("DELETE FROM session_tokens WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ─── Conversation Management ───────────────────────────────────────────────────

def create_conversation(user_id: int, title: str = "New Chat", domain: str = "General") -> int:
    """Create a new conversation. Returns the conversation ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (user_id, title, domain) VALUES (?, ?, ?)",
        (user_id, title, domain),
    )
    conn.commit()
    conv_id = cursor.lastrowid
    conn.close()
    return conv_id


def get_conversations(user_id: int, domain: str = None, search: str = None) -> list[dict]:
    """
    Get all conversations for a user, ordered by most recent.
    Optionally filter by domain or search term.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM conversations WHERE user_id = ?"
    params = [user_id]

    if domain and domain != "All":
        query += " AND domain = ?"
        params.append(domain)

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    query += " ORDER BY updated_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_conversation(conversation_id: int) -> dict | None:
    """Get a single conversation by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def update_conversation_title(conversation_id: int, title: str):
    """Update the title of a conversation."""
    conn = get_connection()
    conn.execute(
        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
        (title, datetime.utcnow().isoformat(), conversation_id),
    )
    conn.commit()
    conn.close()


def update_conversation_timestamp(conversation_id: int):
    """Touch the updated_at timestamp."""
    conn = get_connection()
    conn.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), conversation_id),
    )
    conn.commit()
    conn.close()


def delete_conversation(conversation_id: int):
    """Delete a conversation and all its messages (CASCADE)."""
    conn = get_connection()
    conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()


# ─── Message Management ────────────────────────────────────────────────────────

def save_message(conversation_id: int, role: str, content: str) -> int:
    """Save a message to a conversation. Returns message ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
        (conversation_id, role, content),
    )
    # Also update the conversation's updated_at
    cursor.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), conversation_id),
    )
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()
    return msg_id


def get_messages(conversation_id: int) -> list[dict]:
    """Get all messages for a conversation, ordered chronologically."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conversation_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_conversation_preview(conversation_id: int, max_length: int = 100) -> str:
    """Get a preview of the first user message in a conversation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT content FROM messages WHERE conversation_id = ? AND role = 'user' ORDER BY created_at ASC LIMIT 1",
        (conversation_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        text = row["content"]
        return text[:max_length] + "..." if len(text) > max_length else text
    return "Empty conversation"


def get_message_count(conversation_id: int) -> int:
    """Get the number of messages in a conversation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM messages WHERE conversation_id = ?", (conversation_id,))
    row = cursor.fetchone()
    conn.close()
    return row["count"] if row else 0
