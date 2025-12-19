############################################################
# 📘 文件说明：
# 本文件实现的功能：Risk management utilities for Heablcoin.
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
# - 依赖（标准库）：__future__, dataclasses, typing
# - 依赖（第三方）：无
# - 依赖（本地）：无
#
# 🕒 创建时间：2025-12-19
############################################################

"""Risk management utilities for Heablcoin.

This module centralizes position sizing and risk control logic for Heablcoin's
trading engine. The goal is to help users define consistent rules for how
much capital to allocate per trade and how to adjust positions based on
market movement. Having these rules encapsulated in a single module makes
it easier to unit test and reason about risk across the system.

Features include:

* Calculation of position size based on account balance, percentage risk per trade
  and distance to stop loss. This helps ensure that a single trade does not
  exceed a configured fraction of the user's capital.
* Support for fixed dollar or fixed quantity position sizing.
* Trailing stop utilities that adjust stop loss levels as the price moves in
  the trade's favor. Trailing stops are useful for locking in profits
  automatically.
* Utility functions for validating that risk parameters are sensible (e.g.
  percentages between 0 and 1).

The functions here are intentionally dependency‑free and use only Python's
standard library. They can therefore be imported and used in any context
within the Heablcoin project.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PositionSize:
    """Container for position sizing output.

    Attributes:
        quantity: The number of units (e.g. coins) to trade.
        notional: The total value of the position in base currency.
    """

    quantity: float
    notional: float


def calculate_position_size(
    balance: float,
    price: float,
    stop_distance: float,
    risk_per_trade: float = 0.02,
    use_fixed_notional: Optional[float] = None,
    use_fixed_quantity: Optional[float] = None,
) -> PositionSize:
    """Calculate the position size based on account balance and risk settings.

    Args:
        balance: The total account balance in base currency (e.g. USD).
        price: The entry price of the asset.
        stop_distance: The distance between the entry price and stop loss (in price units).
            For example, if buying BTC at 20,000 and stop loss is at 19,000, then
            `stop_distance` should be 1,000.
        risk_per_trade: Fraction of the account balance to risk on a single trade.
            Default is 0.02 (i.e. 2% of capital). Must be between 0 and 1.
        use_fixed_notional: If provided, ignore calculated sizing and use this
            notional value directly for the position. Cannot be used with
            `use_fixed_quantity`.
        use_fixed_quantity: If provided, ignore calculated sizing and use this
            quantity directly for the position. Cannot be used with
            `use_fixed_notional`.

    Returns:
        PositionSize: A dataclass containing the quantity and notional size.

    Raises:
        ValueError: If input values are invalid or inconsistent.

    Example:
        >>> calculate_position_size(balance=10000, price=20000, stop_distance=500, risk_per_trade=0.01)
        PositionSize(quantity=1.0, notional=20000)
    """
    if balance <= 0:
        raise ValueError("balance must be positive")
    if price <= 0:
        raise ValueError("price must be positive")
    if stop_distance <= 0:
        raise ValueError("stop_distance must be positive")
    if not (0 < risk_per_trade < 1):
        raise ValueError("risk_per_trade must be between 0 and 1")
    if use_fixed_notional is not None and use_fixed_quantity is not None:
        raise ValueError("Cannot specify both use_fixed_notional and use_fixed_quantity")

    # If fixed sizing provided, compute the other dimension accordingly
    if use_fixed_notional is not None:
        notional = min(use_fixed_notional, balance)
        quantity = notional / price
        return PositionSize(quantity=quantity, notional=notional)
    if use_fixed_quantity is not None:
        quantity = use_fixed_quantity
        notional = quantity * price
        if notional > balance:
            raise ValueError("Fixed quantity position exceeds available balance")
        return PositionSize(quantity=quantity, notional=notional)

    # Normal risk‑based sizing: capital at risk = balance * risk_per_trade
    capital_at_risk = balance * risk_per_trade
    # Each unit of quantity loses stop_distance in price. So quantity = capital_at_risk / stop_distance
    quantity = capital_at_risk / stop_distance
    notional = quantity * price
    # Ensure notional does not exceed available balance
    if notional > balance:
        # Scale down quantity proportionally
        scale = balance / notional
        quantity *= scale
        notional = balance
    return PositionSize(quantity=quantity, notional=notional)


def trailing_stop(current_price: float, peak_price: float, trail_percent: float) -> float:
    """Compute a trailing stop level based on price and peak.

    Args:
        current_price: The current market price of the asset.
        peak_price: The highest price reached since trade entry.
        trail_percent: The trailing distance as a fraction (e.g. 0.05 for 5%).

    Returns:
        float: The stop level. If current price has not exceeded peak, returns
            peak_price * (1 - trail_percent).

    Example:
        >>> trailing_stop(current_price=105, peak_price=110, trail_percent=0.05)
        104.5
    """
    if not (0 < trail_percent < 1):
        raise ValueError("trail_percent must be between 0 and 1")
    if current_price <= 0 or peak_price <= 0:
        raise ValueError("Prices must be positive")
    # The stop is anchored off the peak price. As price rises, the peak grows,
    # pulling up the trailing stop. If price falls, the stop remains fixed at
    # the highest anchor achieved.
    anchor = max(current_price, peak_price)
    stop_level = anchor * (1 - trail_percent)
    return stop_level
