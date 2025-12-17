from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from market_analysis.data_provider import StandardMarketData


AnalyzerFn = Callable[[StandardMarketData, Dict[str, Any]], Dict[str, Any]]


@dataclass
class AnalyzerModule:
    name: str
    analyze: AnalyzerFn
    enabled_by_default: bool = True


class AnalyzerRegistry:
    def __init__(self) -> None:
        self._modules: Dict[str, AnalyzerModule] = {}

    def register(self, name: str, analyze: AnalyzerFn, enabled_by_default: bool = True) -> None:
        self._modules[name] = AnalyzerModule(name=name, analyze=analyze, enabled_by_default=enabled_by_default)

    def get(self, name: str) -> Optional[AnalyzerModule]:
        return self._modules.get(name)

    def list(self) -> List[str]:
        return sorted(self._modules.keys())

    def defaults(self) -> List[str]:
        return [k for k, m in self._modules.items() if m.enabled_by_default]
