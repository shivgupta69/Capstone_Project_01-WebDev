"""Application configuration module."""

from datetime import timedelta
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"
INSTANCE_DIR = BACKEND_DIR / "instance"

if load_dotenv:
    load_dotenv(ENV_FILE)


def _resolve_database_path() -> str:
    """Resolve the database path relative to the backend root when needed."""
    raw_path = os.getenv("DATABASE_PATH", "instance/study.db")
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return str(candidate)
    return str((BACKEND_DIR / candidate).resolve())


class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DATABASE = _resolve_database_path()
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
