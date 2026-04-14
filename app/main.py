import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging
from app.services.auth import (
    build_auth_status,
    get_authenticated_username,
    is_auth_enabled,
    is_public_path,
    validate_auth_settings,
)
from app.services.source_registry import validate_enabled_sources

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title=settings.app_title, version=settings.app_version)
install_exception_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")

web_root = settings.project_root / "web"
app.mount("/static", StaticFiles(directory=web_root), name="static")


@app.middleware("http")
async def auth_guard_middleware(request, call_next):
    if not is_auth_enabled() or is_public_path(request.url.path):
        return await call_next(request)
    username = get_authenticated_username(request)
    if username:
        request.state.authenticated_username = username
        return await call_next(request)
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=401,
            content={
                "ok": False,
                "message": "Authentication required",
                "error": {
                    "type": "Unauthorized",
                    **build_auth_status(authenticated=False, username=""),
                },
            },
        )
    return JSONResponse(
        status_code=401,
        content={
            "ok": False,
            "message": "Authentication required",
            "error": {"type": "Unauthorized"},
        },
    )


@app.middleware("http")
async def access_log_middleware(request, call_next):
    started_at = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logging.getLogger("access").info(
        "method=%s path=%s status=%s elapsed_ms=%.2f client=%s",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        getattr(request.client, "host", "-"),
    )
    return response


@app.on_event("startup")
def startup_validation() -> None:
    validate_auth_settings()
    if not settings.startup_validate_sources:
        return
    try:
        results = validate_enabled_sources()
        for result in results:
            logger.info(
                "source_startup_validation source_id=%s ok=%s compatible=%s message=%s",
                result.get("source_id"),
                result.get("ok"),
                result.get("checks", {}).get("compatible"),
                result.get("message"),
            )
    except Exception as exc:  # pragma: no cover - startup diagnostics
        logger.warning("startup source validation failed: %s", exc)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(web_root / "index.html")
