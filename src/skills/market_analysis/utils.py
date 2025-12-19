############################################################
# 📘 文件说明：
# 本文件实现的功能：市场研究/分析模块：提供数据分析、质量评估与研究辅助能力。
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
# - 依赖（标准库）：__future__, datetime, logging, typing
# - 依赖（第三方）：无
# - 依赖（本地）：无
#
# 🕒 创建时间：2025-12-19
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
