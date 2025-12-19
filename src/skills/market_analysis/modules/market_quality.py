"""Aggregate market quality score using structure + flow modules."""
from __future__ import annotations
from typing import Any, Dict
from ..data_provider import StandardMarketData
from .structure_quality import analyze_structure_quality
from .flow_pressure import analyze_flow_pressure


def analyze_market_quality(data: StandardMarketData, params: Dict[str, Any]) -> Dict[str, Any]:
    structure = analyze_structure_quality(data, params)
    flow = analyze_flow_pressure(data, params)
    if "error" in structure or "error" in flow:
        return {"name": "market_quality", "error": "insufficient_data"}
    structure_score = structure.get("structure_alignment_score", 0.0)
    confidence = flow.get("confidence_pct", 0.0)
    pressure_state = flow.get("state", "balanced")
    quality = 0.5 * structure_score + 0.5 * confidence
    tradable = quality >= 55 and pressure_state != "balanced"
    note = "Focus on high conviction trends." if tradable else "Market quality mediocre, wait for clarity."
    return {
        "name": "market_quality",
        "structure_alignment_score": structure_score,
        "flow_confidence_pct": confidence,
        "pressure_state": pressure_state,
        "quality_score": round(quality, 2),
        "tradable": tradable,
        "note": note,
    }
__all__ = ["analyze_market_quality"]
