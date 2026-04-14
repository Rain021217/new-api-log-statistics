from fastapi import APIRouter, Request, Response

from app.core.config import get_settings
from app.schemas.auth import LoginRequest
from app.schemas.common import error_response, success_response
from app.services.audit_log import write_audit_event
from app.services.auth import (
    build_auth_status,
    get_authenticated_username,
    issue_session_token,
    is_auth_enabled,
    verify_credentials,
)

router = APIRouter()


@router.get("/status")
def auth_status(request: Request) -> dict:
    username = get_authenticated_username(request)
    return success_response(
        build_auth_status(authenticated=bool(username), username=username)
    )


@router.post("/login")
def auth_login(payload: LoginRequest, response: Response) -> dict:
    settings = get_settings()
    if not is_auth_enabled():
        return success_response(
            build_auth_status(authenticated=True, username=""),
            message="Authentication is disabled",
        )
    if not verify_credentials(payload.username, payload.password):
        write_audit_event(
            "auth_login_failed",
            {"username": payload.username, "reason": "invalid_credentials"},
        )
        response.status_code = 401
        return error_response("用户名或密码错误", error_type="Unauthorized")

    token = issue_session_token(payload.username)
    response.set_cookie(
        key=settings.auth_session_cookie,
        value=token,
        max_age=settings.auth_session_max_age,
        httponly=True,
        samesite="lax",
        secure=settings.auth_cookie_secure,
        path="/",
    )
    write_audit_event("auth_login_succeeded", {"username": payload.username})
    return success_response(
        build_auth_status(authenticated=True, username=payload.username),
        message="登录成功",
    )


@router.post("/logout")
def auth_logout(request: Request, response: Response) -> dict:
    settings = get_settings()
    username = get_authenticated_username(request)
    response.delete_cookie(settings.auth_session_cookie, path="/")
    if username:
        write_audit_event("auth_logout", {"username": username})
    return success_response(
        build_auth_status(authenticated=False, username=""),
        message="已退出登录",
    )
