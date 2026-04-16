import os
from functools import lru_cache
from pathlib import Path


class Settings:
    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        self.project_root = project_root
        self.app_title = os.getenv("APP_TITLE", "new-api-log-statistics")
        self.app_version = os.getenv("APP_VERSION", "0.2.0")
        self.app_host = os.getenv("APP_HOST", "0.0.0.0")
        self.app_port = int(os.getenv("APP_PORT", "8080"))
        self.app_env = os.getenv("APP_ENV", "development")
        self.cors_allow_origins = [
            origin.strip()
            for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
            if origin.strip()
        ]
        self.query_cache_ttl = int(os.getenv("QUERY_CACHE_TTL", "300"))
        self.db_pool_size = int(os.getenv("DB_POOL_SIZE", "4"))
        self.request_timeout_seconds = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "5"))
        self.slow_query_threshold_ms = int(os.getenv("SLOW_QUERY_THRESHOLD_MS", "250"))
        self.allow_remote_db = os.getenv("ALLOW_REMOTE_DB", "true").lower() == "true"
        self.default_source_id = os.getenv("DEFAULT_SOURCE_ID", "")
        self.redis_url = os.getenv("REDIS_URL", "")
        self.auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"
        self.auth_username = os.getenv("AUTH_USERNAME", "admin")
        self.auth_password = os.getenv("AUTH_PASSWORD", "")
        self.auth_session_secret = os.getenv(
            "AUTH_SESSION_SECRET",
            "change-this-in-production",
        )
        self.auth_session_cookie = os.getenv(
            "AUTH_SESSION_COOKIE",
            "new_api_log_statistics_session",
        )
        self.auth_session_max_age = int(os.getenv("AUTH_SESSION_MAX_AGE", "43200"))
        self.auth_cookie_secure = (
            os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
        )
        self.auth_allow_basic = (
            os.getenv("AUTH_ALLOW_BASIC", "true").lower() == "true"
        )
        self.auth_public_health = (
            os.getenv("AUTH_PUBLIC_HEALTH", "true").lower() == "true"
        )
        self.source_config_json = os.getenv("SOURCE_CONFIG_JSON", "")
        self.source_config_path = Path(
            os.getenv(
                "SOURCE_CONFIG_PATH",
                str(project_root / "config" / "sources.yml"),
            )
        )
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.enable_local_import = (
            os.getenv("ENABLE_LOCAL_IMPORT", "false").lower() == "true"
        )
        self.local_import_scan_roots = [
            Path(item).expanduser()
            for item in os.getenv(
                "LOCAL_IMPORT_SCAN_ROOTS",
                str(project_root.parent),
            ).split(",")
            if item.strip()
        ]
        self.local_import_max_depth = int(os.getenv("LOCAL_IMPORT_MAX_DEPTH", "3"))
        self.startup_validate_sources = (
            os.getenv("STARTUP_VALIDATE_SOURCES", "true").lower() == "true"
        )
        self.app_log_path = os.getenv(
            "APP_LOG_PATH",
            str(project_root / "runtime" / "app.log"),
        )
        self.access_log_path = os.getenv(
            "ACCESS_LOG_PATH",
            str(project_root / "runtime" / "access.log"),
        )
        self.audit_log_path = os.getenv(
            "AUDIT_LOG_PATH",
            str(project_root / "runtime" / "audit.log"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
