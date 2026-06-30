"""User repository for database operations."""

import sqlite3

from backend.app.utils.db import get_db


def insert_user(username: str, hashed_password: str) -> None:
    """
    Insert a new user into the database.

    Args:
        username: User's username.
        hashed_password: Hashed password.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, hashed_password),
    )
    conn.commit()
    conn.close()


def fetch_user_by_username(username: str):
    """
    Fetch user by username.

    Args:
        username: Username to search for.

    Returns:
        Database row or None if not found.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row


def fetch_user_by_id(user_id: int):
    """
    Fetch user by ID.

    Args:
        user_id: User's ID.

    Returns:
        Database row or None if not found.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def is_duplicate_username_error(exc: Exception) -> bool:
    """
    Check if exception is a duplicate username error.

    Args:
        exc: Exception to check.

    Returns:
        True if IntegrityError (duplicate), False otherwise.
    """
    return isinstance(exc, sqlite3.IntegrityError)
