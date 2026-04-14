import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.core.config import get_settings
from app.db.mysql import build_mysql_dsn_preview, inspect_mysql_source, ping_mysql
from app.schemas.source import (
    SourceDefinition,
    SourcePingResult,
    SourcePublic,
    SourceUpsertRequest,
)
from app.services.audit_log import write_audit_event

logger = logging.getLogger(__name__)


def _load_sources_from_json(raw: str) -> list[SourceDefinition]:
    if not raw.strip():
        return []
    parsed = json.loads(raw)
    items = parsed.get("sources", parsed) if isinstance(parsed, dict) else parsed
    return [SourceDefinition(**item) for item in items]


def _load_sources_from_file(path: Path) -> list[SourceDefinition]:
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = raw.get("sources", raw) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        raise ValueError(f"Invalid sources config format in {path}")
    return [SourceDefinition(**item) for item in items]


class SourceRegistry:
    def __init__(self, sources: list[SourceDefinition]) -> None:
        self._sources = {item.source_id: item for item in sources}

    def list_sources(self) -> list[SourcePublic]:
        return [
            SourcePublic.from_definition(item)
            for item in sorted(
                [item for item in self._sources.values() if item.enabled],
                key=lambda x: x.source_name.lower(),
            )
        ]

    def get_source(self, source_id: str) -> SourceDefinition | None:
        return self._sources.get(source_id)

    def list_source_definitions(self) -> list[SourceDefinition]:
        return sorted(self._sources.values(), key=lambda x: x.source_name.lower())


def ping_source_definition(source: SourceDefinition) -> SourcePingResult:
    settings = get_settings()
    try:
        ping_mysql(source, timeout_seconds=settings.request_timeout_seconds)
        checks = inspect_mysql_source(source, timeout_seconds=settings.request_timeout_seconds)
        message = "Connection successful"
        ok = True
    except Exception as exc:  # pragma: no cover - runtime diagnostic path
        logger.warning("Source ping failed for %s: %s", source.source_id, exc)
        message = str(exc)
        ok = False
        checks = {"reachable": False, "compatible": False}
        write_audit_event(
            "source_ping_failed",
            {
                "source_id": source.source_id,
                "source_name": source.source_name,
                "message": message,
            },
        )
    return SourcePingResult(
        ok=ok,
        source_id=source.source_id,
        source_name=source.source_name,
        message=message,
        dsn_preview=build_mysql_dsn_preview(source),
        checks=checks,
    )


def get_runtime_capabilities() -> dict[str, Any]:
    settings = get_settings()
    return {
        "allow_remote_db": settings.allow_remote_db,
        "enable_local_import": settings.enable_local_import,
        "source_config_path": str(settings.source_config_path),
        "source_config_writable": not bool(settings.source_config_json),
    }


@lru_cache(maxsize=1)
def get_source_registry() -> SourceRegistry:
    settings = get_settings()
    sources: list[SourceDefinition] = []
    if settings.source_config_json:
        sources.extend(_load_sources_from_json(settings.source_config_json))
    else:
        sources.extend(_load_sources_from_file(settings.source_config_path))
    return SourceRegistry(sources)


def reset_source_registry_cache() -> None:
    get_source_registry.cache_clear()


def _write_sources_to_file(path: Path, sources: list[SourceDefinition]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "sources": [item.model_dump(mode="json") for item in sources],
    }
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def save_source_definition(payload: SourceUpsertRequest) -> SourcePublic:
    settings = get_settings()
    if settings.source_config_json:
        raise ValueError("SOURCE_CONFIG_JSON mode is read-only and cannot persist changes")

    registry = get_source_registry()
    existing = registry.get_source(payload.source_id or "")
    source = payload.to_source_definition(
        existing=existing,
        require_password=existing is None,
    )

    items = registry.list_source_definitions()
    updated = False
    for index, item in enumerate(items):
        if item.source_id == source.source_id:
            items[index] = source
            updated = True
            break
    if not updated:
        items.append(source)

    _write_sources_to_file(settings.source_config_path, items)
    reset_source_registry_cache()
    return SourcePublic.from_definition(source)


def validate_enabled_sources() -> list[dict[str, Any]]:
    registry = get_source_registry()
    results: list[dict[str, Any]] = []
    for source in registry.list_source_definitions():
        if not source.enabled:
            continue
        result = ping_source_definition(source)
        results.append(result.model_dump(mode="json"))
    return results
