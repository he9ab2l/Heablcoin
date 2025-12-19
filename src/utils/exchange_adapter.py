############################################################
# 📘 文件说明：
# 本文件实现的功能：Unified Exchange Adapter
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
# - 依赖（标准库）：__future__, logging, typing
# - 依赖（第三方）：无
# - 依赖（本地）：无
#
# 🕒 创建时间：2025-12-19
############################################################

"""
Unified Exchange Adapter
------------------------

This module provides a simple abstraction layer over multiple cryptocurrency
exchange APIs. In the initial v2 release only Binance was supported via
ccxt. The adapter in v3 introduces a common interface and stub classes for
additional exchanges such as OKX and Bybit. These stubs allow for easy
extension without breaking existing integrations. If `ccxt` is available,
real API clients are automatically initialised; otherwise a descriptive
exception is raised to indicate that trading functionality is disabled.

Classes
-------
ExchangeAdapter
    Base class defining the common interface for exchanges.

BinanceAdapter
    Implementation of the ExchangeAdapter for the Binance exchange.

OKXAdapter
    Stub implementation for the OKX exchange.

BybitAdapter
    Stub implementation for the Bybit exchange.

Usage
-----
```
from utils.exchange_adapter import BinanceAdapter, OKXAdapter, BybitAdapter

binance = BinanceAdapter(api_key="...", secret="...")
price = binance.get_ticker("BTC/USDT")

okx = OKXAdapter()
try:
    price = okx.get_ticker("ETH/USDT")
except NotImplementedError:
    print("OKX API integration is not yet implemented.")
```

Extending support for a new exchange involves subclassing ExchangeAdapter
and implementing the required methods.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

try:
    import ccxt  # type: ignore
except ImportError:
    ccxt = None  # type: ignore


class ExchangeAdapter:
    """Base class defining the exchange interface."""

    def __init__(self, name: str, api_key: Optional[str] = None, secret: Optional[str] = None) -> None:
        self.name = name
        self.api_key = api_key
        self.secret = secret
        self.client: Any = None
        self._initialise_client()

    def _initialise_client(self) -> None:
        """Initialises the underlying ccxt client if available."""
        if ccxt is None:
            logging.warning(
                "ccxt is not installed; %s adapter will operate in stub mode.", self.name
            )
            return

        try:
            exchange_class = getattr(ccxt, self.name.lower())
            self.client = exchange_class({
                "apiKey": self.api_key or "",
                "secret": self.secret or "",
                "enableRateLimit": True,
            })
        except AttributeError:
            logging.error("Exchange '%s' is not supported by ccxt.", self.name)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Returns the current ticker for a given trading pair.

        Parameters
        ----------
        symbol : str
            The trading pair symbol, e.g., "BTC/USDT".

        Returns
        -------
        dict
            Ticker information.

        Raises
        ------
        NotImplementedError
            If the adapter does not implement this method.
        """
        raise NotImplementedError("get_ticker must be implemented by subclasses")

    def place_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        """Places an order on the exchange.

        This is a high-level wrapper that should be implemented by subclasses.
        Spot and margin orders should be supported. For markets without price
        (market orders) set price to None.
        """
        raise NotImplementedError("place_order must be implemented by subclasses")


class BinanceAdapter(ExchangeAdapter):
    """Adapter implementation for Binance."""

    def __init__(self, api_key: Optional[str] = None, secret: Optional[str] = None) -> None:
        super().__init__("binance", api_key=api_key, secret=secret)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        if self.client is None:
            raise NotImplementedError("Binance client is not available without ccxt")
        return self.client.fetch_ticker(symbol)

    def place_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        if self.client is None:
            raise NotImplementedError("Binance client is not available without ccxt")
        order_type = "market" if price is None else "limit"
        return self.client.create_order(symbol, order_type, side, amount, price)


class OKXAdapter(ExchangeAdapter):
    """Stub adapter for OKX.

    Actual API support can be implemented by subclassing this class and
    overriding the methods below. For now it raises NotImplementedError.
    """

    def __init__(self, api_key: Optional[str] = None, secret: Optional[str] = None) -> None:
        super().__init__("okx", api_key=api_key, secret=secret)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError("OKX integration is not yet implemented")

    def place_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        raise NotImplementedError("OKX integration is not yet implemented")


class BybitAdapter(ExchangeAdapter):
    """Stub adapter for Bybit.

    Actual API support can be implemented by subclassing this class and
    overriding the methods below. For now it raises NotImplementedError.
    """

    def __init__(self, api_key: Optional[str] = None, secret: Optional[str] = None) -> None:
        super().__init__("bybit", api_key=api_key, secret=secret)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError("Bybit integration is not yet implemented")

    def place_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        raise NotImplementedError("Bybit integration is not yet implemented")
