"""MCP tools for strategy registry + attribution."""

from __future__ import annotations

import json
from typing import Any

from core.mcp_safety import mcp_tool_safe
from skills.strategy import StrategyRegistry, StrategyPerformanceTracker


def register_tools(mcp: Any) -> None:
    registry = StrategyRegistry()
    performance = StrategyPerformanceTracker()

    @mcp.tool()
    @mcp_tool_safe
    def register_strategy(
        name: str,
        version: str,
        owner: str,
        symbol: str,
        timeframe: str,
        direction: str,
        risk_level: str = "medium",
        description: str = "",
        tags: str = "",
    ) -> str:
        """注册/更新策略元数据。"""
        record = registry.register(
            name=name,
            version=version,
            owner=owner,
            symbol=symbol,
            timeframe=timeframe,
            direction=direction,
            risk_level=risk_level,
            description=description,
            tags=[t.strip() for t in tags.split(",") if t.strip()],
        )
        return json.dumps({"strategy": record.to_dict()}, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def set_strategy_enabled(name: str, enabled: bool) -> str:
        """切换策略启用状态。"""
        record = registry.set_enabled(name=name, enabled=enabled)
        return json.dumps({"strategy": record.to_dict()}, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def list_strategies(filter_active: bool = False, include_conflicts: bool = True) -> str:
        """列出策略清单并附带冲突检测。"""
        payload = registry.list(filter_active=filter_active, include_conflicts=include_conflicts)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def record_strategy_performance(name: str, pnl: float, exposure_minutes: float = 0.0, tags: str = "") -> str:
        """记录策略实盘表现（盈亏/持仓时长）。"""
        payload = performance.record_trade(
            name=name,
            pnl=pnl,
            exposure_minutes=exposure_minutes,
            tags=[t.strip() for t in tags.split(",") if t.strip()],
        )
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def strategy_performance_report() -> str:
        """输出策略绩效归因汇总。"""
        payload = performance.report()
        return json.dumps(payload, ensure_ascii=False, indent=2)


__all__ = ["register_tools"]
