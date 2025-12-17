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
