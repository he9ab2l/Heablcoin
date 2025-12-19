############################################################
# 📘 文件说明：
# 本文件实现的功能：交易所连接与复用
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
# - 依赖（标准库）：__future__, logging, os, time, typing
# - 依赖（第三方）：ccxt
# - 依赖（本地）：utils.env_helpers
#
# 🕒 创建时间：2025-12-19
############################################################

"""
交易所连接与复用

目标：
- 将交易所连接池从 server.py 中解耦出来，供 tools/skills 复用
- 统一从环境变量读取 CCXT 配置
"""

from __future__ import annotations

import os
import time
import logging
from typing import Any, Optional

import ccxt

from utils.env_helpers import env_bool, env_int, env_str


logger = logging.getLogger(__name__)

EXCHANGE_POOL_TTL_SECONDS = env_int("EXCHANGE_POOL_TTL_SECONDS", 60)
CCXT_TIMEOUT_MS = env_int("CCXT_TIMEOUT_MS", 30000)
CCXT_ENABLE_RATE_LIMIT = env_bool("CCXT_ENABLE_RATE_LIMIT", True)
CCXT_DEFAULT_TYPE = env_str("CCXT_DEFAULT_TYPE", "spot")
CCXT_RECV_WINDOW = env_int("CCXT_RECV_WINDOW", 10000)
CCXT_ADJUST_TIME_DIFFERENCE = env_bool("CCXT_ADJUST_TIME_DIFFERENCE", False)


class ExchangePool:
    """交易所连接池（单例模式）"""

    _instance: Optional["ExchangePool"] = None

    def __new__(cls) -> "ExchangePool":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.exchange = None
            cls._instance.last_used = 0
        return cls._instance

    def get_exchange(self) -> Any:
        current_time = time.time()
        if self.exchange and current_time - self.last_used < EXCHANGE_POOL_TTL_SECONDS:
            self.last_used = current_time
            return self.exchange

        api_key = os.getenv("BINANCE_API_KEY")
        secret = os.getenv("BINANCE_SECRET_KEY")
        use_testnet = os.getenv("USE_TESTNET", "True").lower() == "true"

        self.exchange = ccxt.binance(
            {
                "apiKey": api_key,
                "secret": secret,
                "enableRateLimit": CCXT_ENABLE_RATE_LIMIT,
                "timeout": CCXT_TIMEOUT_MS,
                "options": {
                    "defaultType": CCXT_DEFAULT_TYPE,
                    "adjustForTimeDifference": CCXT_ADJUST_TIME_DIFFERENCE,
                    "recvWindow": CCXT_RECV_WINDOW,
                },
            }
        )

        if use_testnet:
            self.exchange.set_sandbox_mode(True)
            logger.info("已连接 Binance Testnet")
        else:
            logger.info("已连接 Binance 主网")

        self.last_used = current_time
        return self.exchange


def get_exchange() -> Any:
    return ExchangePool().get_exchange()


__all__ = ["ExchangePool", "get_exchange"]
