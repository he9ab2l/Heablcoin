############################################################
# 📘 文件说明：交易纪律模块
# 本文件实现的功能：交易纪律检查与提醒功能
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
# - 函数: load_rules, save_rules, load_state, save_state, is_locked_now
#
# 🔗 主要依赖：__future__, json, market_analysis, pathlib, time, typing
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def _base_dir() -> Path:
    here = Path(__file__).resolve().parent.parent
    out = here / "reports" / "execution_guard"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _rules_path() -> Path:
    return _base_dir() / "rules.json"


def _state_path() -> Path:
    return _base_dir() / "state.json"


def load_rules() -> Dict[str, Any]:
    p = _rules_path()
    if not p.exists():
        return {
            "enabled": False,
            "trend_guard": False,
            "trend_timeframe": "1h",
            "cooldown_seconds": 300,
        }
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        return {
            "enabled": False,
            "trend_guard": False,
            "trend_timeframe": "1h",
            "cooldown_seconds": 300,
        }
    except Exception:
        return {
            "enabled": False,
            "trend_guard": False,
            "trend_timeframe": "1h",
            "cooldown_seconds": 300,
        }


def save_rules(rules: Dict[str, Any]) -> bool:
    try:
        _rules_path().write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        return True
    except Exception:
        return False


def load_state() -> Dict[str, Any]:
    p = _state_path()
    if not p.exists():
        return {"locked_until": 0}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        return {"locked_until": 0}
    except Exception:
        return {"locked_until": 0}


def save_state(state: Dict[str, Any]) -> bool:
    try:
        _state_path().write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        return True
    except Exception:
        return False


def is_locked_now() -> Tuple[bool, int]:
    state = load_state()
    now = int(time.time())
    try:
        locked_until = int(state.get("locked_until") or 0)
    except Exception:
        locked_until = 0
    if locked_until > now:
        return True, locked_until - now
    return False, 0


def lock_for_seconds(seconds: int) -> None:
    sec = int(seconds) if seconds and int(seconds) > 0 else 0
    if sec <= 0:
        return
    now = int(time.time())
    save_state({"locked_until": now + sec})


def _trend_label_for(symbol: str, timeframe: str) -> str:
    try:
        from market_analysis.core import MarketAnalyzer
        import json as _json

        s = MarketAnalyzer().analyze(symbol=symbol, timeframe=timeframe, modules=["technical"], return_format="json")
        data = _json.loads(s)
        mods = (data or {}).get("modules") if isinstance(data, dict) else None
        tech = mods.get("technical") if isinstance(mods, dict) else None
        trend = None
        if isinstance(tech, dict):
            trend = tech.get("trend")
        trend = str(trend or "")
        return trend
    except Exception:
        return ""


def evaluate_order(symbol: str, side: str, estimated_cost: float) -> Tuple[bool, str]:
    rules = load_rules()
    enabled = bool(rules.get("enabled"))
    if not enabled:
        return True, ""

    locked, remain = is_locked_now()
    if locked:
        return False, f"⛔ 已触发冷静期，还需等待 {remain} 秒后才能下单"

    if bool(rules.get("trend_guard")):
        tf = str(rules.get("trend_timeframe") or "1h").strip() or "1h"
        trend = _trend_label_for(symbol, tf)
        s = str(side or "").lower().strip()
        if s == "buy" and "看跌" in trend:
            lock_for_seconds(int(rules.get("cooldown_seconds") or 300))
            return False, f"⛔ 纪律拦截：当前趋势偏空（{trend}），已拒绝买入并进入冷静期"
        if s == "sell" and "看涨" in trend:
            lock_for_seconds(int(rules.get("cooldown_seconds") or 300))
            return False, f"⛔ 纪律拦截：当前趋势偏多（{trend}），已拒绝卖出并进入冷静期"

    return True, ""


__all__ = [
    "load_rules",
    "save_rules",
    "load_state",
    "save_state",
    "is_locked_now",
    "lock_for_seconds",
    "evaluate_order",
]
