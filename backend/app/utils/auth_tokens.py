from itsdangerous import URLSafeTimedSerializer
from flask import current_app


def _get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="auth-token")


def generate_auth_token(user):
    return _get_serializer().dumps(user.to_public_dict())
