from app.core.config import get_settings
from app.db.sql_dialect import get_sql_dialect
from app.db.source_client import execute_query, source_connection
from app.schemas.source import SourceDefinition


def get_options_snapshot(source: SourceDefinition) -> dict:
    dialect = get_sql_dialect(source)
    key_col = dialect.column("key")
    value_col = dialect.column("value")
    query = """
    SELECT
      MAX(CASE WHEN {key_col} = 'general_setting.quota_display_type' THEN {value_col} END) AS quota_display_type,
      MAX(CASE WHEN {key_col} = 'QuotaPerUnit' THEN {value_col} END) AS quota_per_unit,
      MAX(CASE WHEN {key_col} = 'USDExchangeRate' THEN {value_col} END) AS usd_exchange_rate,
      MAX(CASE WHEN {key_col} = 'general_setting.custom_currency_symbol' THEN {value_col} END) AS custom_currency_symbol,
      MAX(CASE WHEN {key_col} = 'general_setting.custom_currency_exchange_rate' THEN {value_col} END) AS custom_currency_exchange_rate
    FROM options
    """.format(key_col=key_col, value_col=value_col)
    settings = get_settings()
    with source_connection(source, connect_timeout=settings.request_timeout_seconds) as conn:
        with conn.cursor() as cursor:
            execute_query(cursor, query, source_id=source.source_id, query_name="meta_options")
            row = cursor.fetchone() or {}
    return {
        "quota_display_type": row.get("quota_display_type") or "",
        "quota_per_unit": row.get("quota_per_unit") or "",
        "usd_exchange_rate": row.get("usd_exchange_rate") or "",
        "custom_currency_symbol": row.get("custom_currency_symbol") or "",
        "custom_currency_exchange_rate": row.get("custom_currency_exchange_rate") or "",
    }


def list_token_names(source: SourceDefinition, limit: int = 200) -> list[dict]:
    query = """
    SELECT token_name, COUNT(*) AS request_count, MAX(created_at) AS latest_created_at
    FROM logs
    WHERE type = 2 AND token_name IS NOT NULL AND token_name <> ''
    GROUP BY token_name
    ORDER BY latest_created_at DESC
    LIMIT %s
    """
    settings = get_settings()
    with source_connection(source, connect_timeout=settings.request_timeout_seconds) as conn:
        with conn.cursor() as cursor:
            execute_query(
                cursor,
                query,
                (limit,),
                source_id=source.source_id,
                query_name="meta_tokens",
            )
            rows = cursor.fetchall() or []
    return rows
