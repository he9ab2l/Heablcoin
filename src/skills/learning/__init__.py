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
