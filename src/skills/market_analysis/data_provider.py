############################################################
# 📘 文件说明：
# 本文件实现的功能：交易所相关模块：封装行情/下单/账户等接口访问能力。
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
# - 依赖（第三方）：pandas
# - 依赖（本地）：.state_manager
#
# 🕒 创建时间：2025-12-19
############################################################

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from .state_manager import get_state


@dataclass
class StandardMarketData:
    ohlcv: List[List[Any]]
    ticker: Optional[Dict[str, Any]]
    df: pd.DataFrame
    metadata: Dict[str, Any]


class DataProvider:
    _instance: Optional["DataProvider"] = None

    def __init__(self, exchange_getter: Optional[Callable[[], Any]] = None) -> None:
        self._exchange_getter = exchange_getter

    @classmethod
    def instance(cls) -> "DataProvider":
        if cls._instance is None:
            cls._instance = DataProvider()
        return cls._instance

    def set_exchange_getter(self, exchange_getter: Optional[Callable[[], Any]]) -> None:
        self._exchange_getter = exchange_getter

    def _get_exchange(self) -> Any:
        if self._exchange_getter is not None:
            return self._exchange_getter()
        from core.exchange import get_exchange

        return get_exchange()

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[List[Any]]:
        state = get_state()

        def key_fn(_symbol: str, _timeframe: str, _limit: int = 100) -> str:
            return f"ohlcv:{_symbol}:{_timeframe}:{int(_limit)}"

        @state.cache.cached(ttl_seconds=300, key_prefix="ma:", key_fn=key_fn)
        def _fetch(_symbol: str, _timeframe: str, _limit: int = 100) -> List[List[Any]]:
            ex = self._get_exchange()
            return ex.fetch_ohlcv(_symbol, _timeframe, limit=int(_limit))

        return _fetch(symbol, timeframe, limit)

    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        state = get_state()

        def key_fn(_symbol: str) -> str:
            return f"ticker:{_symbol}"

        @state.cache.cached(ttl_seconds=15, key_prefix="ma:", key_fn=key_fn)
        def _fetch(_symbol: str) -> Dict[str, Any]:
            ex = self._get_exchange()
            return ex.fetch_ticker(_symbol)

        return _fetch(symbol)

    def get_standard_data(self, symbol: str, timeframe: str, limit: int = 100, include_ticker: bool = True) -> StandardMarketData:
        ohlcv = self.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        ticker = self.fetch_ticker(symbol) if include_ticker else None
        meta = {"symbol": symbol, "timeframe": timeframe, "limit": int(limit)}
        return StandardMarketData(ohlcv=ohlcv, ticker=ticker, df=df, metadata=meta)
