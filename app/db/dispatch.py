from dataclasses import dataclass
from typing import Callable

from app.db.mysql import (
    build_mysql_dsn_preview,
    create_mysql_connection,
    inspect_mysql_source,
    ping_mysql,
    validate_mysql_connection,
)
from app.db.postgres import (
    build_postgres_dsn_preview,
    create_postgres_connection,
    inspect_postgres_source,
    ping_postgres,
    validate_postgres_connection,
)
from app.schemas.source import SourceDefinition


@dataclass(frozen=True)
class SourceDriver:
    connect: Callable
    validate: Callable
    ping: Callable
    inspect: Callable
    dsn_preview: Callable


_DRIVERS = {
    "mysql": SourceDriver(
        connect=create_mysql_connection,
        validate=validate_mysql_connection,
        ping=ping_mysql,
        inspect=inspect_mysql_source,
        dsn_preview=build_mysql_dsn_preview,
    ),
    "mariadb": SourceDriver(
        connect=create_mysql_connection,
        validate=validate_mysql_connection,
        ping=ping_mysql,
        inspect=inspect_mysql_source,
        dsn_preview=build_mysql_dsn_preview,
    ),
    "postgres": SourceDriver(
        connect=create_postgres_connection,
        validate=validate_postgres_connection,
        ping=ping_postgres,
        inspect=inspect_postgres_source,
        dsn_preview=build_postgres_dsn_preview,
    ),
}


def get_source_driver(source: SourceDefinition) -> SourceDriver:
    try:
        return _DRIVERS[source.db_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported db_type: {source.db_type}") from exc
