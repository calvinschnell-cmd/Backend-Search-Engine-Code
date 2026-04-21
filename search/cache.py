from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class CacheEntry(Generic[T]):
    value: T
    expires_at: datetime


class TTLCache(Generic[T]):
    def __init__(self, ttl_seconds: int = 180, max_size: int = 256) -> None:
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._lock = Lock()
        self._data: dict[str, CacheEntry[T]] = {}

    def get(self, key: str) -> T | None:
        now = datetime.now(timezone.utc)
        with self._lock:
            entry = self._data.get(key)
            if not entry:
                return None
            if entry.expires_at <= now:
                self._data.pop(key, None)
                return None
            return entry.value

    def set(self, key: str, value: T) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            if len(self._data) >= self._max_size:
                oldest_key = min(self._data, key=lambda k: self._data[k].expires_at)
                self._data.pop(oldest_key, None)
            self._data[key] = CacheEntry(value=value, expires_at=now + timedelta(seconds=self._ttl))
