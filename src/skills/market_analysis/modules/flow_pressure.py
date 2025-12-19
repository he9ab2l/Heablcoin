"""Order flow pressure analysis."""
from __future__ import annotations
from typing import Any, Dict
import pandas as pd
from ..data_provider import StandardMarketData


def analyze_flow_pressure(data: StandardMarketData, params: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate taker buy/sell pressure using volume + price response."""
    df = data.df.copy()
    if "flow_samples" in params:
        df = pd.DataFrame(params["flow_samples"], columns=df.columns)
    if df.empty or len(df) < 5:
        return {"name": "flow_pressure", "error": "not_enough_data"}
    df["mid_move"] = df["close"].pct_change().fillna(0)
    df["directional_volume"] = df["volume"] * df["mid_move"].apply(lambda x: 1 if x >= 0 else -1)
    pressure = df["directional_volume"].sum()
    total_volume = df["volume"].sum() or 1.0
    ratio = pressure / total_volume
    state = "buying" if ratio > 0.05 else "selling" if ratio < -0.05 else "balanced"
    volatility = float(df["mid_move"].std())
    conviction = min(abs(ratio) * 100, 100.0)
    markdown = (
        f"**Flow Pressure**\n"
        f"- 状态: {state}\n"
        f"- 压力比: {ratio:.2%}\n"
        f"- 波动率: {volatility:.4f}\n"
        f"- 置信度: {conviction:.1f}%\n"
    )
    return {
        "name": "flow_pressure",
        "state": state,
        "pressure_ratio": round(ratio, 4),
        "volatility": round(volatility, 4),
        "confidence_pct": round(conviction, 2),
        "markdown": markdown,
    }
__all__ = ["analyze_flow_pressure"]
