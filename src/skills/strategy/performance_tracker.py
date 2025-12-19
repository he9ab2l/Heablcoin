"""Strategy-level performance attribution."""

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
    return data_dir / "strategy_performance.json"


@dataclass
class StrategyPerformance:
    name: str
    total_pnl: float = 0.0
    wins: int = 0
    losses: int = 0
    trades: int = 0
    gross_exposure_minutes: float = 0.0
    last_trade_at: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        win_rate = (self.wins / self.trades * 100.0) if self.trades else 0.0
        avg_duration = (self.gross_exposure_minutes / self.trades) if self.trades else 0.0
        return {
            "name": self.name,
            "total_pnl": round(self.total_pnl, 4),
            "trades": self.trades,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": round(win_rate, 2),
            "avg_duration_minutes": round(avg_duration, 2),
            "last_trade_at": self.last_trade_at,
            "tags": list(self.tags),
            "status": "contributor" if self.total_pnl >= 0 else "drag",
        }


class StrategyPerformanceTracker:
    """Aggregate attribution metrics for each strategy."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self.path = storage_path or _storage_path()
        self._stats: Dict[str, StrategyPerformance] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        for name, data in payload.get("strategies", {}).items():
            self._stats[name] = StrategyPerformance(
                name=name,
                total_pnl=float(data.get("total_pnl", 0.0)),
                wins=int(data.get("wins", 0)),
                losses=int(data.get("losses", 0)),
                trades=int(data.get("trades", 0)),
                gross_exposure_minutes=float(data.get("gross_exposure_minutes", 0.0)),
                last_trade_at=data.get("last_trade_at"),
                tags=list(data.get("tags", [])),
            )

    def _save(self) -> None:
        payload = {"strategies": {name: stat.__dict__ for name, stat in self._stats.items()}}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def record_trade(
        self,
        name: str,
        pnl: float,
        *,
        exposure_minutes: float = 0.0,
        tags: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        stat = self._stats.setdefault(name, StrategyPerformance(name=name))
        stat.total_pnl += float(pnl)
        stat.trades += 1
        if pnl >= 0:
            stat.wins += 1
        else:
            stat.losses += 1
        stat.gross_exposure_minutes += max(float(exposure_minutes), 0.0)
        if tags:
            stat.tags = sorted(set(stat.tags).union({t.strip() for t in tags if t.strip()}))
        stat.last_trade_at = datetime.utcnow().isoformat()
        self._save()
        return stat.to_dict()

    def report(self) -> Dict[str, Any]:
        stats = [stat.to_dict() for stat in self._stats.values()]
        stats.sort(key=lambda item: item["total_pnl"], reverse=True)
        return {
            "strategies": stats,
            "contributors": [s for s in stats if s["total_pnl"] >= 0],
            "drags": [s for s in stats if s["total_pnl"] < 0],
        }


__all__ = ["StrategyPerformanceTracker", "StrategyPerformance"]
