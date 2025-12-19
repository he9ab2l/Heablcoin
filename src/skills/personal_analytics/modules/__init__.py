############################################################
# 📘 文件说明：
# 本文件实现的功能：包初始化：聚合导出符号并提供稳定的导入入口。
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
# - 依赖（标准库）：__future__
# - 依赖（第三方）：无
# - 依赖（本地）：.attribution, .cost_analysis, .funds_flow, .performance, .period_stats, .portfolio, .risk, .session_analysis, .trade_journal, .trading_behavior
#
# 🕒 创建时间：2025-12-19
############################################################

from __future__ import annotations

from .performance import analyze_performance
from .risk import analyze_risk
from .attribution import analyze_attribution
from .trading_behavior import analyze_behavior
from .portfolio import analyze_portfolio
from .cost_analysis import analyze_costs
from .period_stats import analyze_periods
from .session_analysis import analyze_sessions
from .trade_journal import analyze_journal, add_trade_note, search_trades
from .funds_flow import analyze_funds, add_funds_record

__all__ = [
    "analyze_performance",
    "analyze_risk",
    "analyze_attribution",
    "analyze_behavior",
    "analyze_portfolio",
    "analyze_costs",
    "analyze_periods",
    "analyze_sessions",
    "analyze_journal",
    "analyze_funds",
    "add_trade_note",
    "add_funds_record",
    "search_trades",
]
