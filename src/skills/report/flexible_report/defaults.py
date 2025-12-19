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
# - 依赖（标准库）：__future__, typing
# - 依赖（第三方）：无
# - 依赖（本地）：.analytics, .state, .trade_log, .utils
#
# 🕒 创建时间：2025-12-19
############################################################

from __future__ import annotations

from typing import Any, Dict

from .state import get_data_providers
from .trade_log import read_trade_log, safe_float
from .analytics import compute_trade_analytics
from .utils import now_str


def provider_call(name: str, **kwargs: Any) -> Any:
    fn = get_data_providers().get(name)
    if fn is None:
        return None
    try:
        return fn(**kwargs)
    except Exception:
        return None


def default_section_a() -> Dict[str, Any]:
    rows = read_trade_log(limit=1)
    if not rows:
        return {"order_id": "", "symbol": "", "side": "", "price": 0, "qty": 0, "cost": 0, "cost_ccy": "USDT", "time": now_str()}
    r = rows[-1]
    qty = safe_float(r.get("数量"), 0.0)
    price = safe_float(r.get("价格"), 0.0)
    cost = safe_float(r.get("总额"), qty * price)
    return {"order_id": r.get("订单ID") or "", "symbol": r.get("交易对") or "", "side": r.get("方向") or "", "price": price, "qty": qty, "cost": cost, "cost_ccy": "USDT", "time": r.get("时间") or now_str()}


def default_section_b() -> Dict[str, Any]:
    data = provider_call("account_snapshot")
    if isinstance(data, dict):
        return data
    return {"total_equity": 0.0, "available_usdt": 0.0, "holdings": []}


def default_section_c(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    symbol = str(kwargs.get("symbol") or kwargs.get("C_symbol") or "BTC/USDT")
    mode = str(kwargs.get("mode") or kwargs.get("C_mode") or "simple")
    data = provider_call("ai_decision", symbol=symbol, mode=mode)
    if isinstance(data, dict):
        return data
    return {"advice": "HOLD", "confidence": 0, "rsi": "", "macd": "", "support": "", "resistance": ""}


def default_section_d(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    rows = read_trade_log(limit=None)
    init_capital = kwargs.get("initial_capital_usdt")
    init_capital_f = None
    try:
        if init_capital is not None:
            init_capital_f = float(init_capital)
    except Exception:
        init_capital_f = None
    stats = compute_trade_analytics(rows, initial_capital_usdt=init_capital_f)
    return {
        "pnl": stats.get("total_pnl", 0.0),
        "pnl_pct": stats.get("roi_pct", 0.0),
        "roi_pct": stats.get("roi_pct", 0.0),
        "win_rate": stats.get("win_rate", 0.0),
        "max_drawdown": stats.get("max_drawdown_pct", 0.0),
        "sharpe": stats.get("sharpe", 0.0),
        "profit_factor": stats.get("profit_factor", 0.0),
        "rr_ratio": stats.get("rr_ratio", 0.0),
        "avg_holding_seconds": stats.get("avg_holding_seconds", 0),
        "attribution": stats.get("attribution", []),
        "review": stats.get("review", []),
    }


def default_section_e(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    d = default_section_d(kwargs)
    mdd = safe_float(d.get("max_drawdown"), 0.0)
    sharpe = safe_float(d.get("sharpe"), 0.0)
    lvl = "低"
    if mdd >= 20 or sharpe < -0.5:
        lvl = "高"
    elif mdd >= 10 or sharpe < 0:
        lvl = "中"
    reasons = [f"Max Drawdown: {mdd:.2f}%", f"Sharpe: {sharpe:.2f}"]
    action = "建议降低单笔风险、控制频次，并核对策略信号与执行差异。"
    return {"level": lvl, "reasons": reasons, "action": action}


def default_section_f() -> Dict[str, Any]:
    rows = read_trade_log(limit=50)
    trades = []
    for r in rows[::-1]:
        qty = safe_float(r.get("数量"), 0.0)
        price = safe_float(r.get("价格"), 0.0)
        cost = safe_float(r.get("总额"), qty * price)
        trades.append({"time": r.get("时间"), "symbol": r.get("交易对"), "side": r.get("方向"), "qty": qty, "price": price, "cost": cost})
    return {"trades": trades}


def default_section_g(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    symbol = str(kwargs.get("symbol") or kwargs.get("G_symbol") or "BTC/USDT")
    data = provider_call("market_sentiment", symbol=symbol)
    if isinstance(data, dict):
        return data
    return {"fear_greed": 50, "label": "中性", "trend": "震荡", "top_gainers": [], "top_losers": []}


def default_section_h(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    symbol = kwargs.get("symbol") or kwargs.get("H_symbol")
    data = provider_call("open_orders", symbol=symbol)
    if isinstance(data, dict):
        return data
    return {"orders": []}


__all__ = [
    "provider_call",
    "default_section_a",
    "default_section_b",
    "default_section_c",
    "default_section_d",
    "default_section_e",
    "default_section_f",
    "default_section_g",
    "default_section_h",
]
