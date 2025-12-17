"""学习模块子模块"""
from __future__ import annotations

from learning.modules.pre_trade import PreTradeAuditModule
from learning.modules.in_trade import InTradeCoachModule
from learning.modules.history import HistorySimModule
from learning.modules.growth import GrowthProfileModule
from learning.modules.utility import UtilityModule

__all__ = [
    "PreTradeAuditModule",
    "InTradeCoachModule",
    "HistorySimModule",
    "GrowthProfileModule",
    "UtilityModule",
]
