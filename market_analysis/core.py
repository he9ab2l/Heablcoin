from __future__ import annotations

from typing import Any, Dict, List, Optional

from market_analysis.data_provider import DataProvider
from market_analysis.registry import AnalyzerRegistry
from market_analysis.modules.technical_summary import analyze_technical_summary
from market_analysis.modules.trading_signals import analyze_trading_signals
from market_analysis.modules.sentiment import analyze_sentiment
from market_analysis.modules.patterns import detect_patterns
from market_analysis.modules.market_structure import analyze_structure
from market_analysis.report_generator import to_json, to_markdown


class MarketAnalyzer:
    def __init__(self, provider: Optional[DataProvider] = None, registry: Optional[AnalyzerRegistry] = None) -> None:
        self.provider = provider or DataProvider.instance()
        self.registry = registry or AnalyzerRegistry()
        self._register_builtin_modules()

    def _register_builtin_modules(self) -> None:
        if self.registry.get("technical") is None:
            self.registry.register("technical", analyze_technical_summary, enabled_by_default=True)
        if self.registry.get("signals") is None:
            self.registry.register("signals", analyze_trading_signals, enabled_by_default=True)
        if self.registry.get("sentiment") is None:
            self.registry.register("sentiment", analyze_sentiment, enabled_by_default=False)
        if self.registry.get("patterns") is None:
            self.registry.register("patterns", detect_patterns, enabled_by_default=False)
        if self.registry.get("structure") is None:
            self.registry.register("structure", analyze_structure, enabled_by_default=False)

    def analyze(
        self,
        symbol: str = "BTC/USDT",
        timeframe: str = "1h",
        modules: Optional[List[str]] = None,
        limit: int = 100,
        return_format: str = "markdown",
        **params: Any,
    ) -> str:
        selected = modules or self.registry.defaults()
        std = self.provider.get_standard_data(symbol=symbol, timeframe=timeframe, limit=limit, include_ticker=True)

        out: List[Dict[str, Any]] = []
        for name in selected:
            mod = self.registry.get(name)
            if mod is None:
                out.append({"name": name, "error": "unknown_module"})
                continue
            try:
                out.append(mod.analyze(std, params))
            except Exception as e:
                out.append({"name": name, "error": f"{type(e).__name__}: {e}"})

        fmt = (return_format or "markdown").lower().strip()
        title = f"Market Analysis - {symbol} - {timeframe}"
        if fmt == "json":
            return to_json(title, out)
        return to_markdown(title, out)
