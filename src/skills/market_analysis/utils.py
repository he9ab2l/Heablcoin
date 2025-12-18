############################################################
# 📘 文件说明：分析工具函数
# 本文件实现的功能：市场分析的通用工具函数
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
# │  输入数据    │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  核心处理逻辑 │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  输出结果    │
# └──────────────┘
#
# 📊 数据管道说明：
# 数据流向：交易所API → 数据处理 → 指标计算 → 分析结果输出
#
# 🧩 文件结构：
# - 函数: utcnow, now_ts, safe_float, get_logger, env_int
#
# 🔗 主要依赖：__future__, datetime, logging, os, typing
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def now_ts() -> float:
    return utcnow().timestamp()


def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def env_int(name: str, default: int) -> int:
    import os

    v = os.getenv(name)
    if v is None:
        return default
    try:
        return int(v)
    except Exception:
        return default


def clamp(v: float, lo: float, hi: float) -> float:
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v
