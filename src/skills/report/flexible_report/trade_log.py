from __future__ import annotations


from datetime import datetime

import csv

from pathlib import Path

from typing import Any, Dict, List, Optional


from utils.project_paths import PROJECT_ROOT


def trade_log_path() -> Path:

    return PROJECT_ROOT / "trade_history.csv"


def safe_float(v: Any, default: float = 0.0) -> float:

    try:

        return float(v)

    except Exception:

        return default


def parse_dt(s: Any) -> Optional[datetime]:

    raw = str(s or "").strip()

    if not raw:

        return None

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):

        try:

            return datetime.strptime(raw, fmt)

        except Exception:

            continue

    return None


def read_trade_log(limit: Optional[int] = None) -> List[Dict[str, Any]]:

    p = trade_log_path()

    if not p.exists():

        return []

    try:

        with p.open("r", encoding="utf-8", newline="") as f:

            reader = csv.reader(f)

            rows = list(reader)

    except Exception:

        return []


    if len(rows) < 2:

        return []


    header = rows[0]

    data_rows = rows[1:]

    if limit is not None:

        data_rows = data_rows[-int(limit):]


    out: List[Dict[str, Any]] = []

    for r in data_rows:

        rec: Dict[str, Any] = {}

        for i, k in enumerate(header):

            rec[str(k)] = r[i] if i < len(r) else ""

        out.append(rec)

    return out


__all__ = ["trade_log_path", "safe_float", "parse_dt", "read_trade_log"]
