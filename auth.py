"""
INKFORGE — Auth & Session Management
Local user accounts with SHA-256 passwords.
Per-user story history stored in JSON files.
"""
import os
import json
import hashlib
import secrets
import streamlit as st
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "userdata"
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"


# ── LOW-LEVEL ──────────────────────────────────────────────────
def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _load_users() -> dict:
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text())
        except:
            pass
    return {}


def _save_users(users: dict):
    USERS_FILE.write_text(json.dumps(users, indent=2))


def _load_sessions() -> dict:
    if SESSIONS_FILE.exists():
        try:
            return json.loads(SESSIONS_FILE.read_text())
        except:
            pass
    return {}


def _save_sessions(sessions: dict):
    SESSIONS_FILE.write_text(json.dumps(sessions, indent=2))


def _user_dir(username: str) -> Path:
    d = DATA_DIR / username
    d.mkdir(exist_ok=True)
    return d


# ── USER MANAGEMENT ────────────────────────────────────────────
def register_user(username: str, password: str, display_name: str = "") -> tuple[bool, str]:
    if not username or not password:
        return False, "Username and password required."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    users = _load_users()
    if username.lower() in users:
        return False, "Username already taken."
    users[username.lower()] = {
        "username": username.lower(),
        "display_name": display_name or username,
        "password_hash": _hash(password),
        "created_at": datetime.now().isoformat(),
        "avatar": username[0].upper(),
    }
    _save_users(users)
    _user_dir(username.lower())
    return True, "Account created!"


def login_user(username: str, password: str) -> tuple[bool, str, dict]:
    users = _load_users()
    u = username.lower().strip()
    if u not in users:
        return False, "User not found.", {}
    if users[u]["password_hash"] != _hash(password):
        return False, "Incorrect password.", {}
    token = secrets.token_hex(32)
    sessions = _load_sessions()
    sessions[token] = {"username": u, "created_at": datetime.now().isoformat()}
    _save_sessions(sessions)
    return True, token, users[u]


def validate_session(token: str) -> tuple[bool, dict]:
    if not token:
        return False, {}
    sessions = _load_sessions()
    if token not in sessions:
        return False, {}
    users = _load_users()
    u = sessions[token]["username"]
    if u not in users:
        return False, {}
    return True, users[u]


def logout(token: str):
    sessions = _load_sessions()
    sessions.pop(token, None)
    _save_sessions(sessions)


# ── STORY HISTORY ──────────────────────────────────────────────
def _history_file(username: str) -> Path:
    return _user_dir(username) / "history.json"


def load_history(username: str) -> list:
    f = _history_file(username)
    if f.exists():
        try:
            history  = json.loads(f.read_text())
            # Pinned first, then most recently updated at top
            pinned   = sorted([h for h in history if h.get("pinned")],     key=lambda h: h.get("updated_at",""), reverse=True)
            unpinned = sorted([h for h in history if not h.get("pinned")], key=lambda h: h.get("updated_at",""), reverse=True)
            return pinned + unpinned
        except:
            pass
    return []


def save_session_to_history(username: str, session_data: dict):
    """Save current story session as a history entry."""
    history = load_history(username)
    title = session_data.get("story_title", "Untitled")
    wc    = session_data.get("word_count", 0)
    blocks = session_data.get("story_blocks", [])
    if not blocks:
        return  # Don't save empty sessions

    # Find if this session_id already exists
    sid = session_data.get("session_id")
    entry = {
        "session_id": sid,
        "title": title,
        "word_count": wc,
        "genre": session_data.get("genre", ""),
        "tone": session_data.get("tone", ""),
        "chapter": session_data.get("chapter", 1),
        "updated_at": datetime.now().isoformat(),
        "preview": blocks[-1]["content"][:120] if blocks and blocks[-1].get("content") else "",
        "story_blocks": blocks,
        "book_passage_indices": session_data.get("book_passage_indices", []),
        "characters": session_data.get("characters", []),
        "story_context": session_data.get("story_context", ""),
        "pov": session_data.get("pov", "Third Person"),
    }

    # Update existing or prepend
    existing = next((i for i, h in enumerate(history) if h.get("session_id") == sid), None)
    if existing is not None:
        entry["pinned"] = history[existing].get("pinned", False)  # preserve pin state
        history[existing] = entry
    else:
        history.insert(0, entry)

    # Sort: pinned first, then most recently updated at the top
    pinned   = sorted([h for h in history if h.get("pinned")],     key=lambda h: h.get("updated_at", ""), reverse=True)
    unpinned = sorted([h for h in history if not h.get("pinned")], key=lambda h: h.get("updated_at", ""), reverse=True)
    # Keep max 50 unpinned — never drop pinned
    history  = pinned + unpinned[:50 - len(pinned)]
    _history_file(username).write_text(json.dumps(history, indent=2))


def delete_history_entry(username: str, session_id: str):
    history = load_history(username)
    history = [h for h in history if h.get("session_id") != session_id]
    _save_sorted(username, history)


# ── STREAMLIT HELPERS ──────────────────────────────────────────
def get_current_user() -> dict | None:
    token = st.session_state.get("auth_token", "")
    if not token:
        return None
    valid, user = validate_session(token)
    return user if valid else None


def require_auth() -> bool:
    """Returns True if user is logged in, False otherwise."""
    user = get_current_user()
    return user is not None


def rename_history_entry(username: str, session_id: str, new_title: str):
    history = load_history(username)
    for entry in history:
        if entry.get("session_id") == session_id:
            entry["title"] = new_title.strip()
            break
    _save_sorted(username, history)


def _save_sorted(username: str, history: list):
    """Always save with pinned first, then newest-first within each group."""
    pinned   = sorted([h for h in history if h.get("pinned")],     key=lambda h: h.get("updated_at",""), reverse=True)
    unpinned = sorted([h for h in history if not h.get("pinned")], key=lambda h: h.get("updated_at",""), reverse=True)
    _history_file(username).write_text(json.dumps(pinned + unpinned, indent=2))


def pin_history_entry(username: str, session_id: str):
    history = load_history(username)
    for entry in history:
        if entry.get("session_id") == session_id:
            entry["pinned"] = not entry.get("pinned", False)
            break
    _save_sorted(username, history)


def archive_history_entry(username: str, session_id: str):
    history = load_history(username)
    for entry in history:
        if entry.get("session_id") == session_id:
            entry["archived"] = not entry.get("archived", False)
            break
    _save_sorted(username, history)


def generate_share_token(username: str, session_id: str) -> str:
    import hashlib
    return hashlib.sha256(f"{username}:{session_id}".encode()).hexdigest()[:16]