from urllib.parse import quote_plus

import psycopg
from psycopg.rows import dict_row

from app.schemas.source import SourceDefinition


def create_postgres_connection(
    source: SourceDefinition,
    *,
    timeout_seconds: int = 5,
    dict_rows: bool = True,
    autocommit: bool = True,
):
    connection = psycopg.connect(
        host=source.host,
        port=source.port,
        user=source.user,
        password=source.password,
        dbname=source.database,
        connect_timeout=timeout_seconds,
        autocommit=autocommit,
        row_factory=dict_row if dict_rows else None,
    )
    return connection


def validate_postgres_connection(connection) -> None:
    if getattr(connection, "closed", False):
        raise RuntimeError("connection is closed")
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()


def build_postgres_dsn(source: SourceDefinition) -> str:
    password = quote_plus(source.password or "")
    return (
        f"postgresql+psycopg://{source.user}:{password}"
        f"@{source.host}:{source.port}/{source.database}"
    )


def build_postgres_dsn_preview(source: SourceDefinition) -> str:
    return (
        f"postgresql+psycopg://{source.user}:***"
        f"@{source.host}:{source.port}/{source.database}"
    )


def ping_postgres(source: SourceDefinition, timeout_seconds: int = 5) -> None:
    connection = create_postgres_connection(
        source,
        timeout_seconds=timeout_seconds,
        dict_rows=False,
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    finally:
        connection.close()


def inspect_postgres_source(
    source: SourceDefinition,
    timeout_seconds: int = 5,
) -> dict:
    connection = create_postgres_connection(
        source,
        timeout_seconds=timeout_seconds,
        dict_rows=True,
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_catalog = %s
                  AND table_schema = current_schema()
                  AND table_name IN ('logs', 'options', 'tokens', 'channels')
                """,
                (source.database,),
            )
            found_tables = {row["table_name"] for row in cursor.fetchall() or []}

            options = {}
            if "options" in found_tables:
                cursor.execute(
                    """
                    SELECT "key", "value"
                    FROM options
                    WHERE "key" IN (
                      'QuotaPerUnit',
                      'USDExchangeRate',
                      'general_setting.quota_display_type',
                      'general_setting.custom_currency_symbol',
                      'general_setting.custom_currency_exchange_rate'
                    )
                    """
                )
                options = {row["key"]: row["value"] for row in cursor.fetchall() or []}

            cursor.execute(
                """
                SELECT
                  current_schema() AS schema_name,
                  current_setting('server_encoding') AS charset_name,
                  current_setting('TimeZone') AS session_time_zone
                """
            )
            database_info = cursor.fetchone() or {}

            latest_log_sample = {}
            if "logs" in found_tables:
                cursor.execute(
                    """
                    SELECT
                      id,
                      (other::jsonb ->> 'request_path') AS request_path,
                      (other::jsonb ->> 'model_ratio') AS model_ratio,
                      (other::jsonb ->> 'completion_ratio') AS completion_ratio
                    FROM logs
                    WHERE type = 2
                    ORDER BY id DESC
                    LIMIT 1
                    """
                )
                latest_log_sample = cursor.fetchone() or {}

        required_tables = {"logs", "options"}
        optional_tables = {"tokens", "channels"}
        missing_required_tables = sorted(required_tables - found_tables)

        return {
            "reachable": True,
            "tables": {
                "found": sorted(found_tables),
                "missing_required": missing_required_tables,
                "missing_optional": sorted(optional_tables - found_tables),
            },
            "options": {
                "quota_per_unit": options.get("QuotaPerUnit", ""),
                "usd_exchange_rate": options.get("USDExchangeRate", ""),
                "quota_display_type": options.get("general_setting.quota_display_type", ""),
                "custom_currency_symbol": options.get("general_setting.custom_currency_symbol", ""),
                "custom_currency_exchange_rate": options.get("general_setting.custom_currency_exchange_rate", ""),
            },
            "database": {
                "charset": database_info.get("charset_name", ""),
                "session_time_zone": database_info.get("session_time_zone", ""),
                "system_time_zone": database_info.get("session_time_zone", ""),
                "schema_name": database_info.get("schema_name", ""),
            },
            "log_sample": latest_log_sample,
            "compatible": len(missing_required_tables) == 0,
        }
    finally:
        connection.close()
