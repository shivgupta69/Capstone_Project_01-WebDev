"""Service layer package."""

from backend.app.services.analytics_service import get_daily_analytics, track_completion_delta
from backend.app.services.auth_service import authenticate_user, get_user_by_id, register_user
from backend.app.services.schedule_service import (
    build_study_schedule,
    generate_schedule,
    schedule_user_tasks,
)
from backend.app.services.task_service import (
    create_task,
    create_task_with_details,
    delete_task,
    get_filtered_task_rows,
    get_user_tasks,
    get_weekly_analytics,
    update_task_status,
)

__all__ = [
    "build_study_schedule",
    "authenticate_user",
    "create_task",
    "create_task_with_details",
    "delete_task",
    "generate_schedule",
    "get_daily_analytics",
    "get_filtered_task_rows",
    "get_user_by_id",
    "get_user_tasks",
    "get_weekly_analytics",
    "register_user",
    "schedule_user_tasks",
    "track_completion_delta",
    "update_task_status",
]
