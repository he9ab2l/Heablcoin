from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def now_ts() -> float:
    return utcnow().timestamp()


def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def env_int(name: str, default: int) -> int:
    import os

    v = os.getenv(name)
    if v is None:
        return default
    try:
        return int(v)
    except Exception:
        return default


def clamp(v: float, lo: float, hi: float) -> float:
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v
