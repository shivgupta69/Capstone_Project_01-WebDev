import sqlite3
import re

from backend.app.models.user_model import User
from backend.app.repositories.user_repository import (
    fetch_user_by_id,
    fetch_user_by_username,
    insert_user,
    is_duplicate_username_error,
)
from backend.app.utils.security import hash_password, verify_password


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def register_user(username, password):
    username = (username or "").strip()
    password = (password or "").strip()

    if not username or not password:
        return False, None, "Username and password cannot be empty.", "error"

    if len(username) > 50:
        return False, None, "Username must be 50 characters or fewer.", "error"

    if not USERNAME_PATTERN.fullmatch(username):
        return (
            False,
            None,
            "Username can only include letters, numbers, dot, underscore, and dash.",
            "error",
        )

    if len(password) < 8:
        return False, None, "Password must be at least 8 characters.", "error"

    hashed_password = hash_password(password)

    try:
        insert_user(username, hashed_password)
        user = User.from_row(fetch_user_by_username(username))
    except sqlite3.Error as exc:
        if is_duplicate_username_error(exc):
            return False, None, "Username already exists. Please choose another.", "error"

        return False, None, "Unable to register right now. Please try again.", "error"
    except Exception:
        # Defensive catch-all to avoid exposing internals.
        return False, None, "Unable to register right now. Please try again.", "error"

    return True, user, "Registration successful! Please login.", "success"


def authenticate_user(username, password):
    username = (username or "").strip()
    password = (password or "").strip()

    if not username or not password:
        return False, None, "Username and password cannot be empty.", "error"

    try:
        row = fetch_user_by_username(username)
    except sqlite3.Error:
        return False, None, "Unable to login right now. Please try again.", "error"
    except Exception:
        return False, None, "Unable to login right now. Please try again.", "error"

    user = User.from_row(row)
    if user and verify_password(user.password, password):
        return True, user, None, None

    return False, None, "Invalid username or password.", "error"


def get_user_by_id(user_id):
    try:
        return User.from_row(fetch_user_by_id(user_id))
    except sqlite3.Error:
        return None
    except Exception:
        return None
