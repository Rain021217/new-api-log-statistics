from collections import defaultdict, deque
from contextlib import contextmanager
import logging
from threading import Lock
import time
from typing import Deque, Iterator

import pymysql
from pymysql.cursors import DictCursor

from app.core.config import get_settings
from app.schemas.source import SourceDefinition

logger = logging.getLogger(__name__)


class _SourcePoolManager:
    def __init__(self) -> None:
        self._pools: dict[str, Deque[pymysql.connections.Connection]] = defaultdict(deque)
        self._locks: dict[str, Lock] = defaultdict(Lock)

    def _make_connection(
        self,
        source: SourceDefinition,
        *,
        connect_timeout: int,
    ) -> pymysql.connections.Connection:
        return pymysql.connect(
            host=source.host,
            port=source.port,
            user=source.user,
            password=source.password,
            database=source.database,
            charset=source.charset or "utf8mb4",
            connect_timeout=connect_timeout,
            read_timeout=connect_timeout,
            write_timeout=connect_timeout,
            cursorclass=DictCursor,
            autocommit=True,
        )

    def acquire(
        self,
        source: SourceDefinition,
        *,
        connect_timeout: int,
    ) -> pymysql.connections.Connection:
        settings = get_settings()
        pool = self._pools[source.source_id]
        lock = self._locks[source.source_id]
        with lock:
            while pool:
                connection = pool.pop()
                try:
                    connection.ping(reconnect=True)
                    return connection
                except Exception:
                    try:
                        connection.close()
                    except Exception:
                        pass
            return self._make_connection(source, connect_timeout=connect_timeout)

    def release(self, source: SourceDefinition, connection: pymysql.connections.Connection) -> None:
        settings = get_settings()
        pool = self._pools[source.source_id]
        lock = self._locks[source.source_id]
        with lock:
            if len(pool) < settings.db_pool_size:
                try:
                    connection.ping(reconnect=True)
                    pool.append(connection)
                    return
                except Exception:
                    pass
        try:
            connection.close()
        except Exception:
            pass


_POOL_MANAGER = _SourcePoolManager()


@contextmanager
def source_connection(
    source: SourceDefinition,
    *,
    connect_timeout: int = 5,
) -> Iterator[pymysql.connections.Connection]:
    connection = _POOL_MANAGER.acquire(source, connect_timeout=connect_timeout)
    try:
        yield connection
    finally:
        _POOL_MANAGER.release(source, connection)


def execute_query(
    cursor,
    query: str,
    params=None,
    *,
    source_id: str,
    query_name: str,
):
    settings = get_settings()
    started_at = time.perf_counter()
    cursor.execute(query, params)
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    if elapsed_ms >= settings.slow_query_threshold_ms:
        logger.warning(
            "slow_query source_id=%s query_name=%s elapsed_ms=%.2f",
            source_id,
            query_name,
            elapsed_ms,
        )
    return elapsed_ms
