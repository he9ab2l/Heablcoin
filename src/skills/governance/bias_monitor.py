"""Detect behavioral drift in AI decisions."""


from __future__ import annotations


import json

from collections import deque, Counter

from dataclasses import dataclass

from datetime import datetime, timedelta

from pathlib import Path

from typing import Any, Deque, Dict, Optional


from utils.project_paths import PROJECT_ROOT


def _storage_path() -> Path:

    data_dir = PROJECT_ROOT / "data"

    data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir / "ai_bias_monitor.json"


@dataclass

class BiasSample:

    timestamp: str

    direction: str

    result: str

    pnl: float

    market_state: str


    def to_dict(self) -> Dict[str, Any]:

        return {

            "timestamp": self.timestamp,

            "direction": self.direction,

            "result": self.result,

            "pnl": round(self.pnl, 4),

            "market_state": self.market_state,

        }


class BiasMonitor:

    """Light-weight bias detector for AI agents."""


    def __init__(self, storage_path: Optional[Path] = None, window: int = 200) -> None:

        self.path = storage_path or _storage_path()

        self.window = window

        self._samples: Deque[BiasSample] = deque(maxlen=window)

        self._load()


    def _load(self) -> None:

        if not self.path.exists():

            return

        try:

            payload = json.loads(self.path.read_text(encoding="utf-8"))

        except Exception:

            payload = {}

        for item in payload.get("samples", []):

            self._samples.append(

                BiasSample(

                    timestamp=item.get("timestamp", datetime.utcnow().isoformat()),

                    direction=item.get("direction", "neutral"),

                    result=item.get("result", "unknown"),

                    pnl=float(item.get("pnl", 0.0)),

                    market_state=item.get("market_state", "unknown"),

                )

            )


    def _save(self) -> None:

        payload = {"samples": [sample.to_dict() for sample in self._samples]}

        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


    def record(self, direction: str, result: str, pnl: float, market_state: str) -> Dict[str, Any]:

        sample = BiasSample(

            timestamp=datetime.utcnow().isoformat(),

            direction=direction,

            result=result,

            pnl=pnl,

            market_state=market_state,

        )

        self._samples.append(sample)

        self._save()

        return sample.to_dict()


    def diagnose(self) -> Dict[str, Any]:

        directions = Counter(sample.direction for sample in self._samples)

        states = Counter(sample.market_state for sample in self._samples)

        total = len(self._samples)

        warnings = []

        if total >= 10:

            dominant_dir, count = directions.most_common(1)[0]

            if count / total >= 0.75:

                warnings.append(f"Direction bias detected: {dominant_dir} {count}/{total}.")

        recent_time = datetime.utcnow() - timedelta(minutes=30)

        over_trading = sum(1 for s in self._samples if datetime.fromisoformat(s.timestamp) >= recent_time)

        if over_trading >= 10:

            warnings.append("Potential over-trading: >=10 decisions in last 30 minutes.")

        market_bias = ""

        if states:

            dominant_state, state_count = states.most_common(1)[0]

            if state_count / total >= 0.7:

                market_bias = dominant_state

                warnings.append(f"State bias: {dominant_state} used {state_count}/{total}.")

        avg_pnl = sum(sample.pnl for sample in self._samples) / total if total else 0.0

        return {

            "sample_count": total,

            "direction_distribution": directions,

            "market_state_distribution": states,

            "avg_pnl": round(avg_pnl, 4),

            "warnings": warnings,

            "dominant_state": market_bias,

        }


__all__ = ["BiasMonitor", "BiasSample"]
