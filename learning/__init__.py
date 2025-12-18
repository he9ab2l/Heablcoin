############################################################
# 📘 文件说明：学习模块初始化
# 本文件实现的功能：交易学习与复盘模块的包初始化
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
# 🔗 主要依赖：__future__, learning
#
# 🕒 创建时间：2025-12-18
############################################################

"""
Heablcoin 学习模块

提供交易学习、训练、成长画像等功能。
"""
from __future__ import annotations

from learning.registry import LearningRegistry
from learning.modules.pre_trade import PreTradeAuditModule
from learning.modules.in_trade import InTradeCoachModule
from learning.modules.history import HistorySimModule
from learning.modules.growth import GrowthProfileModule
from learning.modules.utility import UtilityModule
from learning.notifier import send_learning_report, send_training_summary, send_daily_learning_report

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
