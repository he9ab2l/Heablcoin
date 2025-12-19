############################################################
# 📘 文件说明：
# 本文件实现的功能：MCP tools for strategy registry + attribution.
#
# 📋 程序整体伪代码（中文）：
# 1. 初始化主要依赖与变量
# 2. 加载输入数据或接收外部请求
# 3. 执行主要逻辑步骤（如计算、处理、训练、渲染等）
# 4. 输出或返回结果
# 5. 异常处理与资源释放
#
# 🔄 程序流程图（逻辑流）：
# ┌──────────┐
# │  输入数据 │
# └─────┬────┘
#       ↓
# ┌────────────┐
# │  核心处理逻辑 │
# └─────┬──────┘
#       ↓
# ┌──────────┐
# │  输出结果 │
# └──────────┘
#
# 📊 数据管道说明：
# 数据流向：输入源 → 数据清洗/转换 → 核心算法模块 → 输出目标（文件 / 接口 / 终端）
#
# 🧩 文件结构：
# - 依赖（标准库）：__future__, json, typing
# - 依赖（第三方）：无
# - 依赖（本地）：core.mcp_safety, skills.strategy
#
# 🕒 创建时间：2025-12-19
############################################################

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
