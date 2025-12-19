"""Multi-timeframe structure quality assessment."""


from __future__ import annotations


from dataclasses import dataclass

from typing import Any, Dict, List, Sequence


import pandas as pd


from ..data_provider import DataProvider, StandardMarketData


DEFAULT_TIMEFRAMES = ["15m", "1h", "4h"]


@dataclass

class FrameSignal:

    timeframe: str

    slope_pct: float

    label: str


    def to_dict(self) -> Dict[str, Any]:

        return {

            "timeframe": self.timeframe,

            "slope_pct": round(self.slope_pct, 4),

            "label": self.label,

        }


def _calc_slope(df: pd.DataFrame) -> float:

    if df.empty:

        return 0.0

    closes = df["close"].astype(float).values

    if len(closes) < 2:

        return 0.0

    return (closes[-1] - closes[0]) / (closes[0] or 1.0)


def _label_from_slope(value: float) -> str:

    if value > 0.02:

        return "strong_uptrend"

    if value > 0.005:

        return "moderate_uptrend"

    if value < -0.02:

        return "strong_downtrend"

    if value < -0.005:

        return "moderate_downtrend"

    return "range"


def _volatility_score(df: pd.DataFrame) -> float:

    returns = df["close"].pct_change().dropna()

    if returns.empty:

        return 0.0

    return min(float(returns.std() * (len(df) ** 0.5)), 0.5)


def analyze_structure_quality(data: StandardMarketData, options: Dict[str, Any]) -> Dict[str, Any]:

    """Assess multi-timeframe alignment and regime quality."""

    provider = DataProvider.instance()

    timeframes: Sequence[str] = options.get("timeframes") or DEFAULT_TIMEFRAMES

    synthetic_frames: Dict[str, List[List[float]]] = options.get("synthetic_frames", {})

    skip_fetch = options.get("skip_fetch", False)


    signals: List[FrameSignal] = []

    base_tf = data.metadata.get("timeframe")

    for tf in timeframes:

        if tf == base_tf and not synthetic_frames:

            df = data.df.copy()

        elif tf in synthetic_frames:

            df = pd.DataFrame(

                synthetic_frames[tf],

                columns=["timestamp", "open", "high", "low", "close", "volume"],

            )

        elif skip_fetch:

            continue

        else:

            ohlcv = provider.fetch_ohlcv(data.metadata["symbol"], tf, limit=120)

            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])

        slope = _calc_slope(df)

        signals.append(FrameSignal(timeframe=tf, slope_pct=slope, label=_label_from_slope(slope)))


    if not signals:

        return {"module": "structure_quality", "error": "no_data"}


    up_count = sum(1 for s in signals if "uptrend" in s.label)

    down_count = sum(1 for s in signals if "downtrend" in s.label)

    aligned = max(up_count, down_count) / len(signals)

    structure_score = round(aligned * 100.0, 2)

    if aligned >= 0.75:

        regime = "aligned"

    elif aligned >= 0.5:

        regime = "mixed"

    else:

        regime = "choppy"


    vol_score = _volatility_score(data.df)

    vol_label = "calm" if vol_score < 0.05 else "balanced" if vol_score < 0.15 else "elevated"

    execution_hint = "Fade extremes carefully" if regime == "choppy" else (

        "Prefer trend continuation entries" if up_count > down_count else "Watch for breakdowns"

    )


    return {

        "module": "structure_quality",

        "structure_alignment_score": structure_score,

        "signals": [s.to_dict() for s in signals],

        "regime": regime,

        "volatility": {"score": round(vol_score, 4), "label": vol_label},

        "execution_hint": execution_hint,

    }


__all__ = ["analyze_structure_quality"]
