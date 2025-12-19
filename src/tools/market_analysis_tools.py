from __future__ import annotations

from typing import Any, Optional

from core.mcp_safety import mcp_tool_safe
from skills.market_analysis.core import MarketAnalyzer
from skills.report.query_backup import save_query_backup


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
    mcp.tool()(mcp_tool_safe(get_market_analysis_modular))
