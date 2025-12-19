"""Audit log for critical AI/system actions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.project_paths import PROJECT_ROOT


def _storage_path() -> Path:
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "audit_trail.json"


@dataclass
class AuditEvent:
    event_type: str
    severity: str
    payload: Dict[str, Any] = field(default_factory=dict)
    requires_ack: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    acknowledged_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "severity": self.severity,
            "payload": self.payload,
            "requires_ack": self.requires_ack,
            "created_at": self.created_at,
            "acknowledged_at": self.acknowledged_at,
        }


class AuditTrail:
    """Append-only audit log stored locally."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self.path = storage_path or _storage_path()
        self._events: List[AuditEvent] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        for item in payload.get("events", []):
            self._events.append(
                AuditEvent(
                    event_type=item.get("event_type", "unknown"),
                    severity=item.get("severity", "info"),
                    payload=item.get("payload", {}),
                    requires_ack=bool(item.get("requires_ack", False)),
                    created_at=item.get("created_at", datetime.utcnow().isoformat()),
                    acknowledged_at=item.get("acknowledged_at"),
                )
            )

    def _save(self) -> None:
        payload = {"events": [event.to_dict() for event in self._events[-500:]]}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def log(self, event_type: str, severity: str, payload: Optional[Dict[str, Any]] = None, requires_ack: bool = False) -> Dict[str, Any]:
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            payload=payload or {},
            requires_ack=requires_ack,
        )
        self._events.append(event)
        self._save()
        return event.to_dict()

    def acknowledge(self, index: int) -> Dict[str, Any]:
        if index < 0 or index >= len(self._events):
            raise IndexError("invalid audit index")
        event = self._events[index]
        event.acknowledged_at = datetime.utcnow().isoformat()
        self._save()
        return event.to_dict()

    def list_events(self, limit: int = 50) -> Dict[str, Any]:
        return {"events": [event.to_dict() for event in self._events[-limit:]]}


__all__ = ["AuditTrail", "AuditEvent"]
