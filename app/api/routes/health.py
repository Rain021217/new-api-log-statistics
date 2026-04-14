from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.schemas.common import success_response
from app.services.auth import build_auth_status, get_authenticated_username
from app.services.query_cache import query_cache

router = APIRouter()


@router.get("")
def get_health(request: Request) -> dict:
    settings = get_settings()
    username = get_authenticated_username(request)
    return success_response(
        {
            "service": settings.app_title,
            "version": settings.app_version,
            "time_utc": datetime.now(timezone.utc).isoformat(),
            "cache_backend": query_cache.get_backend_name(),
            "auth": build_auth_status(authenticated=bool(username), username=username),
        }
    )
