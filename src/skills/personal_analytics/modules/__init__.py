############################################################
# 📘 文件说明：个人分析子模块初始化
# 本文件实现的功能：个人分析子模块的包初始化
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
# │  模块导入    │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  导出接口    │
# └──────────────┘
#
# 📊 数据管道说明：
# 数据流向：输入源 → 数据处理 → 核心算法 → 输出目标
#
# 🧩 文件结构：
# - 核心逻辑实现
#
# 🔗 主要依赖：__future__, personal_analytics
#
# 🕒 创建时间：2025-12-18
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
