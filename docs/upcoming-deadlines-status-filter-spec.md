# Spec: Hide Completed Tasks From Upcoming Deadlines

## Summary

The dashboard's "Upcoming Deadlines" section should show only unfinished tasks that still need attention. Tasks with a due date and status `todo` or `in-progress` should appear. Tasks with status `done` should be excluded from the list and from the badge count.

## Problem

Previously, the sidebar counted and rendered every task with a due date. That meant completed tasks continued to appear in "Upcoming Deadlines" even after the user marked them as done.

## Desired Behavior

| Due Date | Status | Show in Upcoming Deadlines |
| --- | --- | --- |
| Present | `todo` | Yes |
| Present | `in-progress` | Yes |
| Present | `done` | No |
| Missing | Any status | No |

## Implementation Notes

- Update `frontend/templates/partials/dashboard_sidebar.html`.
- Use the same condition for the badge count and the rendered task list:
  - task has a due date
  - task status is not `done`
- Do not remove completed tasks from the main dashboard task list.
- Do not change task storage, analytics, scheduling, or status update APIs.

## Acceptance Criteria

- A due-date task marked `todo` appears in Upcoming Deadlines.
- A due-date task marked `in-progress` appears in Upcoming Deadlines.
- A due-date task marked `done` does not appear in Upcoming Deadlines.
- The Upcoming Deadlines badge count excludes completed tasks.
- If all due-date tasks are completed, the empty state appears.
- Status changes continue to refresh the dashboard through `/api/dashboard-fragments`.

## Test Coverage

Regression tests should request `/api/dashboard-fragments` and inspect `sidebarHtml` so completed tasks can still remain visible in the main task list without causing false failures.
