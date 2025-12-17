from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from market_analysis.cache_manager import CacheManager


@dataclass
class StateManager:
    config: Dict[str, Any] = field(default_factory=dict)
    cache: CacheManager = field(default_factory=lambda: CacheManager(maxsize=2048))
    container: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        self.container[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.container.get(key, default)


_STATE: Optional[StateManager] = None


def get_state() -> StateManager:
    global _STATE
    if _STATE is None:
        _STATE = StateManager()
    return _STATE
