"""Strategy registry for lifecycle management."""


from __future__ import annotations


import json

from dataclasses import dataclass, field

from datetime import datetime

from pathlib import Path

from typing import Any, Dict, List, Optional


from utils.project_paths import PROJECT_ROOT


def _registry_path() -> Path:

    data_dir = PROJECT_ROOT / "data"

    data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir / "strategy_registry.json"


@dataclass

class StrategyRecord:

    name: str

    version: str

    owner: str

    symbol: str

    timeframe: str

    direction: str

    risk_level: str

    description: str = ""

    tags: List[str] = field(default_factory=list)

    enabled: bool = True

    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


    def to_dict(self) -> Dict[str, Any]:

        payload = self.__dict__.copy()

        payload["tags"] = list(self.tags)

        return payload


class StrategyRegistry:

    """Simple JSON-backed registry for strategy metadata."""


    def __init__(self, storage_path: Optional[Path] = None) -> None:

        self.path = storage_path or _registry_path()

        self._items: List[StrategyRecord] = []

        self._load()


    # ------------------------------------------------------------------ persistence helpers

    def _load(self) -> None:

        if not self.path.exists():

            return

        try:

            data = json.loads(self.path.read_text(encoding="utf-8"))

        except Exception:

            data = {"strategies": []}

        self._items = [

            StrategyRecord(

                **{**item, "tags": item.get("tags", [])}

            )

            for item in data.get("strategies", [])

        ]


    def _save(self) -> None:

        payload = {"strategies": [record.to_dict() for record in self._items]}

        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


    def _find(self, name: str) -> Optional[StrategyRecord]:

        for record in self._items:

            if record.name == name:

                return record

        return None


    # ------------------------------------------------------------------ public API

    def register(

        self,

        name: str,

        version: str,

        owner: str,

        symbol: str,

        timeframe: str,

        direction: str,

        risk_level: str,

        description: str = "",

        tags: Optional[List[str]] = None,

    ) -> StrategyRecord:

        record = self._find(name)

        now = datetime.utcnow().isoformat()

        if record:

            record.version = version

            record.owner = owner

            record.symbol = symbol

            record.timeframe = timeframe

            record.direction = direction

            record.risk_level = risk_level

            record.description = description

            record.tags = list(tags or record.tags)

            record.updated_at = now

        else:

            record = StrategyRecord(

                name=name,

                version=version,

                owner=owner,

                symbol=symbol,

                timeframe=timeframe,

                direction=direction,

                risk_level=risk_level,

                description=description,

                tags=list(tags or []),

            )

            self._items.append(record)

        self._save()

        return record


    def set_enabled(self, name: str, enabled: bool) -> StrategyRecord:

        record = self._find(name)

        if not record:

            raise ValueError(f"strategy '{name}' not found")

        record.enabled = bool(enabled)

        record.updated_at = datetime.utcnow().isoformat()

        self._save()

        return record


    def list(

        self,

        *,

        filter_active: bool = False,

        include_conflicts: bool = True,

    ) -> Dict[str, Any]:

        items = [

            record.to_dict()

            for record in self._items

            if (not filter_active or record.enabled)

        ]

        result: Dict[str, Any] = {"strategies": items}

        if include_conflicts:

            result["conflicts"] = self._detect_conflicts(items)

        return result


    def _detect_conflicts(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

        conflicts: List[Dict[str, Any]] = []

        key_map: Dict[str, List[Dict[str, Any]]] = {}

        for record in items:

            if not record.get("enabled", True):

                continue

            key = f"{record['symbol']}::{record['timeframe']}"

            key_map.setdefault(key, []).append(record)

        for key, bucket in key_map.items():

            if len(bucket) < 2:

                continue

            long_count = sum(1 for item in bucket if item["direction"].lower().startswith("long"))

            short_count = sum(1 for item in bucket if item["direction"].lower().startswith("short"))

            if long_count and short_count:

                conflicts.append(

                    {

                        "symbol_timeframe": key,

                        "type": "direction_conflict",

                        "strategies": [item["name"] for item in bucket],

                    }

                )

            if len(bucket) >= 3:

                conflicts.append(

                    {

                        "symbol_timeframe": key,

                        "type": "overcrowded",

                        "strategies": [item["name"] for item in bucket],

                    }

                )

        return conflicts


__all__ = ["StrategyRegistry"]
