from flask import Blueprint, render_template, request, session

from backend.app.services.analytics_service import get_daily_analytics
from backend.app.utils.helpers import login_required


analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
@login_required
def analytics_view():
    days = request.args.get("days", default=7, type=int)
    analytics_data = get_daily_analytics(session["user_id"], days=days)

    return render_template(
        "analytics.html",
        analytics_data=analytics_data,
        selected_days=max(7, min(days or 7, 30)),
    )
