############################################################
# 📘 文件说明：
# 本文件实现的功能：Heablcoin 工具模块
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
# - 依赖（标准库）：无
# - 依赖（第三方）：无
# - 依赖（本地）：.backtesting, .env_helpers, .exchange_adapter, .notifier, .risk_management, .smart_cache, .smart_logger, .validators
#
# 🕒 创建时间：2025-12-19
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

# Environment variable helpers (extracted from Heablcoin.py for reuse)
from .env_helpers import (
    env_str,
    env_int,
    env_float,
    env_bool,
    resolve_path,
    parse_symbols,
)  # noqa: F401

from .validators import (
    parse_price,
    validate_price_condition,
    is_valid_wallet_address,
    normalize_symbol,
)  # noqa: F401

__all__ += [
    'ExchangeAdapter', 'BinanceAdapter', 'OKXAdapter', 'BybitAdapter',
    'run_backtest', 'Notifier', 'ConsoleChannel', 'TelegramChannel', 'NotificationChannel',
    'calculate_position_size', 'trailing_stop', 'PositionSize',
    'env_str', 'env_int', 'env_float', 'env_bool', 'resolve_path', 'parse_symbols',
    'parse_price', 'validate_price_condition', 'is_valid_wallet_address', 'normalize_symbol',
]
