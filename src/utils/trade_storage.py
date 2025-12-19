import csv
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


_TRADE_STORE_LOCK = threading.RLock()


class TradeStore:
    def __init__(self, db_path: str, csv_path: str = "") -> None:
        self.db_path = str(db_path)
        self.csv_path = str(csv_path or "")
        self._init_db()
        self._maybe_migrate_csv()
    def _init_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    amount REAL NOT NULL,
                    price REAL NOT NULL,
                    cost REAL NOT NULL,
                    status TEXT,
                    time_str TEXT,
                    timestamp INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_side ON trades(side)")
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    def insert_trade(
        self,
        order_id: str,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        cost: float,
        status: str,
        time_str: str,
        timestamp: int,
    ) -> bool:
        order_id = str(order_id or "").strip()
        if not order_id:
            return False
        with _TRADE_STORE_LOCK:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO trades
                        (order_id, symbol, side, amount, price, cost, status, time_str, timestamp)
                    VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        str(symbol or ""),
                        str(side or "").upper(),
                        float(amount),
                        float(price),
                        float(cost),
                        str(status or ""),
                        str(time_str or ""),
                        int(timestamp),
                    ),
                )
        return True
    def list_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        lim = int(limit) if limit and int(limit) > 0 else 10
        with _TRADE_STORE_LOCK:
            with self._get_connection() as conn:
                cur = conn.execute(
                    """
                    SELECT order_id, symbol, side, amount, price, cost, status, time_str, timestamp
                    FROM trades
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (lim,),
                )
                return [dict(r) for r in cur.fetchall()]
    def iter_trades(self) -> Iterable[Dict[str, Any]]:
        with _TRADE_STORE_LOCK:
            with self._get_connection() as conn:
                cur = conn.execute(
                    """
                    SELECT order_id, symbol, side, amount, price, cost, status, time_str, timestamp
                    FROM trades
                    ORDER BY timestamp ASC
                    """
                )
                for r in cur.fetchall():
                    yield dict(r)
    def sum_cost_by_date_prefix(self, date_prefix: str) -> float:
        prefix = str(date_prefix or "").strip()
        if not prefix:
            return 0.0
        with _TRADE_STORE_LOCK:
            with self._get_connection() as conn:
                cur = conn.execute(
                    """
                    SELECT COALESCE(SUM(cost), 0) AS total
                    FROM trades
                    WHERE time_str LIKE ?
                    """,
                    (f"{prefix}%",),
                )
                row = cur.fetchone()
                try:
                    return float(row[0] if row is not None else 0.0)
                except Exception:
                    return 0.0
    def stats_since_date_prefix(self, start_date_prefix: str) -> Dict[str, Any]:
        prefix = str(start_date_prefix or "").strip()
        if not prefix:
            return {"buy": 0.0, "sell": 0.0, "count": 0}
        with _TRADE_STORE_LOCK:
            with self._get_connection() as conn:
                cur = conn.execute(
                    """
                    SELECT side, cost
                    FROM trades
                    WHERE time_str >= ?
                    """,
                    (prefix,),
                )
                buy = 0.0
                sell = 0.0
                count = 0
                for r in cur.fetchall():
                    count += 1
                    side = str(r[0] or "").upper()
                    try:
                        c = float(r[1])
                    except Exception:
                        c = 0.0
                    if side == "BUY":
                        buy += c
                    else:
                        sell += c
                return {"buy": buy, "sell": sell, "count": count}
    def _maybe_migrate_csv(self) -> None:
        if not self.csv_path:
            return
        p = Path(self.csv_path)
        if not p.exists():
            return
        try:
            with self._get_connection() as conn:
                cur = conn.execute("SELECT COUNT(1) FROM trades")
                row = cur.fetchone()
                existing = int(row[0] if row else 0)
        except Exception:
            return
        if existing > 0:
            return
        try:
            with p.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception:
            return
        for r in rows:
            time_str = str(r.get("时间") or "").strip()
            ts = 0
            if time_str:
                try:
                    ts = int(datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").timestamp())
                except Exception:
                    ts = 0
            try:
                amount = float(r.get("数量") or 0)
            except Exception:
                amount = 0.0
            try:
                price = float(r.get("价格") or 0)
            except Exception:
                price = 0.0
            try:
                cost = float(r.get("总额") or 0)
            except Exception:
                cost = 0.0
            try:
                self.insert_trade(
                    order_id=str(r.get("订单ID") or ""),
                    symbol=str(r.get("交易对") or ""),
                    side=str(r.get("方向") or ""),
                    amount=amount,
                    price=price,
                    cost=cost,
                    status=str(r.get("状态") or ""),
                    time_str=time_str,
                    timestamp=ts,
                )
            except Exception:
                continue
__all__ = ["TradeStore"]
