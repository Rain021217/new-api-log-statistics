from dataclasses import dataclass

from app.schemas.source import SourceDefinition


@dataclass(frozen=True)
class SqlDialect:
    name: str
    decimal_type: str
    bigint_type: str
    text_type: str
    identifier_quote: str

    def ident(self, name: str) -> str:
        quote = self.identifier_quote
        return f"{quote}{name}{quote}"

    def column(self, name: str, alias: str = "") -> str:
        if alias:
            return f"{alias}.{self.ident(name)}"
        return self.ident(name)

    def json_text(self, column_expr: str, key: str) -> str:
        if self.name == "postgres":
            return f"(({column_expr})::jsonb ->> '{key}')"
        return f"JSON_UNQUOTE(JSON_EXTRACT({column_expr}, '$.{key}'))"

    def cast_decimal(self, expr: str, precision: str = "20,6") -> str:
        return f"CAST({expr} AS {self.decimal_type.format(precision=precision)})"

    def cast_decimal_or_default(
        self,
        text_expr: str,
        *,
        default: str = "0",
        precision: str = "20,6",
    ) -> str:
        return self.cast_decimal(
            f"COALESCE(NULLIF({text_expr}, ''), '{default}')",
            precision=precision,
        )

    def cast_bigint(self, expr: str) -> str:
        return f"CAST({expr} AS {self.bigint_type})"

    def cast_bigint_or_default(self, text_expr: str, *, default: str = "0") -> str:
        return self.cast_bigint(f"COALESCE(NULLIF({text_expr}, ''), '{default}')")

    def cast_text(self, expr: str) -> str:
        return f"CAST({expr} AS {self.text_type})"

    def format_timestamp(self, epoch_expr: str) -> str:
        if self.name == "postgres":
            return f"TO_TIMESTAMP({epoch_expr})"
        return f"FROM_UNIXTIME({epoch_expr})"

    def date_from_epoch(self, epoch_expr: str) -> str:
        if self.name == "postgres":
            return f"DATE(TO_TIMESTAMP({epoch_expr}))"
        return f"DATE(FROM_UNIXTIME({epoch_expr}))"

    def bucket_expressions(self, granularity: str, created_at_expr: str = "created_at") -> tuple[str, str]:
        timestamp_expr = self.format_timestamp(created_at_expr)
        if self.name == "postgres":
            if granularity == "hour":
                return (
                    f"TO_CHAR(DATE_TRUNC('hour', {timestamp_expr}), 'YYYY-MM-DD HH24:00')",
                    f"EXTRACT(EPOCH FROM DATE_TRUNC('hour', {timestamp_expr}))",
                )
            if granularity == "week":
                return (
                    f"TO_CHAR(DATE_TRUNC('week', {timestamp_expr}), 'IYYY-\"W\"IW')",
                    f"EXTRACT(EPOCH FROM DATE_TRUNC('week', {timestamp_expr}))",
                )
            return (
                f"TO_CHAR(DATE_TRUNC('day', {timestamp_expr}), 'YYYY-MM-DD')",
                f"EXTRACT(EPOCH FROM DATE_TRUNC('day', {timestamp_expr}))",
            )

        if granularity == "hour":
            return (
                "CONCAT("
                "YEAR(FROM_UNIXTIME(created_at)), '-', "
                "LPAD(MONTH(FROM_UNIXTIME(created_at)), 2, '0'), '-', "
                "LPAD(DAY(FROM_UNIXTIME(created_at)), 2, '0'), ' ', "
                "LPAD(HOUR(FROM_UNIXTIME(created_at)), 2, '0'), ':00'"
                ")",
                "UNIX_TIMESTAMP("
                "TIMESTAMP(DATE(FROM_UNIXTIME(created_at)), MAKETIME(HOUR(FROM_UNIXTIME(created_at)), 0, 0))"
                ")",
            )
        if granularity == "week":
            return (
                "CONCAT(YEAR(FROM_UNIXTIME(created_at)), '-W', LPAD(WEEK(FROM_UNIXTIME(created_at), 3), 2, '0'))",
                "MIN(created_at)",
            )
        return (
            "CONCAT("
            "YEAR(FROM_UNIXTIME(created_at)), '-', "
            "LPAD(MONTH(FROM_UNIXTIME(created_at)), 2, '0'), '-', "
            "LPAD(DAY(FROM_UNIXTIME(created_at)), 2, '0')"
            ")",
            "UNIX_TIMESTAMP(DATE(FROM_UNIXTIME(created_at)))",
        )


MYSQL_DIALECT = SqlDialect(
    name="mysql",
    decimal_type="DECIMAL({precision})",
    bigint_type="SIGNED",
    text_type="CHAR",
    identifier_quote="`",
)

POSTGRES_DIALECT = SqlDialect(
    name="postgres",
    decimal_type="NUMERIC({precision})",
    bigint_type="BIGINT",
    text_type="TEXT",
    identifier_quote='"',
)


def get_sql_dialect(source: SourceDefinition) -> SqlDialect:
    if source.db_type == "postgres":
        return POSTGRES_DIALECT
    return MYSQL_DIALECT
