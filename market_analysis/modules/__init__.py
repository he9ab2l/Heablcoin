############################################################
# 📘 文件说明：分析子模块初始化
# 本文件实现的功能：市场分析子模块的包初始化
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
# 数据流向：交易所API → 数据处理 → 指标计算 → 分析结果输出
#
# 🧩 文件结构：
# - 核心逻辑实现
#
# 🔗 主要依赖：__future__, market_analysis
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

from market_analysis.modules.technical_summary import analyze_technical_summary
from market_analysis.modules.trading_signals import analyze_trading_signals
from market_analysis.modules.sentiment import analyze_sentiment
from market_analysis.modules.patterns import detect_patterns
from market_analysis.modules.market_structure import analyze_structure

__all__ = [
    "analyze_technical_summary",
    "analyze_trading_signals",
    "analyze_sentiment",
    "detect_patterns",
    "analyze_structure",
]
