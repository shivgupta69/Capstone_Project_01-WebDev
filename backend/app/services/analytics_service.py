import sqlite3
from datetime import date, datetime, timedelta

from backend.app.repositories.analytics_repository import (
    ensure_study_logs_table,
    fetch_daily_analytics_rows,
    insert_daily_study_log,
)


MIN_ANALYTICS_DAYS = 7
MAX_ANALYTICS_DAYS = 30


def _is_valid_id(value):
    return isinstance(value, int) and value > 0


def _coerce_hours(value):
    try:
        hours = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, hours)


def track_completion_delta(user_id, previous_status, current_status, hours_value):
    if not _is_valid_id(user_id):
        return

    previous_status = (previous_status or "").strip()
    current_status = (current_status or "").strip()

    # Record only done-transition deltas to keep analytics deterministic.
    if previous_status != "done" and current_status == "done":
        tasks_delta = 1
        hours_delta = _coerce_hours(hours_value)
    elif previous_status == "done" and current_status != "done":
        tasks_delta = -1
        hours_delta = -_coerce_hours(hours_value)
    else:
        return

    try:
        ensure_study_logs_table()
        insert_daily_study_log(
            user_id=user_id,
            log_date=date.today().isoformat(),
            hours_studied=hours_delta,
            tasks_completed=tasks_delta,
        )
    except sqlite3.Error:
        return
    except Exception:
        return


def get_daily_analytics(user_id, days=7):
    if not _is_valid_id(user_id):
        return {"labels": [], "hours": [], "completed": []}

    try:
        days_int = int(days)
    except (TypeError, ValueError):
        days_int = MIN_ANALYTICS_DAYS

    days_int = max(MIN_ANALYTICS_DAYS, min(days_int, MAX_ANALYTICS_DAYS))

    labels = [
        (date.today() - timedelta(days=offset)).isoformat()
        for offset in reversed(range(days_int))
    ]
    hours_by_day = {label: 0.0 for label in labels}
    completed_by_day = {label: 0 for label in labels}

    try:
        ensure_study_logs_table()
        rows = fetch_daily_analytics_rows(user_id, days_int)
    except sqlite3.Error:
        rows = []
    except Exception:
        rows = []

    for row in rows:
        log_date = row[0]
        if log_date not in hours_by_day:
            continue

        try:
            datetime.strptime(log_date, "%Y-%m-%d")
        except ValueError:
            continue

        hours_value = max(0.0, float(row[1] or 0))
        completed_value = max(0, int(row[2] or 0))

        hours_by_day[log_date] = round(hours_value, 2)
        completed_by_day[log_date] = completed_value

    return {
        "labels": labels,
        "hours": [hours_by_day[label] for label in labels],
        "completed": [completed_by_day[label] for label in labels],
    }
