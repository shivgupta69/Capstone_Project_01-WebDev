"""Repository layer package."""

from backend.app.repositories.user_repository import (
    insert_user,
    fetch_user_by_username,
    fetch_user_by_id,
    is_duplicate_username_error,
)
from backend.app.repositories.task_repository import (
    fetch_tasks_by_user_id,
    fetch_task_by_id_for_user,
    fetch_filtered_tasks,
    fetch_distinct_categories,
    fetch_category_counts,
    fetch_stats_by_category,
    fetch_task_columns,
    insert_task,
    delete_task_for_user,
    update_task_status_for_user,
    update_task_schedule_fields,
    fetch_weekly_analytics,
)
from backend.app.repositories.analytics_repository import (
    ensure_study_logs_table,
    insert_daily_study_log,
    fetch_daily_analytics_rows,
)

__all__ = [
    "insert_user",
    "fetch_user_by_username",
    "fetch_user_by_id",
    "is_duplicate_username_error",
    "fetch_tasks_by_user_id",
    "fetch_task_by_id_for_user",
    "fetch_filtered_tasks",
    "fetch_distinct_categories",
    "fetch_category_counts",
    "fetch_stats_by_category",
    "fetch_task_columns",
    "insert_task",
    "delete_task_for_user",
    "update_task_status_for_user",
    "update_task_schedule_fields",
    "fetch_weekly_analytics",
    "ensure_study_logs_table",
    "insert_daily_study_log",
    "fetch_daily_analytics_rows",
]
