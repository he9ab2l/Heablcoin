"""Account-level risk budget manager."""


from __future__ import annotations


import json

import os

from dataclasses import dataclass, field

from datetime import datetime, timezone, timedelta

from pathlib import Path

from typing import Any, Dict, Optional


from utils.env_helpers import env_float

from utils.project_paths import PROJECT_ROOT


def _default_path() -> Path:

    data_dir = PROJECT_ROOT / "data"

    data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir / "risk_budget.json"


def _period_key(period: str, moment: datetime) -> str:

    if period == "daily":

        return moment.strftime("%Y-%m-%d")

    if period == "weekly":

        week_start = moment - timedelta(days=moment.weekday())

        return week_start.strftime("%Y-%m-%d")

    if period == "monthly":

        return moment.strftime("%Y-%m-01")

    raise ValueError(f"unknown period: {period}")


@dataclass

class PeriodState:

    budget: float

    used: float = 0.0

    period_key: str = ""

    frozen: bool = False

    freeze_reason: str = ""


    def to_dict(self) -> Dict[str, Any]:

        return {

            "budget": self.budget,

            "used": round(self.used, 4),

            "period_key": self.period_key,

            "frozen": self.frozen,

            "freeze_reason": self.freeze_reason,

            "remaining": round(max(self.budget - self.used, 0.0), 4),

            "utilization_pct": round((self.used / self.budget * 100.0) if self.budget else 0.0, 2),

        }


class RiskBudgetManager:

    """Manages daily/weekly/monthly loss budgets and freeze status."""


    PERIODS = ("daily", "weekly", "monthly")


    def __init__(

        self,

        storage_path: Optional[Path] = None,

        budgets: Optional[Dict[str, float]] = None,

    ) -> None:

        self.path = storage_path or _default_path()

        default_budgets = {

            "daily": env_float("RISK_BUDGET_DAILY", 500.0),

            "weekly": env_float("RISK_BUDGET_WEEKLY", 2000.0),

            "monthly": env_float("RISK_BUDGET_MONTHLY", 8000.0),

        }

        if budgets:

            default_budgets.update(budgets)

        self._state: Dict[str, PeriodState] = {}

        self._events: list[Dict[str, Any]] = []

        self._load()

        for period in self.PERIODS:

            if period not in self._state:

                self._state[period] = PeriodState(budget=default_budgets[period])

            elif budgets and period in budgets:

                self._state[period].budget = budgets[period]

        self._save()


    # ------------------------------------------------------------------ persistence helpers

    def _load(self) -> None:

        if not self.path.exists():

            return

        try:

            payload = json.loads(self.path.read_text(encoding="utf-8"))

        except Exception:

            payload = {}

        periods = payload.get("periods", {})

        self._state = {

            period: PeriodState(**values) for period, values in periods.items()

        }

        self._events = payload.get("events", [])


    def _save(self) -> None:

        payload = {

            "periods": {period: state.__dict__ for period, state in self._state.items()},

            "events": self._events[-200:],

        }

        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


    # ------------------------------------------------------------------ internal helpers

    def _ensure_period(self, period: str, moment: datetime) -> PeriodState:

        state = self._state.setdefault(period, PeriodState(budget=0.0))

        key = _period_key(period, moment)

        if state.period_key != key:

            state.period_key = key

            state.used = 0.0

            state.frozen = False

            state.freeze_reason = ""

        return state


    def _freeze_if_needed(self, period: str, state: PeriodState) -> None:

        if not state.frozen and state.used > state.budget > 0:

            state.frozen = True

            state.freeze_reason = f"{period} loss {state.used:.2f} > {state.budget:.2f}"


    # ------------------------------------------------------------------ public API

    def get_status(self) -> Dict[str, Any]:

        now = datetime.utcnow().replace(tzinfo=timezone.utc)

        for period in self.PERIODS:

            self._ensure_period(period, now)

        return {

            "periods": {period: state.to_dict() for period, state in self._state.items()},

            "frozen": any(state.frozen for state in self._state.values()),

            "events": self._events[-10:],

        }


    def record_event(self, loss_amount: float, tag: str = "", note: str = "") -> Dict[str, Any]:

        if loss_amount >= 0:

            loss = loss_amount

        else:

            loss = -loss_amount

        moment = datetime.utcnow().replace(tzinfo=timezone.utc)

        for period in self.PERIODS:

            state = self._ensure_period(period, moment)

            state.used += loss

            self._freeze_if_needed(period, state)

        event = {

            "timestamp": moment.isoformat(),

            "loss": round(loss, 4),

            "tag": tag,

            "note": note,

        }

        self._events.append(event)

        self._save()

        return {"event": event, "status": self.get_status()}


    def update_budget(self, period: str, budget: float, unfreeze: bool = False) -> Dict[str, Any]:

        if period not in self.PERIODS:

            raise ValueError(f"unknown period: {period}")

        state = self._state.setdefault(period, PeriodState(budget=budget))

        state.budget = max(float(budget), 0.0)

        if unfreeze:

            state.frozen = False

            state.freeze_reason = ""

        self._save()

        return self.get_status()


    def reset_period(self, period: str) -> Dict[str, Any]:

        if period not in self.PERIODS:

            raise ValueError(f"unknown period: {period}")

        state = self._state[period]

        state.used = 0.0

        state.frozen = False

        state.freeze_reason = ""

        state.period_key = _period_key(period, datetime.utcnow().replace(tzinfo=timezone.utc))

        self._save()

        return self.get_status()


__all__ = ["RiskBudgetManager"]
