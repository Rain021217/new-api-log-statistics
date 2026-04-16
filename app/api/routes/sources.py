from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.schemas.common import success_response
from app.schemas.source import (
    SourceConnectionTestRequest,
    SourceImportUriRequest,
    SourceUpsertRequest,
)
from app.services.local_import import scan_local_new_api_sources
from app.services.audit_log import write_audit_event
from app.services.source_registry import (
    delete_source_definition,
    get_runtime_capabilities,
    get_source_registry,
    ping_source_definition,
    save_source_definition,
)

router = APIRouter()


@router.get("")
def list_sources() -> dict:
    registry = get_source_registry()
    return success_response(
        {
            "items": [item.model_dump(mode="json") for item in registry.list_sources()],
            "capabilities": get_runtime_capabilities(),
        }
    )


@router.get("/{source_id}/health")
def source_health(source_id: str) -> dict:
    registry = get_source_registry()
    source = registry.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail=f"Unknown source_id: {source_id}")
    result = ping_source_definition(source)
    return success_response(result.model_dump(mode="json"))


@router.post("/test")
def test_source(payload: SourceConnectionTestRequest) -> dict:
    result = ping_source_definition(payload.to_source_definition())
    return success_response(result.model_dump(mode="json"))


@router.post("")
def create_source(payload: SourceUpsertRequest) -> dict:
    source_public = save_source_definition(payload)
    write_audit_event(
        "source_saved",
        {
            "source_id": source_public.source_id,
            "source_name": source_public.source_name,
            "action": "create_or_upsert",
        },
    )
    return success_response(source_public.model_dump(mode="json"), message="Source saved")


@router.put("/{source_id}")
def update_source(source_id: str, payload: SourceUpsertRequest) -> dict:
    source_public = save_source_definition(payload.model_copy(update={"source_id": source_id}))
    write_audit_event(
        "source_updated",
        {
            "source_id": source_public.source_id,
            "source_name": source_public.source_name,
        },
    )
    return success_response(source_public.model_dump(mode="json"), message="Source updated")


@router.delete("/{source_id}")
def delete_source(source_id: str) -> dict:
    try:
        source_public = delete_source_definition(source_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown source_id: {source_id}")
    write_audit_event(
        "source_deleted",
        {
            "source_id": source_public.source_id,
            "source_name": source_public.source_name,
        },
    )
    return success_response(source_public.model_dump(mode="json"), message="Source deleted")


@router.post("/import-uri")
def import_source_uri(payload: SourceImportUriRequest) -> dict:
    source = payload.to_source_definition()
    result = ping_source_definition(source)
    write_audit_event(
        "source_import_uri_tested",
        {
            "source_id": source.source_id,
            "source_name": source.source_name,
            "ok": result.ok,
        },
    )
    return success_response(
        {
            "source": source.model_dump(mode="json", exclude={"password"}),
            "test_result": result.model_dump(mode="json"),
        }
    )


@router.post("/import-local")
def import_local_sources() -> dict:
    settings = get_settings()
    if not settings.enable_local_import:
        raise HTTPException(status_code=403, detail="Local import is disabled")
    result = scan_local_new_api_sources()
    write_audit_event(
        "source_import_local_scanned",
        {
            "candidate_count": len(result.get("candidates", [])),
            "scan_root_count": len(result.get("scan_roots", [])),
        },
    )
    return success_response(result)
