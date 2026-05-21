"""
Database layer for Smart AI Assistant.
Uses Supabase (PostgreSQL) for persistent cloud storage.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from dotenv import load_dotenv
from supabase import create_client, Client

# Load .env for local development
load_dotenv()

# ─── Supabase Client (Singleton) ───────────────────────────────────────────────

_supabase_client: Client | None = None


def _get_credentials():
    """Get Supabase credentials from .env (local) or st.secrets (Streamlit Cloud)."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        try:
            import streamlit as st
            url = url or st.secrets.get("SUPABASE_URL")
            key = key or st.secrets.get("SUPABASE_KEY")
        except Exception:
            pass

    return url, key


def get_supabase_client() -> Client:
    """Get or create the Supabase client singleton."""
    global _supabase_client
    if _supabase_client is None:
        url, key = _get_credentials()
        if not url or not key:
            raise RuntimeError(
                "Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY "
                "in .env (local) or Streamlit Secrets (cloud)."
            )
        _supabase_client = create_client(url, key)
    return _supabase_client


def _now_iso() -> str:
    """Current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def init_db():
    """Verify Supabase connection. Tables must be created via Supabase SQL Editor."""
    try:
        client = get_supabase_client()
        client.table("users").select("id").limit(1).execute()
    except RuntimeError:
        raise
    except Exception as e:
        print(f"[DB] Supabase connection note: {e}")


# ─── User Management ───────────────────────────────────────────────────────────

def create_user(username: str, email: str, password: str, full_name: str) -> dict | None:
    """
    Register a new user. Returns user dict on success, None if username/email exists.
    Password is hashed with bcrypt before storage.
    """
    try:
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except Exception:
        return None

    try:
        supabase = get_supabase_client()
        result = supabase.table("users").insert({
            "username": username.strip().lower(),
            "email": email.strip().lower(),
            "password_hash": password_hash,
            "full_name": full_name.strip(),
        }).execute()

        if result.data:
            row = result.data[0]
            return {
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "full_name": row["full_name"],
            }
        return None
    except Exception as e:
        # PostgreSQL unique constraint violation = code 23505
        if "23505" in str(e) or "duplicate" in str(e).lower():
            return None
        print(f"[DB ERROR] create_user: {e}")
        return None


def authenticate_user(username: str, password: str) -> dict | None:
    """Verify credentials. Returns user dict on success, None on failure."""
    try:
        supabase = get_supabase_client()
        result = supabase.table("users").select(
            "id, username, email, password_hash, full_name"
        ).eq("username", username.strip().lower()).execute()

        if result.data:
            row = result.data[0]
            if bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
                return {
                    "id": row["id"],
                    "username": row["username"],
                    "email": row["email"],
                    "full_name": row["full_name"],
                }
        return None
    except Exception as e:
        print(f"[DB ERROR] authenticate_user: {e}")
        return None


def get_user_by_id(user_id: int) -> dict | None:
    """Fetch user by ID."""
    try:
        supabase = get_supabase_client()
        result = supabase.table("users").select(
            "id, username, email, full_name"
        ).eq("id", user_id).execute()

        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"[DB ERROR] get_user_by_id: {e}")
        return None


def get_or_create_google_user(email: str, full_name: str, google_id: str = "") -> dict | None:
    """
    Find or create a user from Google OAuth.
    - If a user with this email exists, return them.
    - Otherwise, create a new user (no password) and return them.
    """
    try:
        supabase = get_supabase_client()

        # Check if user already exists by email
        result = supabase.table("users").select(
            "id, username, email, full_name"
        ).eq("email", email.strip().lower()).execute()

        if result.data:
            return result.data[0]

        # Create new Google user (username derived from email, no password)
        username = email.split("@")[0].lower().replace(".", "_")

        # Ensure username is unique by appending random suffix if needed
        check = supabase.table("users").select("id").eq("username", username).execute()
        if check.data:
            username = f"{username}_{secrets.token_hex(3)}"

        result = supabase.table("users").insert({
            "username": username,
            "email": email.strip().lower(),
            "password_hash": "",  # Google users don't have a password
            "full_name": full_name.strip() if full_name else email.split("@")[0],
        }).execute()

        if result.data:
            row = result.data[0]
            return {
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "full_name": row["full_name"],
            }
        return None
    except Exception as e:
        print(f"[DB ERROR] get_or_create_google_user: {e}")
        return None


# ─── Session Token Management (Remember Me) ────────────────────────────────────

def create_session_token(user_id: int, days: int = 30) -> str:
    """Generate a secure session token for 'Remember Me'. Valid for `days` days."""
    token = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(days=days)

    try:
        supabase = get_supabase_client()

        # Clean up old tokens — keep max 4 active sessions
        existing = supabase.table("session_tokens").select("id").eq(
            "user_id", user_id
        ).order("created_at", desc=True).execute()

        if existing.data and len(existing.data) >= 4:
            ids_to_delete = [r["id"] for r in existing.data[4:]]
            if ids_to_delete:
                supabase.table("session_tokens").delete().in_(
                    "id", ids_to_delete
                ).execute()

        # Insert new token
        supabase.table("session_tokens").insert({
            "user_id": user_id,
            "token": token,
            "expires_at": expires_at.isoformat(),
        }).execute()
    except Exception as e:
        print(f"[DB ERROR] create_session_token: {e}")

    return token


def validate_session_token(token: str) -> dict | None:
    """Validate a session token. Returns user dict if valid and not expired, else None."""
    try:
        supabase = get_supabase_client()

        # Clean expired tokens
        supabase.table("session_tokens").delete().lt(
            "expires_at", _now_iso()
        ).execute()

        # Fetch token with joined user data
        result = supabase.table("session_tokens").select(
            "token, expires_at, users(id, username, email, full_name)"
        ).eq("token", token).gt("expires_at", _now_iso()).execute()

        if result.data:
            user_data = result.data[0].get("users")
            if user_data:
                return user_data
        return None
    except Exception as e:
        print(f"[DB ERROR] validate_session_token: {e}")
        return None


def delete_session_token(token: str):
    """Remove a session token (logout)."""
    try:
        supabase = get_supabase_client()
        supabase.table("session_tokens").delete().eq("token", token).execute()
    except Exception as e:
        print(f"[DB ERROR] delete_session_token: {e}")


def delete_all_user_tokens(user_id: int):
    """Remove all session tokens for a user (logout everywhere)."""
    try:
        supabase = get_supabase_client()
        supabase.table("session_tokens").delete().eq("user_id", user_id).execute()
    except Exception as e:
        print(f"[DB ERROR] delete_all_user_tokens: {e}")


# ─── Conversation Management ───────────────────────────────────────────────────

def create_conversation(user_id: int, title: str = "New Chat", domain: str = "General") -> int:
    """Create a new conversation. Returns the conversation ID."""
    try:
        supabase = get_supabase_client()
        result = supabase.table("conversations").insert({
            "user_id": user_id,
            "title": title,
            "domain": domain,
        }).execute()

        if result.data:
            return result.data[0]["id"]
        return None
    except Exception as e:
        print(f"[DB ERROR] create_conversation: {e}")
        return None


def get_conversations(user_id: int, domain: str = None, search: str = None) -> list[dict]:
    """Get all conversations for a user, ordered by most recent."""
    try:
        supabase = get_supabase_client()
        query = supabase.table("conversations").select("*").eq("user_id", user_id)

        if domain and domain != "All":
            query = query.eq("domain", domain)
        if search:
            query = query.ilike("title", f"%{search}%")

        result = query.order("updated_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        print(f"[DB ERROR] get_conversations: {e}")
        return []


def get_conversation(conversation_id: int) -> dict | None:
    """Get a single conversation by ID."""
    try:
        supabase = get_supabase_client()
        result = supabase.table("conversations").select("*").eq(
            "id", conversation_id
        ).execute()

        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"[DB ERROR] get_conversation: {e}")
        return None


def update_conversation_title(conversation_id: int, title: str):
    """Update the title of a conversation."""
    try:
        supabase = get_supabase_client()
        supabase.table("conversations").update({
            "title": title,
            "updated_at": _now_iso(),
        }).eq("id", conversation_id).execute()
    except Exception as e:
        print(f"[DB ERROR] update_conversation_title: {e}")


def update_conversation_timestamp(conversation_id: int):
    """Touch the updated_at timestamp."""
    try:
        supabase = get_supabase_client()
        supabase.table("conversations").update({
            "updated_at": _now_iso(),
        }).eq("id", conversation_id).execute()
    except Exception as e:
        print(f"[DB ERROR] update_conversation_timestamp: {e}")


def delete_conversation(conversation_id: int):
    """Delete a conversation and all its messages (CASCADE)."""
    try:
        supabase = get_supabase_client()
        supabase.table("conversations").delete().eq(
            "id", conversation_id
        ).execute()
    except Exception as e:
        print(f"[DB ERROR] delete_conversation: {e}")


# ─── Message Management ────────────────────────────────────────────────────────

def save_message(conversation_id: int, role: str, content: str) -> int:
    """Save a message to a conversation. Returns message ID."""
    try:
        supabase = get_supabase_client()
        result = supabase.table("messages").insert({
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
        }).execute()

        # Also update the conversation's updated_at
        supabase.table("conversations").update({
            "updated_at": _now_iso(),
        }).eq("id", conversation_id).execute()

        if result.data:
            return result.data[0]["id"]
        return None
    except Exception as e:
        print(f"[DB ERROR] save_message: {e}")
        return None


def get_messages(conversation_id: int) -> list[dict]:
    """Get all messages for a conversation, ordered chronologically."""
    try:
        supabase = get_supabase_client()
        result = supabase.table("messages").select("*").eq(
            "conversation_id", conversation_id
        ).order("created_at").execute()
        return result.data or []
    except Exception as e:
        print(f"[DB ERROR] get_messages: {e}")
        return []


def get_conversation_preview(conversation_id: int, max_length: int = 100) -> str:
    """Get a preview of the first user message in a conversation."""
    try:
        supabase = get_supabase_client()
        result = supabase.table("messages").select("content").eq(
            "conversation_id", conversation_id
        ).eq("role", "user").order("created_at").limit(1).execute()

        if result.data:
            text = result.data[0]["content"]
            return text[:max_length] + "..." if len(text) > max_length else text
        return "Empty conversation"
    except Exception as e:
        print(f"[DB ERROR] get_conversation_preview: {e}")
        return "Empty conversation"


def get_message_count(conversation_id: int) -> int:
    """Get the number of messages in a conversation."""
    try:
        supabase = get_supabase_client()
        result = supabase.table("messages").select(
            "id", count="exact"
        ).eq("conversation_id", conversation_id).execute()
        return result.count or 0
    except Exception as e:
        print(f"[DB ERROR] get_message_count: {e}")
        return 0
