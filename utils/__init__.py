############################################################
# 📘 文件说明：工具模块初始化
# 本文件实现的功能：通用工具模块的包初始化
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
# 🔗 主要依赖：backtesting, exchange_adapter, notifier, risk_management, smart_cache, smart_logger
#
# 🕒 创建时间：2025-12-18
############################################################

"""
Heablcoin 工具模块
"""

from .smart_logger import get_smart_logger, log_performance
from .smart_cache import get_smart_cache, cached

# Expose legacy utilities
__all__ = ['get_smart_logger', 'log_performance', 'get_smart_cache', 'cached']

# v3 additions: unify exchange API, backtesting and notification utilities
from .exchange_adapter import ExchangeAdapter, BinanceAdapter, OKXAdapter, BybitAdapter  # noqa: F401
from .backtesting import run_backtest  # noqa: F401
from .notifier import (
    Notifier,
    ConsoleChannel,
    TelegramChannel,
    NotificationChannel,
)  # noqa: F401

# Import risk management utilities into package namespace
from .risk_management import calculate_position_size, trailing_stop, PositionSize  # noqa: F401

__all__ += [
    'ExchangeAdapter', 'BinanceAdapter', 'OKXAdapter', 'BybitAdapter',
    'run_backtest', 'Notifier', 'ConsoleChannel', 'TelegramChannel', 'NotificationChannel',
    # v4 additions: risk management utilities
    'calculate_position_size', 'trailing_stop', 'PositionSize'
]
