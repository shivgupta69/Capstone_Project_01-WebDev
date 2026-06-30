"""Route blueprints package."""

from backend.app.routes.auth_routes import auth_bp
from backend.app.routes.task_routes import task_bp
from backend.app.routes.schedule_routes import schedule_bp
from backend.app.routes.analytics_routes import analytics_bp

__all__ = ["auth_bp", "task_bp", "schedule_bp", "analytics_bp"]
