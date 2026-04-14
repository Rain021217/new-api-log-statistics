from urllib.parse import quote_plus

import pymysql

from app.schemas.source import SourceDefinition


def build_mysql_dsn(source: SourceDefinition) -> str:
    password = quote_plus(source.password or "")
    charset = source.charset or "utf8mb4"
    return (
        f"mysql+pymysql://{source.user}:{password}"
        f"@{source.host}:{source.port}/{source.database}?charset={charset}"
    )


def build_mysql_dsn_preview(source: SourceDefinition) -> str:
    charset = source.charset or "utf8mb4"
    return (
        f"mysql+pymysql://{source.user}:***"
        f"@{source.host}:{source.port}/{source.database}?charset={charset}"
    )


def ping_mysql(source: SourceDefinition, timeout_seconds: int = 5) -> None:
    connection = pymysql.connect(
        host=source.host,
        port=source.port,
        user=source.user,
        password=source.password,
        database=source.database,
        charset=source.charset or "utf8mb4",
        connect_timeout=timeout_seconds,
        read_timeout=timeout_seconds,
        write_timeout=timeout_seconds,
        cursorclass=pymysql.cursors.Cursor,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    finally:
        connection.close()


def inspect_mysql_source(
    source: SourceDefinition,
    timeout_seconds: int = 5,
) -> dict:
    connection = pymysql.connect(
        host=source.host,
        port=source.port,
        user=source.user,
        password=source.password,
        database=source.database,
        charset=source.charset or "utf8mb4",
        connect_timeout=timeout_seconds,
        read_timeout=timeout_seconds,
        write_timeout=timeout_seconds,
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                  AND table_name IN ('logs', 'options', 'tokens', 'channels')
                """,
                (source.database,),
            )
            found_tables = {row["table_name"] for row in cursor.fetchall() or []}

            cursor.execute(
                """
                SELECT `key`, `value`
                FROM options
                WHERE `key` IN (
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
                SELECT DEFAULT_CHARACTER_SET_NAME AS charset_name
                FROM information_schema.SCHEMATA
                WHERE SCHEMA_NAME = %s
                """,
                (source.database,),
            )
            schema_info = cursor.fetchone() or {}

            cursor.execute("SELECT @@session.time_zone AS session_time_zone, @@system_time_zone AS system_time_zone")
            timezone_info = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT
                  id,
                  JSON_UNQUOTE(JSON_EXTRACT(other, '$.request_path')) AS request_path,
                  JSON_UNQUOTE(JSON_EXTRACT(other, '$.model_ratio')) AS model_ratio,
                  JSON_UNQUOTE(JSON_EXTRACT(other, '$.completion_ratio')) AS completion_ratio
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
                "charset": schema_info.get("charset_name", ""),
                "session_time_zone": timezone_info.get("session_time_zone", ""),
                "system_time_zone": timezone_info.get("system_time_zone", ""),
            },
            "log_sample": latest_log_sample,
            "compatible": len(missing_required_tables) == 0,
        }
    finally:
        connection.close()
