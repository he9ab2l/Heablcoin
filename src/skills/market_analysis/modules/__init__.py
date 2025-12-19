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
# - 依赖（本地）：.flow_pressure, .market_quality, .market_structure, .patterns, .sentiment, .structure_quality, .technical_summary, .trading_signals
#
# 🕒 创建时间：2025-12-19
############################################################

from __future__ import annotations

from .technical_summary import analyze_technical_summary
from .trading_signals import analyze_trading_signals
from .sentiment import analyze_sentiment
from .patterns import detect_patterns
from .market_structure import analyze_structure
from .structure_quality import analyze_structure_quality
from .flow_pressure import analyze_flow_pressure
from .market_quality import analyze_market_quality

__all__ = [
    "analyze_technical_summary",
    "analyze_trading_signals",
    "analyze_sentiment",
    "detect_patterns",
    "analyze_structure",
    "analyze_structure_quality",
    "analyze_flow_pressure",
    "analyze_market_quality",
]
