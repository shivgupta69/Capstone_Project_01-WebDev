"""Scheduling services for dashboard timelines and task planning."""

from datetime import date, datetime, timedelta
from typing import Any

from backend.app.repositories.task_repository import (
    fetch_tasks_by_user_id,
    update_task_schedule_fields,
)
from backend.app.utils.timezone import get_ist_now, get_ist_today, make_ist_datetime

DEFAULT_DAY_START_HOUR = 9
DEFAULT_DAILY_AVAILABLE_HOURS = 4


def _parse_iso_date(date_value):
    """Parse an ISO date string into a ``date`` object."""
    if not date_value:
        return None
    try:
        return datetime.strptime(date_value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _task_priority_score(task_row, today):
    """Return a deterministic scheduling priority for a task row."""
    due_date = _parse_iso_date(task_row[5] if len(task_row) > 5 else None)
    status = task_row[6] if len(task_row) > 6 and task_row[6] else "todo"
    estimated_hours = task_row[7] if len(task_row) > 7 and task_row[7] is not None else task_row[4]

    score = 0
    if due_date:
        days_until_due = (due_date - today).days
        if days_until_due <= 1:
            score += 5
        elif days_until_due <= 3:
            score += 4
        elif days_until_due <= 7:
            score += 3
        else:
            score += 1

    if status == "in-progress":
        score += 2

    if estimated_hours >= 4:
        score += 3
    elif estimated_hours >= 2:
        score += 2
    else:
        score += 1

    return score


def generate_schedule(tasks):
    """Build the visual day timeline used by the schedule page."""
    schedule = []
    current_time = make_ist_datetime(get_ist_now().date(), DEFAULT_DAY_START_HOUR)

    sorted_tasks = sorted(tasks, key=lambda task: task[4], reverse=True)

    for task in sorted_tasks:
        duration = float(task[4])
        start_time = current_time
        end_time = start_time + timedelta(hours=duration)
        schedule.append(
            {
                "task": task[2],
                "category": task[3],
                "start_time": start_time,
                "end_time": end_time,
                "duration_hours": duration,
            }
        )
        current_time = end_time

    return schedule


def build_study_schedule(tasks, daily_available_hours=DEFAULT_DAILY_AVAILABLE_HOURS):
    """Create a day-wise study plan without exceeding daily capacity."""
    if daily_available_hours <= 0:
        daily_available_hours = DEFAULT_DAILY_AVAILABLE_HOURS

    today = get_ist_today()
    pending_tasks = []

    for row in tasks:
        status = row[6] if len(row) > 6 and row[6] else "todo"
        if status == "done":
            continue

        estimated_hours = row[7] if len(row) > 7 and row[7] is not None else row[4]
        estimated_hours = max(float(estimated_hours), 0.5)
        due_date = _parse_iso_date(row[5] if len(row) > 5 else None)

        pending_tasks.append(
            {
                "id": row[0],
                "task_name": row[2],
                "category": row[3],
                "due_date": due_date,
                "estimated_hours": estimated_hours,
                "priority_score": _task_priority_score(row, today),
            }
        )

    pending_tasks.sort(
        key=lambda task: (
            task["due_date"] is None,
            task["due_date"] or date.max,
            -task["priority_score"],
            -task["estimated_hours"],
            task["id"],
        )
    )

    day_capacity: dict[date, float] = {}
    schedule_sessions: list[dict[str, Any]] = []
    assignments = {}

    for task in pending_tasks:
        remaining_hours = task["estimated_hours"]
        cursor_day = today
        first_scheduled_day = None
        deadline_day = task["due_date"]

        while remaining_hours > 0:
            if deadline_day and cursor_day > deadline_day:
                deadline_day = None

            if cursor_day not in day_capacity:
                day_capacity[cursor_day] = float(daily_available_hours)

            available_hours = day_capacity[cursor_day]
            if available_hours <= 0:
                cursor_day += timedelta(days=1)
                continue

            allocated_hours = min(remaining_hours, available_hours)
            day_capacity[cursor_day] -= allocated_hours
            remaining_hours -= allocated_hours

            if first_scheduled_day is None:
                first_scheduled_day = cursor_day

            schedule_sessions.append(
                {
                    "task_id": task["id"],
                    "task": task["task_name"],
                    "category": task["category"],
                    "date": cursor_day.isoformat(),
                    "hours": allocated_hours,
                    "priority_score": task["priority_score"],
                }
            )

            if remaining_hours > 0:
                cursor_day += timedelta(days=1)

        assignments[task["id"]] = (
            first_scheduled_day.isoformat() if first_scheduled_day else today.isoformat()
        )

    for row in tasks:
        if row[0] not in assignments:
            assignments[row[0]] = row[8] if len(row) > 8 and row[8] else None

    return {"sessions": schedule_sessions, "assignments": assignments}


def schedule_user_tasks(user_id, daily_available_hours=DEFAULT_DAILY_AVAILABLE_HOURS):
    """Persist auto-scheduled dates for a user's current task list."""
    tasks = fetch_tasks_by_user_id(user_id)
    schedule_result = build_study_schedule(tasks, daily_available_hours=daily_available_hours)

    for task_row in tasks:
        task_id = task_row[0]
        estimated_hours = (
            task_row[7] if len(task_row) > 7 and task_row[7] is not None else task_row[4]
        )
        scheduled_date = schedule_result["assignments"].get(task_id)
        update_task_schedule_fields(task_id, user_id, estimated_hours, scheduled_date)

    return schedule_result
