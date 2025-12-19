############################################################
# 📘 文件说明：
# 本文件实现的功能：Strategy-level capital isolation.
#
# 📋 程序整体伪代码（中文）：
# 1. 初始化主要依赖与变量
# 2. 加载输入数据或接收外部请求
# 3. 执行主要逻辑步骤（如计算、处理、训练、渲染等）
# 4. 输出或返回结果
# 5. 异常处理与资源释放
#
# 🔄 程序流程图（逻辑流）：
# ┌──────────┐
# │  输入数据 │
# └─────┬────┘
#       ↓
# ┌────────────┐
# │  核心处理逻辑 │
# └─────┬──────┘
#       ↓
# ┌──────────┐
# │  输出结果 │
# └──────────┘
#
# 📊 数据管道说明：
# 数据流向：输入源 → 数据清洗/转换 → 核心算法模块 → 输出目标（文件 / 接口 / 终端）
#
# 🧩 文件结构：
# - 依赖（标准库）：__future__, dataclasses, datetime, json, pathlib, typing
# - 依赖（第三方）：无
# - 依赖（本地）：utils.project_paths
#
# 🕒 创建时间：2025-12-19
############################################################

"""Strategy-level capital isolation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from utils.project_paths import PROJECT_ROOT


def _storage_path() -> Path:
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "strategy_funds.json"


@dataclass
class PoolState:
    name: str
    capital: float
    locked: float = 0.0
    max_drawdown_pct: float = 0.2
    status: str = "active"
    notes: str = ""
    total_pnl: float = 0.0
    trades: int = 0
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def available(self) -> float:
        return max(self.capital - self.locked, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "capital": round(self.capital, 4),
            "locked": round(self.locked, 4),
            "available": round(self.available, 4),
            "max_drawdown_pct": round(self.max_drawdown_pct * 100.0, 2),
            "status": self.status,
            "notes": self.notes,
            "total_pnl": round(self.total_pnl, 4),
            "trades": self.trades,
            "last_updated": self.last_updated,
        }


class FundAllocator:
    """Simple JSON-backed allocator that isolates capital per strategy."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self.path = storage_path or _storage_path()
        self._pools: Dict[str, PoolState] = {}
        self._load()

    # ------------------------------------------------------------------ persistence
    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        pools = payload.get("pools", {})
        for name, data in pools.items():
            self._pools[name] = PoolState(
                name=name,
                capital=float(data.get("capital", 0.0)),
                locked=float(data.get("locked", 0.0)),
                max_drawdown_pct=float(data.get("max_drawdown_pct", 0.2)),
                status=data.get("status", "active"),
                notes=data.get("notes", ""),
                total_pnl=float(data.get("total_pnl", 0.0)),
                trades=int(data.get("trades", 0)),
                last_updated=data.get("last_updated", datetime.utcnow().isoformat()),
            )

    def _save(self) -> None:
        payload = {"pools": {name: pool.to_dict() for name, pool in self._pools.items()}}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------ helpers
    def _get(self, name: str) -> PoolState:
        if name not in self._pools:
            raise ValueError(f"pool '{name}' not found")
        return self._pools[name]

    def _update_status(self, pool: PoolState) -> None:
        drawdown = abs(pool.total_pnl) if pool.total_pnl < 0 else 0.0
        if pool.capital <= 0 or (pool.capital > 0 and drawdown / pool.capital >= pool.max_drawdown_pct):
            pool.status = "frozen"
        elif pool.status == "frozen" and pool.available > 0:
            pool.status = "active"

    # ------------------------------------------------------------------ public API
    def set_pool(self, name: str, capital: float, *, max_drawdown_pct: float = 0.2, notes: str = "") -> Dict[str, Any]:
        pool = self._pools.get(name)
        now = datetime.utcnow().isoformat()
        if pool:
            pool.capital = max(float(capital), 0.0)
            pool.max_drawdown_pct = max(float(max_drawdown_pct), 0.01)
            pool.notes = notes or pool.notes
            pool.last_updated = now
        else:
            pool = PoolState(
                name=name,
                capital=max(float(capital), 0.0),
                max_drawdown_pct=max(float(max_drawdown_pct), 0.01),
                notes=notes,
            )
            self._pools[name] = pool
        self._update_status(pool)
        self._save()
        return pool.to_dict()

    def allocate(self, name: str, amount: float) -> Dict[str, Any]:
        pool = self._get(name)
        amount = max(float(amount), 0.0)
        if amount > pool.available:
            raise ValueError(f"insufficient capital in {name}: need {amount}, available {pool.available}")
        pool.locked += amount
        pool.last_updated = datetime.utcnow().isoformat()
        self._save()
        return pool.to_dict()

    def release(self, name: str, amount: float, realized_pnl: float = 0.0) -> Dict[str, Any]:
        pool = self._get(name)
        amount = max(float(amount), 0.0)
        pool.locked = max(pool.locked - amount, 0.0)
        pool.capital += float(realized_pnl)
        pool.total_pnl += float(realized_pnl)
        pool.trades += 1
        pool.last_updated = datetime.utcnow().isoformat()
        self._update_status(pool)
        self._save()
        return pool.to_dict()

    def list_pools(self) -> Dict[str, Any]:
        return {"pools": [pool.to_dict() for pool in self._pools.values()]}


__all__ = ["FundAllocator", "PoolState"]
