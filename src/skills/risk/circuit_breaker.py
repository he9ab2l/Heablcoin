"""Circuit breaker helper to pause execution during extreme moves."""


from __future__ import annotations


import json

from dataclasses import dataclass, field

from datetime import datetime, timedelta

from pathlib import Path

from typing import Dict, Any, Optional


from utils.project_paths import PROJECT_ROOT


def _storage_path() -> Path:

    data_dir = PROJECT_ROOT / "data"

    data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir / "circuit_breaker.json"


@dataclass

class CircuitState:

    symbol: str

    triggered: bool = False

    last_triggered: Optional[str] = None

    cooldown_minutes: int = 30

    threshold_pct: float = 0.05

    halt_reasons: list[str] = field(default_factory=list)


    def to_dict(self) -> Dict[str, Any]:

        return {

            "symbol": self.symbol,

            "triggered": self.triggered,

            "last_triggered": self.last_triggered,

            "cooldown_minutes": self.cooldown_minutes,

            "threshold_pct": round(self.threshold_pct * 100.0, 2),

            "halt_reasons": list(self.halt_reasons),

        }


class CircuitBreaker:

    """Monitor percentage moves + liquidity health and pause execution if required."""


    def __init__(self, storage_path: Optional[Path] = None) -> None:

        self.path = storage_path or _storage_path()

        self._states: Dict[str, CircuitState] = {}

        self._load()


    def _load(self) -> None:

        if not self.path.exists():

            return

        try:

            payload = json.loads(self.path.read_text(encoding="utf-8"))

        except Exception:

            payload = {}

        for symbol, data in payload.get("states", {}).items():

            self._states[symbol] = CircuitState(

                symbol=symbol,

                triggered=bool(data.get("triggered", False)),

                last_triggered=data.get("last_triggered"),

                cooldown_minutes=int(data.get("cooldown_minutes", 30)),

                threshold_pct=float(data.get("threshold_pct", 0.05)),

                halt_reasons=list(data.get("halt_reasons", [])),

            )


    def _save(self) -> None:

        payload = {"states": {symbol: state.to_dict() for symbol, state in self._states.items()}}

        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


    def configure(self, symbol: str, *, threshold_pct: float, cooldown_minutes: int) -> Dict[str, Any]:

        state = self._states.setdefault(symbol, CircuitState(symbol=symbol))

        state.threshold_pct = max(float(threshold_pct), 0.01)

        state.cooldown_minutes = max(int(cooldown_minutes), 1)

        self._save()

        return state.to_dict()


    def check_move(self, symbol: str, move_pct: float, *, liquidity_score: float = 1.0, reason: str = "") -> Dict[str, Any]:

        """Record a move; returns if execution should pause."""

        state = self._states.setdefault(symbol, CircuitState(symbol=symbol))

        now = datetime.utcnow()

        if state.last_triggered:

            last = datetime.fromisoformat(state.last_triggered)

            if now - last >= timedelta(minutes=state.cooldown_minutes):

                state.triggered = False

                state.halt_reasons.clear()


        abs_move = abs(move_pct)

        should_trigger = abs_move >= state.threshold_pct or liquidity_score < 0.3

        if should_trigger:

            state.triggered = True

            state.last_triggered = now.isoformat()

            entry = f"{reason or 'extreme_move'} | move={move_pct:.2%} liquidity={liquidity_score:.2f}"

            state.halt_reasons.append(entry)

        self._save()

        return state.to_dict()


    def status(self, symbol: Optional[str] = None) -> Dict[str, Any]:

        if symbol:

            state = self._states.get(symbol)

            if not state:

                return {"symbol": symbol, "triggered": False}

            return state.to_dict()

        return {"states": [state.to_dict() for state in self._states.values()]}


__all__ = ["CircuitBreaker", "CircuitState"]
