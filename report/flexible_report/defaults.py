from __future__ import annotations

from typing import Any, Dict

from report.flexible_report.state import get_data_providers
from report.flexible_report.trade_log import read_trade_log, safe_float
from report.flexible_report.analytics import compute_trade_analytics
from report.flexible_report.utils import now_str


def provider_call(name: str, **kwargs: Any) -> Any:
    fn = get_data_providers().get(name)
    if fn is None:
        return None
    try:
        return fn(**kwargs)
    except Exception:
        return None


def default_A() -> Dict[str, Any]:
    rows = read_trade_log(limit=1)
    if not rows:
        return {"order_id": "", "symbol": "", "side": "", "price": 0, "qty": 0, "cost": 0, "cost_ccy": "USDT", "time": now_str()}
    r = rows[-1]
    qty = safe_float(r.get("数量"), 0.0)
    price = safe_float(r.get("价格"), 0.0)
    cost = safe_float(r.get("总额"), qty * price)
    return {"order_id": r.get("订单ID") or "", "symbol": r.get("交易对") or "", "side": r.get("方向") or "", "price": price, "qty": qty, "cost": cost, "cost_ccy": "USDT", "time": r.get("时间") or now_str()}


def default_B() -> Dict[str, Any]:
    data = provider_call("account_snapshot")
    if isinstance(data, dict):
        return data
    return {"total_equity": 0.0, "available_usdt": 0.0, "holdings": []}


def default_C(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    symbol = str(kwargs.get("symbol") or kwargs.get("C_symbol") or "BTC/USDT")
    mode = str(kwargs.get("mode") or kwargs.get("C_mode") or "simple")
    data = provider_call("ai_decision", symbol=symbol, mode=mode)
    if isinstance(data, dict):
        return data
    return {"advice": "HOLD", "confidence": 0, "rsi": "", "macd": "", "support": "", "resistance": ""}


def default_D(kwargs: Dict[str, Any]) -> Dict[str, Any]:
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


def default_E(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    d = default_D(kwargs)
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


def default_F() -> Dict[str, Any]:
    rows = read_trade_log(limit=50)
    trades = []
    for r in rows[::-1]:
        qty = safe_float(r.get("数量"), 0.0)
        price = safe_float(r.get("价格"), 0.0)
        cost = safe_float(r.get("总额"), qty * price)
        trades.append({"time": r.get("时间"), "symbol": r.get("交易对"), "side": r.get("方向"), "qty": qty, "price": price, "cost": cost})
    return {"trades": trades}


def default_G(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    symbol = str(kwargs.get("symbol") or kwargs.get("G_symbol") or "BTC/USDT")
    data = provider_call("market_sentiment", symbol=symbol)
    if isinstance(data, dict):
        return data
    return {"fear_greed": 50, "label": "中性", "trend": "震荡", "top_gainers": [], "top_losers": []}


def default_H(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    symbol = kwargs.get("symbol") or kwargs.get("H_symbol")
    data = provider_call("open_orders", symbol=symbol)
    if isinstance(data, dict):
        return data
    return {"orders": []}


__all__ = [
    "provider_call",
    "default_A",
    "default_B",
    "default_C",
    "default_D",
    "default_E",
    "default_F",
    "default_G",
    "default_H",
]
