from datetime import datetime, timezone

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session

from backend.app.services.auth_service import authenticate_user, register_user
from backend.app.utils.auth_tokens import generate_auth_token
from backend.app.utils.helpers import login_required


auth_bp = Blueprint("auth", __name__)


def _is_json_request():
    accepts = request.accept_mimetypes
    return request.is_json or accepts["application/json"] >= accepts["text/html"]


def _build_auth_response(user, message=None):
    token = generate_auth_token(user)
    return {
        "token": token,
        "user": user.to_public_dict(),
        "message": message,
    }


def _start_user_session(user):
    # Reset session data on login to reduce fixation risk.
    session.clear()
    session["user_id"] = user.id
    session["user"] = user.to_public_dict()
    session["auth_token"] = generate_auth_token(user)
    session["authenticated_at"] = datetime.now(timezone.utc).isoformat()
    session.permanent = True


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if request.is_json:
            payload = request.get_json(silent=True) or {}
            username = payload.get("username")
            password = payload.get("password")

        success, user, message, category = register_user(username, password)

        if success:
            if _is_json_request():
                _start_user_session(user)
                return jsonify(_build_auth_response(user, message)), 201
            flash(message, category)
            return redirect("/login")

        if _is_json_request():
            return jsonify({"message": message}), 400
        flash(message, category)
        return redirect("/register")

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if request.is_json:
            payload = request.get_json(silent=True) or {}
            username = payload.get("username")
            password = payload.get("password")

        success, user, message, category = authenticate_user(
            username, password
        )

        if success:
            _start_user_session(user)
            if _is_json_request():
                return jsonify(_build_auth_response(user)), 200
            flash("Welcome back!", "success")
            return redirect("/")

        if _is_json_request():
            return jsonify({"message": message}), 401
        flash(message, category)

    return render_template("login.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    session.clear()
    if _is_json_request():
        return jsonify({"success": True}), 200
    flash("You have been logged out safely.", "success")
    return redirect("/login")
