from fastapi import APIRouter, HTTPException, Query

from app.repositories.meta_repository import get_options_snapshot, list_token_names
from app.schemas.common import success_response
from app.services.query_cache import query_cache
from app.services.source_registry import get_source_registry

router = APIRouter()


def _require_source(source_id: str):
    registry = get_source_registry()
    source = registry.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail=f"Unknown source_id: {source_id}")
    return source


@router.get("/options")
def meta_options(source_id: str = Query(...)) -> dict:
    source = _require_source(source_id)
    return success_response(
        query_cache.get_or_set(
            namespace=f"{source_id}:meta:options",
            payload={"source_id": source_id},
            ttl_seconds=60,
            loader=lambda: get_options_snapshot(source),
        )
    )


@router.get("/tokens")
def meta_tokens(source_id: str = Query(...), limit: int = Query(200, ge=1, le=500)) -> dict:
    source = _require_source(source_id)
    items = query_cache.get_or_set(
        namespace=f"{source_id}:meta:tokens",
        payload={"source_id": source_id, "limit": limit},
        ttl_seconds=60,
        loader=lambda: list_token_names(source, limit=limit),
    )
    return success_response({"items": items})
