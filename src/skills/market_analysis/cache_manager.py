from __future__ import annotations


from collections import OrderedDict

import functools

import threading

import time

from typing import Any, Callable, Dict, Optional, Tuple


class CacheManager:

    def __init__(self, maxsize: int = 2048) -> None:

        self._maxsize = int(maxsize) if int(maxsize) > 0 else 2048

        self._lock = threading.RLock()

        self._data: "OrderedDict[str, Tuple[float, Any]]" = OrderedDict()


    def get(self, key: str) -> Any:

        now = time.time()

        with self._lock:

            item = self._data.get(key)

            if item is None:

                return None

            expires_at, value = item

            if expires_at and expires_at < now:

                try:

                    del self._data[key]

                except Exception:

                    pass

                return None

            self._data.move_to_end(key)

            return value


    def set(self, key: str, value: Any, ttl_seconds: int) -> None:

        ttl = int(ttl_seconds)

        expires_at = time.time() + ttl if ttl > 0 else 0.0

        with self._lock:

            self._data[key] = (expires_at, value)

            self._data.move_to_end(key)

            while len(self._data) > self._maxsize:

                self._data.popitem(last=False)


    def cached(

        self,

        ttl_seconds: int,

        key_prefix: str = "",

        key_fn: Optional[Callable[..., str]] = None,

    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:

        ttl = int(ttl_seconds)


        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:

            @functools.wraps(fn)

            def wrapper(*args: Any, **kwargs: Any) -> Any:

                if key_fn is not None:

                    k = key_fn(*args, **kwargs)

                else:

                    k = f"{fn.__module__}.{fn.__name__}:{args!r}:{kwargs!r}"

                key = f"{key_prefix}{k}"

                hit = self.get(key)

                if hit is not None:

                    return hit

                val = fn(*args, **kwargs)

                self.set(key, val, ttl)

                return val


            return wrapper


        return decorator
