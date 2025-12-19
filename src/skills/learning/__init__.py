############################################################
# 📘 文件说明：
# 本文件实现的功能：Heablcoin 学习模块
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
# - 依赖（本地）：.modules.growth, .modules.history, .modules.in_trade, .modules.pre_trade, .modules.utility, .notifier, .registry
#
# 🕒 创建时间：2025-12-19
############################################################

"""
Heablcoin 学习模块

提供交易学习、训练、成长画像等功能。
"""
from __future__ import annotations

from .registry import LearningRegistry
from .modules.pre_trade import PreTradeAuditModule
from .modules.in_trade import InTradeCoachModule
from .modules.history import HistorySimModule
from .modules.growth import GrowthProfileModule
from .modules.utility import UtilityModule
from .notifier import send_learning_report, send_training_summary, send_daily_learning_report

__all__ = [
    "LearningRegistry",
    "PreTradeAuditModule",
    "InTradeCoachModule",
    "HistorySimModule",
    "GrowthProfileModule",
    "UtilityModule",
    "send_learning_report",
    "send_training_summary",
    "send_daily_learning_report",
]
