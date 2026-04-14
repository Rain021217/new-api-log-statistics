from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time

from fastapi import Request

from app.core.config import get_settings

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {
    "/",
    "/favicon.ico",
    "/api/auth/login",
    "/api/auth/logout",
    "/api/auth/status",
}
PUBLIC_PREFIXES = ("/static/",)


def is_auth_enabled() -> bool:
    settings = get_settings()
    return settings.auth_enabled


def validate_auth_settings() -> None:
    settings = get_settings()
    if not settings.auth_enabled:
        return
    if not settings.auth_password:
        raise RuntimeError("AUTH_ENABLED=true requires AUTH_PASSWORD to be set")
    if settings.auth_session_secret == "change-this-in-production":
        logger.warning("AUTH_SESSION_SECRET is using the default placeholder value")


def build_auth_status(*, authenticated: bool, username: str = "") -> dict:
    settings = get_settings()
    return {
        "enabled": settings.auth_enabled,
        "authenticated": authenticated,
        "username": username,
        "allow_basic": settings.auth_allow_basic,
        "public_health": settings.auth_public_health,
    }


def _signature(payload: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def issue_session_token(username: str) -> str:
    settings = get_settings()
    expires_at = int(time.time()) + settings.auth_session_max_age
    payload = f"{username}|{expires_at}"
    signature = _signature(payload, settings.auth_session_secret)
    token = f"{payload}|{signature}"
    return base64.urlsafe_b64encode(token.encode("utf-8")).decode("ascii")


def read_session_token(token: str) -> str:
    settings = get_settings()
    if not token:
        return ""
    try:
        decoded = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        username, expires_at_raw, signature = decoded.rsplit("|", 2)
        payload = f"{username}|{expires_at_raw}"
        if not hmac.compare_digest(signature, _signature(payload, settings.auth_session_secret)):
            return ""
        if int(expires_at_raw) < int(time.time()):
            return ""
        return username
    except Exception:
        return ""


def verify_credentials(username: str, password: str) -> bool:
    settings = get_settings()
    if not settings.auth_enabled:
        return False
    return hmac.compare_digest(username, settings.auth_username) and hmac.compare_digest(
        password,
        settings.auth_password,
    )


def _decode_basic_auth(request: Request) -> tuple[str, str]:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Basic "):
        return "", ""
    encoded = header[6:].strip()
    try:
        raw = base64.b64decode(encoded).decode("utf-8")
    except Exception:
        return "", ""
    if ":" not in raw:
        return "", ""
    username, password = raw.split(":", 1)
    return username, password


def get_authenticated_username(request: Request) -> str:
    settings = get_settings()
    if not settings.auth_enabled:
        return ""
    cookie_token = request.cookies.get(settings.auth_session_cookie, "")
    username = read_session_token(cookie_token)
    if username:
        return username
    if settings.auth_allow_basic:
        basic_user, basic_password = _decode_basic_auth(request)
        if verify_credentials(basic_user, basic_password):
            return basic_user
    return ""


def is_public_path(path: str) -> bool:
    settings = get_settings()
    if path in PUBLIC_PATHS:
        return True
    if path.startswith(PUBLIC_PREFIXES):
        return True
    if settings.auth_public_health and path == "/api/health":
        return True
    return False
