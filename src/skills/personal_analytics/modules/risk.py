from __future__ import annotations


from datetime import datetime

from typing import Any, Dict, List, Optional


from ..data_provider import safe_float, parse_datetime


def analyze_risk(trades: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:

    """

    风险分析模块。

    计算最大回撤、风险敞口、连续亏损等风险指标。

    """

    initial_capital = safe_float(params.get("initial_capital"), 10000.0)


    if not trades:

        return {

            "name": "risk",

            "payload": {

                "max_drawdown_pct": 0,

                "max_drawdown_usdt": 0,

                "risk_level": "低",

                "consecutive_losses": 0,

            },

            "markdown": "⚠️ **风险分析**\n\n暂无交易记录",

        }


    # 计算闭合交易

    lots: Dict[str, List[Dict[str, Any]]] = {}

    closed_pnls: List[Dict[str, Any]] = []


    def push_lot(symbol: str, qty: float, price: float, t: Optional[datetime]) -> None:

        lots.setdefault(symbol, []).append({"qty": qty, "price": price, "time": t})


    def pop_close(symbol: str, qty_to_close: float, close_price: float, close_time: Optional[datetime], closing_side: str) -> float:

        remaining = qty_to_close

        pnl_total = 0.0

        book = lots.get(symbol) or []

        while remaining > 1e-12 and book:

            lot = book[0]

            lot_qty = float(lot.get("qty", 0.0))

            if abs(lot_qty) < 1e-12:

                book.pop(0)

                continue

            match_qty = min(remaining, abs(lot_qty))

            entry_price = float(lot.get("price", 0.0))

            direction = "LONG" if lot_qty > 0 else "SHORT"

            if direction == "LONG":

                pnl = (close_price - entry_price) * match_qty

            else:

                pnl = (entry_price - close_price) * match_qty

            remaining -= match_qty

            if lot_qty > 0:

                lot["qty"] = lot_qty - match_qty

            else:

                lot["qty"] = lot_qty + match_qty

            if abs(float(lot.get("qty", 0.0))) < 1e-12:

                book.pop(0)

            closed_pnls.append({"time": close_time, "pnl": pnl})

            pnl_total += pnl

        lots[symbol] = book

        return pnl_total


    def apply_trade(symbol: str, side: str, qty: float, price: float, t: Optional[datetime]) -> None:

        s = (side or "").upper().strip()

        if qty <= 0 or price <= 0:

            return

        book = lots.get(symbol) or []

        long_qty = sum(max(0.0, float(x.get("qty", 0.0))) for x in book)

        short_qty = sum(max(0.0, -float(x.get("qty", 0.0))) for x in book)

        if s == "BUY":

            if short_qty > 1e-12:

                to_close = min(qty, short_qty)

                pop_close(symbol, to_close, price, t, "BUY")

                remain = qty - to_close

                if remain > 1e-12:

                    push_lot(symbol, remain, price, t)

            else:

                push_lot(symbol, qty, price, t)

        elif s == "SELL":

            if long_qty > 1e-12:

                to_close = min(qty, long_qty)

                pop_close(symbol, to_close, price, t, "SELL")

                remain = qty - to_close

                if remain > 1e-12:

                    push_lot(symbol, -remain, price, t)

            else:

                push_lot(symbol, -qty, price, t)


    for r in trades:

        symbol = str(r.get("symbol") or r.get("交易对") or "").strip() or "UNKNOWN"

        side = str(r.get("side") or r.get("方向") or "").strip()

        qty = safe_float(r.get("qty") or r.get("数量"), 0.0)

        price = safe_float(r.get("price") or r.get("价格"), 0.0)

        t = r.get("time") if isinstance(r.get("time"), datetime) else parse_datetime(r.get("时间") or r.get("time"))

        apply_trade(symbol, side, qty, price, t)


    # 计算最大回撤

    equity = initial_capital

    peak = equity

    mdd = 0.0

    mdd_pct = 0.0


    sorted_pnls = sorted(closed_pnls, key=lambda x: x.get("time") or datetime.min)

    for item in sorted_pnls:

        pnl = float(item.get("pnl", 0))

        equity += pnl

        if equity > peak:

            peak = equity

        dd = peak - equity

        if dd > mdd:

            mdd = dd

            mdd_pct = (dd / peak * 100.0) if peak > 0 else 0.0


    # 连续亏损

    max_consecutive_losses = 0

    current_streak = 0

    for item in sorted_pnls:

        if float(item.get("pnl", 0)) < 0:

            current_streak += 1

            max_consecutive_losses = max(max_consecutive_losses, current_streak)

        else:

            current_streak = 0


    # 单笔最大亏损

    max_single_loss = min((float(x.get("pnl", 0)) for x in closed_pnls), default=0)


    # 风险敞口 (当前未平仓)

    open_exposure = 0.0

    for sym, book in lots.items():

        for lot in book:

            qty = abs(float(lot.get("qty", 0)))

            price = float(lot.get("price", 0))

            open_exposure += qty * price


    # 风险等级判断

    if mdd_pct >= 20 or max_consecutive_losses >= 5:

        risk_level = "高"

        risk_color = "🔴"

    elif mdd_pct >= 10 or max_consecutive_losses >= 3:

        risk_level = "中"

        risk_color = "🟡"

    else:

        risk_level = "低"

        risk_color = "🟢"


    # 风险建议

    suggestions = []

    if mdd_pct >= 15:

        suggestions.append("最大回撤较高，建议降低单笔仓位")

    if max_consecutive_losses >= 4:

        suggestions.append("连续亏损次数较多，建议检查策略有效性")

    if open_exposure > initial_capital * 0.5:

        suggestions.append("当前敞口较大，注意风险控制")

    if not suggestions:

        suggestions.append("风险指标正常，继续保持")


    # 生成 markdown

    markdown = (

        f"⚠️ **风险分析**\n"

        f"{'═' * 35}\n\n"

        f"{risk_color} **风险等级**: {risk_level}\n\n"

        f"**回撤指标**\n"

        f"├─ 最大回撤: {mdd:,.2f} USDT ({mdd_pct:.2f}%)\n"

        f"├─ 单笔最大亏损: {max_single_loss:,.2f} USDT\n"

        f"└─ 连续亏损: {max_consecutive_losses} 次\n\n"

        f"**敞口分析**\n"

        f"└─ 当前未平仓敞口: {open_exposure:,.2f} USDT\n\n"

        f"**风险建议**\n"

        + "\n".join([f"├─ {s}" for s in suggestions[:-1]])

        + (f"\n└─ {suggestions[-1]}" if suggestions else "")

    )


    return {

        "name": "risk",

        "payload": {

            "max_drawdown_pct": mdd_pct,

            "max_drawdown_usdt": mdd,

            "max_single_loss": max_single_loss,

            "consecutive_losses": max_consecutive_losses,

            "open_exposure": open_exposure,

            "risk_level": risk_level,

            "suggestions": suggestions,

        },

        "markdown": markdown,

    }


def get_module_info() -> Dict[str, Any]:

    return {

        "name": "risk",

        "title": "风险分析",

        "description": "计算最大回撤、风险敞口、连续亏损等风险指标",

        "version": "1.0.0",

    }


__all__ = ["analyze_risk", "get_module_info"]
