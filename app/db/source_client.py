from collections import defaultdict, deque
from contextlib import contextmanager
import logging
from threading import Lock
import time
from typing import Any, Deque, Iterator

from app.core.config import get_settings
from app.db.dispatch import get_source_driver
from app.schemas.source import SourceDefinition

logger = logging.getLogger(__name__)


class _SourcePoolManager:
    def __init__(self) -> None:
        self._pools: dict[tuple[str, str], Deque[Any]] = defaultdict(deque)
        self._locks: dict[tuple[str, str], Lock] = defaultdict(Lock)

    def _make_connection(
        self,
        source: SourceDefinition,
        *,
        connect_timeout: int,
    ):
        driver = get_source_driver(source)
        return driver.connect(
            source,
            timeout_seconds=connect_timeout,
            dict_rows=True,
            autocommit=True,
        )

    def acquire(
        self,
        source: SourceDefinition,
        *,
        connect_timeout: int,
    ):
        pool_key = (source.db_type, source.source_id)
        pool = self._pools[pool_key]
        lock = self._locks[pool_key]
        driver = get_source_driver(source)
        with lock:
            while pool:
                connection = pool.pop()
                try:
                    driver.validate(connection)
                    return connection
                except Exception:
                    try:
                        connection.close()
                    except Exception:
                        pass
            return self._make_connection(source, connect_timeout=connect_timeout)

    def release(self, source: SourceDefinition, connection) -> None:
        settings = get_settings()
        pool_key = (source.db_type, source.source_id)
        pool = self._pools[pool_key]
        lock = self._locks[pool_key]
        driver = get_source_driver(source)
        with lock:
            if len(pool) < settings.db_pool_size:
                try:
                    driver.validate(connection)
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
) -> Iterator[Any]:
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
