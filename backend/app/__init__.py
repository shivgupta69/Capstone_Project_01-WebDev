"""Flask application factory module."""

from pathlib import Path

from flask import Flask, session
from werkzeug.middleware.proxy_fix import ProxyFix

from backend.config.config import Config
from backend.app.routes.auth_routes import auth_bp
from backend.app.routes.task_routes import task_bp
from backend.app.routes.schedule_routes import schedule_bp
from backend.app.routes.analytics_routes import analytics_bp
from backend.app.services.auth_service import get_user_by_id
from backend.app.utils.db import get_db as _get_db, init_db

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
TEMPLATE_DIR = FRONTEND_DIR / "templates"
STATIC_DIR = FRONTEND_DIR / "static"


def create_app(config_object=None):
    """
    Application factory for creating Flask app instances.

    Args:
        config_object: Optional configuration object or dict to override defaults.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(
        __name__,
        template_folder=str(TEMPLATE_DIR),
        static_folder=str(STATIC_DIR),
    )
    app.config.from_object(Config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    if config_object:
        if isinstance(config_object, dict):
            app.config.update(config_object)
        else:
            app.config.from_object(config_object)

    app.register_blueprint(auth_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(analytics_bp)

    with app.app_context():
        init_db(app)

    @app.context_processor
    def inject_current_user():
        """Inject current user into all templates."""
        current_user = None
        try:
            session_user = session.get("user")
            if session_user:
                current_user = session_user
            else:
                user_id = session.get("user_id")
                if isinstance(user_id, int) and user_id > 0:
                    user = get_user_by_id(user_id)
                    if user:
                        current_user = user.to_public_dict()
                        session["user"] = current_user
        except RuntimeError:
            current_user = None

        return {"current_user": current_user}

    return app


# Backward-compatible exports for existing imports/tests.
app = create_app()


def get_db():
    """Get database connection (legacy compatibility)."""
    return _get_db(app)
