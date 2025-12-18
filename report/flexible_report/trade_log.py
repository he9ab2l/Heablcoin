############################################################
# 📘 文件说明：交易日志报告
# 本文件实现的功能：交易日志的报告生成
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
# 数据流向：输入源 → 数据处理 → 核心算法 → 输出目标
#
# 🧩 文件结构：
# - 函数: trade_log_path, safe_float, parse_dt, read_trade_log
#
# 🔗 主要依赖：__future__, csv, datetime, pathlib, typing
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

from datetime import datetime
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional


def trade_log_path() -> Path:
    here = Path(__file__).resolve().parent.parent.parent
    return here / "trade_history.csv"


def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def parse_dt(s: Any) -> Optional[datetime]:
    raw = str(s or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            continue
    return None


def read_trade_log(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    p = trade_log_path()
    if not p.exists():
        return []
    try:
        with p.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
    except Exception:
        return []

    if len(rows) < 2:
        return []

    header = rows[0]
    data_rows = rows[1:]
    if limit is not None:
        data_rows = data_rows[-int(limit):]

    out: List[Dict[str, Any]] = []
    for r in data_rows:
        rec: Dict[str, Any] = {}
        for i, k in enumerate(header):
            rec[str(k)] = r[i] if i < len(r) else ""
        out.append(rec)
    return out


__all__ = ["trade_log_path", "safe_float", "parse_dt", "read_trade_log"]
