from __future__ import annotations
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from utils.project_paths import PROJECT_ROOT


def get_trade_log_path() -> Path:
    """获取交易日志文件路径"""
    return PROJECT_ROOT / "trade_history.csv"


def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def parse_datetime(s: Any) -> Optional[datetime]:
    raw = str(s or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            continue
    return None


def read_trade_history(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """读取交易历史记录"""
    db_file = os.getenv('TRADE_DB_FILE', '').strip()
    if not db_file:
        db_file = str((PROJECT_ROOT / 'data' / 'trades.db').resolve())
    try:
        from utils.trade_storage import TradeStore


        store = TradeStore(db_path=db_file, csv_path=str(get_trade_log_path()))
        rows = store.list_trades(limit=int(limit) if limit and int(limit) > 0 else 0)
        if rows:
            rows = list(reversed(rows))
            out: List[Dict[str, Any]] = []
            for r in rows:
                out.append({
                    '时间': str(r.get('time_str') or ''),
                    '订单ID': str(r.get('order_id') or ''),
                    '交易对': str(r.get('symbol') or ''),
                    '方向': str(r.get('side') or '').upper(),
                    '数量': str(r.get('amount') or ''),
                    '价格': str(r.get('price') or ''),
                    '总额': str(r.get('cost') or ''),
                    '状态': str(r.get('status') or ''),
                })
            return out
    except Exception:
        pass
    p = get_trade_log_path()
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


def normalize_trade_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """标准化交易记录格式"""
    return {
        "order_id": str(raw.get("订单ID") or raw.get("order_id") or ""),
        "symbol": str(raw.get("交易对") or raw.get("symbol") or ""),
        "side": str(raw.get("方向") or raw.get("side") or "").upper(),
        "qty": safe_float(raw.get("数量") or raw.get("qty")),
        "price": safe_float(raw.get("价格") or raw.get("price")),
        "cost": safe_float(raw.get("总额") or raw.get("cost")),
        "fee": safe_float(raw.get("手续费") or raw.get("fee")),
        "time": parse_datetime(raw.get("时间") or raw.get("time")),
        "time_str": str(raw.get("时间") or raw.get("time") or ""),
    }
__all__ = [
    "get_trade_log_path",
    "safe_float",
    "parse_datetime",
    "read_trade_history",
    "normalize_trade_record",
]
