"""Volatility-aware position sizing utilities."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence
import pandas as pd
from skills.market_analysis.data_provider import DataProvider


@dataclass


class PositionSizingResult:
    symbol: str
    timeframe: str
    measured_vol: float
    target_vol: float
    scale: float
    suggested_notional: float
    base_notional: float
    note: str = ""
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "measured_vol": round(self.measured_vol, 4),
            "target_vol": round(self.target_vol, 4),
            "scale": round(self.scale, 3),
            "suggested_notional": round(self.suggested_notional, 4),
            "base_notional": round(self.base_notional, 4),
            "note": self.note,
        }


class VolatilityPositionSizer:
    """Use realized volatility to auto-scale position sizes."""
    def __init__(
        self,
        provider: Optional[DataProvider] = None,
        *,
        min_scale: float = 0.25,
        max_scale: float = 2.0,
    ) -> None:
        self.provider = provider or DataProvider.instance()
        self.min_scale = min_scale
        self.max_scale = max_scale
    @staticmethod
    def _realized_vol(prices: Sequence[float]) -> float:
        series = pd.Series(prices).pct_change().dropna()
        if series.empty:
            return 0.0
        return float(series.std())
    def measure_volatility(
        self,
        symbol: str,
        timeframe: str,
        *,
        limit: int = 120,
        synthetic_prices: Optional[Sequence[float]] = None,
    ) -> float:
        if synthetic_prices:
            return self._realized_vol(synthetic_prices)
        ohlcv = self.provider.fetch_ohlcv(symbol, timeframe, limit=limit)
        closes = [float(item[4]) for item in ohlcv]
        return self._realized_vol(closes)
    def suggest_notional(
        self,
        *,
        account_balance: float,
        risk_pct: float,
        symbol: str,
        timeframe: str,
        target_vol: float = 0.02,
        lookback: int = 120,
        synthetic_prices: Optional[Sequence[float]] = None,
    ) -> PositionSizingResult:
        base_notional = max(account_balance, 0.0) * max(risk_pct, 0.0)
        measured = self.measure_volatility(symbol, timeframe, limit=lookback, synthetic_prices=synthetic_prices)
        if measured <= 0:
            scale = self.max_scale
            note = "No volatility data, using max scale."
        else:
            raw_scale = target_vol / measured
            scale = max(self.min_scale, min(raw_scale, self.max_scale))
            note = "Vol-adjusted" if self.min_scale < scale < self.max_scale else "Clipped to bounds"
        suggested = base_notional * scale
        return PositionSizingResult(
            symbol=symbol,
            timeframe=timeframe,
            measured_vol=measured,
            target_vol=target_vol,
            scale=scale,
            suggested_notional=suggested,
            base_notional=base_notional,
            note=note,
        )
__all__ = ["VolatilityPositionSizer", "PositionSizingResult"]
