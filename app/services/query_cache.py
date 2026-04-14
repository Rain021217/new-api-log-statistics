import json
import logging
import time
from hashlib import sha1
from threading import Lock
from typing import Any, Callable

from app.core.config import get_settings

try:
    import redis as redis_lib
except Exception:  # pragma: no cover - optional runtime dependency
    redis_lib = None

logger = logging.getLogger(__name__)


class QueryCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()
        self._redis_client = None
        self._backend_name = "memory"

    def _make_key(self, namespace: str, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        digest = sha1(raw.encode("utf-8")).hexdigest()
        return f"{namespace}:{digest}"

    def _get_redis_client(self):
        if self._redis_client is not None:
            return self._redis_client
        settings = get_settings()
        if not settings.redis_url or redis_lib is None:
            self._backend_name = "memory"
            return None
        try:
            self._redis_client = redis_lib.from_url(settings.redis_url, decode_responses=True)
            self._redis_client.ping()
            self._backend_name = "redis"
            logger.info("query_cache_backend backend=redis")
            return self._redis_client
        except Exception:
            self._redis_client = None
            self._backend_name = "memory"
            return None

    def get_or_set(
        self,
        *,
        namespace: str,
        payload: dict[str, Any],
        ttl_seconds: int,
        loader: Callable[[], Any],
    ) -> Any:
        key = self._make_key(namespace, payload)
        redis_client = self._get_redis_client()
        if redis_client is not None:
            cached = redis_client.get(key)
            if cached is not None:
                return json.loads(cached)
            value = loader()
            redis_client.setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False, default=str))
            return value

        now = time.time()
        with self._lock:
            cached = self._store.get(key)
            if cached and cached[0] > now:
                return cached[1]

        value = loader()
        with self._lock:
            self._store[key] = (now + ttl_seconds, value)
        return value

    def clear_all(self) -> None:
        redis_client = self._get_redis_client()
        if redis_client is not None:
            redis_client.flushdb()
            return
        with self._lock:
            self._store.clear()

    def get_backend_name(self) -> str:
        self._get_redis_client()
        return self._backend_name


query_cache = QueryCache()
