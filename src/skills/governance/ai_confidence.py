"""Confidence scoring for AI decisions."""
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
    return data_dir / "ai_confidence_log.json"


@dataclass


class ConfidenceEntry:
    decision_id: str
    score: float
    level: str
    action: str
    inputs: Dict[str, float] = field(default_factory=dict)
    rationale: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "score": round(self.score, 3),
            "level": self.level,
            "action": self.action,
            "inputs": self.inputs,
            "rationale": self.rationale,
            "tags": list(self.tags),
            "created_at": self.created_at,
        }


class DecisionConfidenceMonitor:
    """Assigns confidence + execution action per AI decision."""
    DEFAULT_WEIGHTS = {
        "signal_strength": 0.4,
        "data_quality": 0.2,
        "risk_alignment": 0.2,
        "latency": 0.2,
    }
    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self.path = storage_path or _storage_path()
        self._entries: list[ConfidenceEntry] = []
        self._load()
    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        for item in payload.get("entries", []):
            self._entries.append(
                ConfidenceEntry(
                    decision_id=item.get("decision_id", ""),
                    score=float(item.get("score", 0.0)),
                    level=item.get("level", "low"),
                    action=item.get("action", "suggest"),
                    inputs=item.get("inputs", {}),
                    rationale=item.get("rationale", ""),
                    tags=list(item.get("tags", [])),
                    created_at=item.get("created_at", datetime.utcnow().isoformat()),
                )
            )
    def _save(self) -> None:
        payload = {"entries": [entry.to_dict() for entry in self._entries[-200:]]}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    def score(
        self,
        decision_id: str,
        *,
        inputs: Dict[str, float],
        rationale: str = "",
        tags: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        normalized = {k: max(0.0, min(float(v), 1.0)) for k, v in inputs.items()}
        score = 0.0
        for key, weight in self.DEFAULT_WEIGHTS.items():
            score += normalized.get(key, 0.5) * weight
        level, action = self._classify(score)
        entry = ConfidenceEntry(
            decision_id=decision_id,
            score=score,
            level=level,
            action=action,
            inputs=normalized,
            rationale=rationale,
            tags=list(tags or []),
        )
        self._entries.append(entry)
        self._save()
        return entry.to_dict()
    @staticmethod
    def _classify(score: float) -> tuple[str, str]:
        if score >= 0.75:
            return "high", "auto_execute"
        if score >= 0.55:
            return "medium", "human_confirm"
        return "low", "advisory"
    def recent(self, limit: int = 20) -> Dict[str, Any]:
        return {"entries": [entry.to_dict() for entry in self._entries[-limit:]]}
__all__ = ["DecisionConfidenceMonitor", "ConfidenceEntry"]
