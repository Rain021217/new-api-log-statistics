from fastapi import APIRouter, HTTPException, Query

from app.repositories.stats_repository import (
    get_token_cost_breakdown,
    get_token_cost_charts,
    get_token_cost_details,
    get_token_cost_summary,
    get_token_cost_trend,
)
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


def _build_filters(
    token_name: str = "",
    model_name: str = "",
    username: str = "",
    group_name: str = "",
    ip: str = "",
    channel_id: int | None = None,
    request_id: str = "",
    start_time: int | None = None,
    end_time: int | None = None,
) -> dict:
    return {
        "token_name": token_name.strip(),
        "model_name": model_name.strip(),
        "username": username.strip(),
        "group_name": group_name.strip(),
        "ip": ip.strip(),
        "channel_id": channel_id,
        "request_id": request_id.strip(),
        "start_time": start_time,
        "end_time": end_time,
    }


@router.get("/token-cost-summary")
def token_cost_summary(
    source_id: str = Query(...),
    token_name: str = Query("", description="Exact token name"),
    model_name: str = Query(""),
    username: str = Query(""),
    group_name: str = Query(""),
    ip: str = Query(""),
    channel_id: int | None = Query(None),
    request_id: str = Query(""),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
) -> dict:
    source = _require_source(source_id)
    filters = _build_filters(
        token_name,
        model_name,
        username,
        group_name,
        ip,
        channel_id,
        request_id,
        start_time,
        end_time,
    )
    return success_response(
        query_cache.get_or_set(
            namespace=f"{source_id}:stats:summary",
            payload=filters,
            ttl_seconds=120,
            loader=lambda: get_token_cost_summary(source, filters),
        )
    )


@router.get("/token-cost-details")
def token_cost_details(
    source_id: str = Query(...),
    token_name: str = Query("", description="Exact token name"),
    model_name: str = Query(""),
    username: str = Query(""),
    group_name: str = Query(""),
    ip: str = Query(""),
    channel_id: int | None = Query(None),
    request_id: str = Query(""),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    order_by: str = Query("created_at"),
    order_dir: str = Query("desc"),
) -> dict:
    source = _require_source(source_id)
    filters = _build_filters(
        token_name,
        model_name,
        username,
        group_name,
        ip,
        channel_id,
        request_id,
        start_time,
        end_time,
    )
    return success_response(
        query_cache.get_or_set(
            namespace=f"{source_id}:stats:details",
            payload={
                **filters,
                "page": page,
                "page_size": page_size,
                "order_by": order_by,
                "order_dir": order_dir,
            },
            ttl_seconds=120,
            loader=lambda: get_token_cost_details(
                source,
                filters,
                page=page,
                page_size=page_size,
                order_by=order_by,
                order_dir=order_dir,
            ),
        )
    )


@router.get("/token-cost-trend")
def token_cost_trend(
    source_id: str = Query(...),
    token_name: str = Query("", description="Exact token name"),
    model_name: str = Query(""),
    username: str = Query(""),
    group_name: str = Query(""),
    ip: str = Query(""),
    channel_id: int | None = Query(None),
    request_id: str = Query(""),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    granularity: str | None = Query(None),
) -> dict:
    source = _require_source(source_id)
    filters = _build_filters(
        token_name,
        model_name,
        username,
        group_name,
        ip,
        channel_id,
        request_id,
        start_time,
        end_time,
    )
    return success_response(
        query_cache.get_or_set(
            namespace=f"{source_id}:stats:trend",
            payload={**filters, "granularity": granularity or ""},
            ttl_seconds=120,
            loader=lambda: get_token_cost_trend(source, filters, granularity=granularity),
        )
    )


@router.get("/token-cost-breakdown")
def token_cost_breakdown(
    source_id: str = Query(...),
    token_name: str = Query("", description="Exact token name"),
    model_name: str = Query(""),
    username: str = Query(""),
    group_name: str = Query(""),
    ip: str = Query(""),
    channel_id: int | None = Query(None),
    request_id: str = Query(""),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    top_n: int = Query(10, ge=1, le=50),
) -> dict:
    source = _require_source(source_id)
    filters = _build_filters(
        token_name,
        model_name,
        username,
        group_name,
        ip,
        channel_id,
        request_id,
        start_time,
        end_time,
    )
    return success_response(
        query_cache.get_or_set(
            namespace=f"{source_id}:stats:breakdown",
            payload={**filters, "top_n": top_n},
            ttl_seconds=120,
            loader=lambda: get_token_cost_breakdown(source, filters, top_n=top_n),
        )
    )


@router.get("/token-cost-charts")
def token_cost_charts(
    source_id: str = Query(...),
    token_name: str = Query("", description="Exact token name"),
    model_name: str = Query(""),
    username: str = Query(""),
    group_name: str = Query(""),
    ip: str = Query(""),
    channel_id: int | None = Query(None),
    request_id: str = Query(""),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    granularity: str | None = Query(None),
    top_n: int = Query(10, ge=1, le=50),
) -> dict:
    source = _require_source(source_id)
    filters = _build_filters(
        token_name,
        model_name,
        username,
        group_name,
        ip,
        channel_id,
        request_id,
        start_time,
        end_time,
    )
    return success_response(
        query_cache.get_or_set(
            namespace=f"{source_id}:stats:charts",
            payload={**filters, "granularity": granularity or "", "top_n": top_n},
            ttl_seconds=120,
            loader=lambda: get_token_cost_charts(
                source,
                filters,
                granularity=granularity,
                top_n=top_n,
            ),
        )
    )
