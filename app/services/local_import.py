from pathlib import Path
from typing import Any

import yaml

from app.core.config import get_settings
from app.schemas.source import SourceDefinition
from app.services.source_registry import ping_source_definition


def _parse_env_file(path: Path) -> dict[str, str]:
    env_map: dict[str, str] = {}
    if not path.exists():
        return env_map
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env_map[key.strip()] = value.strip().strip('"').strip("'")
    return env_map


def _coerce_environment(value: Any) -> dict[str, str]:
    if isinstance(value, dict):
        return {str(key): str(val) for key, val in value.items()}
    if isinstance(value, list):
        result: dict[str, str] = {}
        for item in value:
            if isinstance(item, str) and "=" in item:
                key, val = item.split("=", 1)
                result[key] = val
        return result
    return {}


def _build_source_from_mapping(
    mapping: dict[str, str],
    *,
    source_name: str,
    origin_path: Path,
) -> SourceDefinition | None:
    host = mapping.get("DB_HOST") or mapping.get("MYSQL_HOST")
    port = mapping.get("DB_PORT") or mapping.get("MYSQL_PORT") or "3306"
    database = mapping.get("DB_NAME") or mapping.get("MYSQL_DATABASE")
    user = mapping.get("DB_USER") or mapping.get("MYSQL_USER")
    password = mapping.get("DB_PASSWORD") or mapping.get("MYSQL_PASSWORD")
    if not all([host, database, user, password]):
        return None
    source_id = (
        f"{origin_path.stem}-{source_name}".lower()
        .replace(" ", "-")
        .replace("_", "-")
    )
    return SourceDefinition(
        source_id=source_id,
        source_name=source_name,
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database,
        charset=mapping.get("DB_CHARSET", "utf8mb4"),
        timezone=mapping.get("TZ", "Asia/Shanghai"),
        notes=f"Imported from {origin_path}",
    )


def scan_local_new_api_sources() -> dict[str, Any]:
    settings = get_settings()
    candidates: list[dict[str, Any]] = []
    scanned_paths: list[str] = []

    ignored_dir_names = {
        ".git",
        ".venv",
        "node_modules",
        "__pycache__",
        "archive",
    }

    def iter_candidate_files(root: Path) -> list[Path]:
        matches: list[Path] = []
        root = root.resolve()
        for current_root, dirs, files in __import__("os").walk(root):
            current_path = Path(current_root)
            depth = len(current_path.relative_to(root).parts)
            dirs[:] = [
                item
                for item in dirs
                if item not in ignored_dir_names and depth < settings.local_import_max_depth
            ]
            for file_name in files:
                if file_name in {".env", "docker-compose.yml", "docker-compose.yaml"}:
                    matches.append(current_path / file_name)
        return matches

    for root in settings.local_import_scan_roots:
        if not root.exists():
            continue
        candidate_files = iter_candidate_files(root)
        for path in [item for item in candidate_files if item.name == ".env"]:
            scanned_paths.append(str(path))
            env_map = _parse_env_file(path)
            source = _build_source_from_mapping(
                env_map,
                source_name=f"{path.parent.name} env",
                origin_path=path,
            )
            if source:
                candidates.append(
                    {
                        "origin": str(path),
                        "kind": "env",
                        "source": source.model_dump(mode="json", exclude={"password"}),
                        "has_password": True,
                        "test_result": ping_source_definition(source).model_dump(mode="json"),
                    }
                )

        for path in [
            item
            for item in candidate_files
            if item.name in {"docker-compose.yml", "docker-compose.yaml"}
        ]:
            scanned_paths.append(str(path))
            raw = yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore")) or {}
            services = raw.get("services", {})
            if not isinstance(services, dict):
                continue
            for service_name, service in services.items():
                if not isinstance(service, dict):
                    continue
                env_map = _coerce_environment(service.get("environment"))
                env_file_value = service.get("env_file")
                env_files = env_file_value if isinstance(env_file_value, list) else [env_file_value] if env_file_value else []
                for env_file in env_files:
                    env_path = (path.parent / env_file).resolve()
                    env_map.update(_parse_env_file(env_path))
                source = _build_source_from_mapping(
                    env_map,
                    source_name=f"{path.parent.name}:{service_name}",
                    origin_path=path,
                )
                if source:
                    candidates.append(
                        {
                            "origin": str(path),
                            "kind": "compose",
                            "service": service_name,
                            "source": source.model_dump(mode="json", exclude={"password"}),
                            "has_password": True,
                            "test_result": ping_source_definition(source).model_dump(mode="json"),
                        }
                    )

    dedup: dict[str, dict[str, Any]] = {}
    for item in candidates:
        dedup[item["source"]["source_id"]] = item

    return {
        "scan_roots": [str(path) for path in settings.local_import_scan_roots],
        "scanned_paths": scanned_paths,
        "candidates": list(dedup.values()),
    }
