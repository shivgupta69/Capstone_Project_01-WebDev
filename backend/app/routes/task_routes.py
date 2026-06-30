from flask import Blueprint, flash, jsonify, redirect, render_template, request, session
from backend.app.services.task_service import (
    create_task_with_details,
    delete_task,
    get_user_category_counts,
    get_filtered_task_rows,
    get_user_stats,
    get_weekly_analytics,
    update_task_status,
)
from backend.app.utils.helpers import login_required


task_bp = Blueprint("tasks", __name__)


def _get_dashboard_filters():
    return {
        "search": (request.args.get("search") or "").strip(),
        "category": (request.args.get("category") or "").strip(),
        "status": (request.args.get("status") or "").strip(),
        "due_filter": (request.args.get("due_filter") or "").strip(),
    }


def _get_dashboard_context(user_id):
    filters = _get_dashboard_filters()
    tasks = get_filtered_task_rows(
        user_id,
        search=filters["search"],
        category=filters["category"],
        status=filters["status"],
        due_filter=filters["due_filter"],
    )
    stats = get_user_stats(user_id)
    category_counts = get_user_category_counts(user_id)
    weekly_analytics = get_weekly_analytics(user_id)

    return {
        "tasks": tasks,
        "labels": [row[0] for row in stats],
        "data": [row[1] for row in stats],
        "category_counts": category_counts,
        "filters": filters,
        "weekly_analytics": weekly_analytics,
    }


@task_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]
    return render_template("dashboard.html", **_get_dashboard_context(user_id))


@task_bp.route("/api/dashboard-fragments")
@login_required
def dashboard_fragments():
    context = _get_dashboard_context(session["user_id"])
    return jsonify(
        {
            "metricsHtml": render_template("partials/dashboard_metrics.html", **context),
            "filtersHtml": render_template("partials/dashboard_filters.html", **context),
            "taskListHtml": render_template("partials/dashboard_task_list.html", **context),
            "sidebarHtml": render_template("partials/dashboard_sidebar.html", **context),
        }
    )


@task_bp.route("/add", methods=["POST"])
@login_required
def add_task():
    _, message, category, _ = create_task_with_details(
        session["user_id"],
        request.form.get("task"),
        request.form.get("category"),
        request.form.get("duration"),
        request.form.get("due_date"),
        request.form.get("status") or "todo",
    )
    flash(message, category)
    return redirect("/")


@task_bp.route("/api/tasks", methods=["POST"])
@login_required
def add_task_api():
    payload = request.get_json(silent=True) or request.form
    success, message, _, task = create_task_with_details(
        session["user_id"],
        payload.get("task"),
        payload.get("category"),
        payload.get("duration"),
        payload.get("due_date"),
        payload.get("status") or "todo",
    )
    status_code = 201 if success else 400
    return jsonify({"success": success, "message": message, "task": task}), status_code


@task_bp.route("/delete/<int:id>", methods=["GET", "POST"])
@login_required
def remove_task(id):
    _, message, category, _ = delete_task(id, session["user_id"])
    flash(message, category)
    return redirect("/")


@task_bp.route("/api/tasks/<int:id>", methods=["DELETE"])
@login_required
def delete_task_api(id):
    success, message, _, task = delete_task(id, session["user_id"])
    status_code = 200 if success else 404
    return jsonify({"success": success, "message": message, "taskId": id}), status_code


@task_bp.route("/task/<int:id>/status", methods=["POST"])
@login_required
def change_task_status(id):
    _, message, category, _ = update_task_status(
        id, session["user_id"], request.form.get("status")
    )
    flash(message, category)
    return redirect("/")


@task_bp.route("/api/tasks/<int:id>/status", methods=["PUT"])
@login_required
def change_task_status_api(id):
    status = None
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        status = payload.get("status")
    if status is None:
        status = request.form.get("status")

    success, message, _, task = update_task_status(id, session["user_id"], status)
    status_code = 200 if success else 400
    return (
        jsonify(
            {
                "success": success,
                "message": message,
                "taskId": id,
                "status": status,
                "task": task,
            }
        ),
        status_code,
    )
