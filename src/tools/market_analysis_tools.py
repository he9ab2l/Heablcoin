############################################################
# 📘 文件说明：市场分析MCP工具
# 本文件实现的功能：注册市场分析相关的MCP工具
#
# 📋 程序整体伪代码（中文）：
# 1. 初始化依赖模块和配置
# 2. 定义核心类和函数
# 3. 实现主要业务逻辑
# 4. 提供对外接口
# 5. 异常处理与日志记录
#
# 🔄 程序流程图（逻辑流）：
# ┌──────────────┐
# │  MCP 请求    │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  工具函数处理 │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  返回结果    │
# └──────────────┘
#
# 📊 数据管道说明：
# 数据流向：交易所API → 数据处理 → 指标计算 → 分析结果输出
#
# 🧩 文件结构：
# - 函数: get_market_analysis_modular, register_tools
#
# 🔗 主要依赖：__future__, market_analysis, report, typing
#
# 🕒 创建时间：2025-12-18
############################################################

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
