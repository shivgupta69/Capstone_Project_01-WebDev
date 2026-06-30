"""Database utilities for SQLite connections and schema management."""

import sqlite3
from pathlib import Path
import os

from flask import current_app, has_app_context

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = BACKEND_DIR / "instance" / "study.db"


def _ensure_database_directory(db_path: str) -> None:
    """Create the SQLite parent directory when the path is file-backed."""
    db_directory = os.path.dirname(os.path.abspath(db_path))
    if db_directory:
        os.makedirs(db_directory, exist_ok=True)


def _resolve_database_path(raw_path: str) -> str:
    """Resolve relative database paths against the backend directory."""
    if raw_path == ":memory:":
        return raw_path

    candidate = Path(raw_path)
    if candidate.is_absolute():
        return str(candidate)

    return str((BACKEND_DIR / candidate).resolve())


def get_db(flask_app=None):
    """
    Get a SQLite database connection.

    Args:
        flask_app: Optional Flask app instance to get config from.

    Returns:
        SQLite connection object.
    """
    if flask_app is not None:
        db_path = flask_app.config.get("DATABASE", str(DEFAULT_DATABASE_PATH))
    elif has_app_context():
        db_path = current_app.config.get("DATABASE", str(DEFAULT_DATABASE_PATH))
    else:
        db_path = os.getenv("DATABASE_PATH", "instance/study.db")

    db_path = _resolve_database_path(db_path)

    if db_path != ":memory:":
        _ensure_database_directory(db_path)

    return sqlite3.connect(db_path)


def init_db(flask_app=None):
    """
    Initialize database with required tables.

    Creates users, tasks, and study_logs tables if they don't exist.
    Handles schema migrations for legacy databases.

    Args:
        flask_app: Optional Flask app instance to get config from.
    """
    conn = get_db(flask_app)
    cursor = conn.cursor()

    # Create users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )

    # Create tasks table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_name TEXT,
            category TEXT,
            duration INTEGER,
            due_date TEXT,
            status TEXT DEFAULT 'todo',
            estimated_hours REAL,
            scheduled_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    # Create study_logs table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS study_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            hours_studied REAL NOT NULL DEFAULT 0,
            tasks_completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    # Schema migrations for legacy databases
    cursor.execute("PRAGMA table_info(tasks)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    if "due_date" not in existing_columns:
        cursor.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")

    if "status" not in existing_columns:
        cursor.execute("ALTER TABLE tasks ADD COLUMN status TEXT DEFAULT 'todo'")

    if "estimated_hours" not in existing_columns:
        cursor.execute("ALTER TABLE tasks ADD COLUMN estimated_hours REAL")

    if "scheduled_date" not in existing_columns:
        cursor.execute("ALTER TABLE tasks ADD COLUMN scheduled_date TEXT")

    # Backfill defaults
    cursor.execute(
        "UPDATE tasks SET status='todo' WHERE status IS NULL OR TRIM(status)=''"
    )
    cursor.execute(
        "UPDATE tasks SET estimated_hours=duration WHERE estimated_hours IS NULL"
    )

    conn.commit()
    conn.close()
