############################################################
# 📘 文件说明：
# 本文件实现的功能：MCP 相关模块：定义/封装工具调用并强化 stdout 协议安全。
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
# - 依赖（标准库）：__future__, typing
# - 依赖（第三方）：无
# - 依赖（本地）：core.mcp_safety, skills.market_analysis.core, skills.report.query_backup
#
# 🕒 创建时间：2025-12-19
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
