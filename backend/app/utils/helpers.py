"""Helper utilities for Flask routes."""

from functools import wraps

from flask import flash, redirect, session


def login_required(view_func):
    """
    Decorator to protect routes that require authentication.

    Clears session and redirects to login if user_id is invalid.

    Args:
        view_func: The route function to wrap.

    Returns:
        Wrapped function with authentication check.
    """

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not isinstance(user_id, int) or user_id <= 0:
            session.clear()
            flash("Please log in to continue.", "error")
            return redirect("/login")
        return view_func(*args, **kwargs)

    return wrapped
