from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.export import router as export_router
from app.api.routes.health import router as health_router
from app.api.routes.meta import router as meta_router
from app.api.routes.stats import router as stats_router
from app.api.routes.sources import router as sources_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(export_router, prefix="/export", tags=["export"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(sources_router, prefix="/sources", tags=["sources"])
api_router.include_router(meta_router, prefix="/meta", tags=["meta"])
api_router.include_router(stats_router, prefix="/stats", tags=["stats"])
