from flask import Blueprint, render_template, session

from backend.app.services.schedule_service import generate_schedule
from backend.app.services.task_service import get_user_task_rows
from backend.app.utils.helpers import login_required
from backend.app.utils.timezone import IST, ensure_ist


schedule_bp = Blueprint("schedule", __name__)


@schedule_bp.route("/schedule")
@login_required
def schedule_view():
    tasks = get_user_task_rows(session["user_id"])
    schedule = generate_schedule(tasks)
    for item in schedule:
        item["start_time"] = ensure_ist(item.get("start_time"))
        item["end_time"] = ensure_ist(item.get("end_time"))
    return render_template("schedule.html", schedule=schedule, timezone_label=IST.zone)
