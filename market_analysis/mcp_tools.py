from __future__ import annotations

from typing import Any, Optional

from market_analysis.core import MarketAnalyzer
from report.query_backup import save_query_backup


def get_market_analysis_modular(
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    modules: str = "",
    return_format: str = "markdown",
) -> str:
    analyzer = MarketAnalyzer()
    selected = [m.strip() for m in (modules or "").split(",") if m.strip()]
    result = analyzer.analyze(symbol=symbol, timeframe=timeframe, modules=selected or None, return_format=return_format)
    try:
        save_query_backup(
            tool_name="get_market_analysis_modular",
            title=f"{symbol}__{timeframe}",
            content=result,
            params={"symbol": symbol, "timeframe": timeframe, "modules": modules, "return_format": return_format},
            return_format=return_format,
            extra_meta={"kind": "market_analysis"},
        )
    except Exception:
        pass
    return result


def register_tools(mcp: Any) -> None:
    mcp.tool()(get_market_analysis_modular)
