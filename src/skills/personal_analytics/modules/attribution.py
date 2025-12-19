from __future__ import annotations


from datetime import datetime

from typing import Any, Dict, List, Optional


from ..data_provider import safe_float, parse_datetime


def analyze_attribution(trades: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:

    """

    盈亏归因分析模块。

    按交易对、时间段、方向等维度分析盈亏来源。

    """

    if not trades:

        return {

            "name": "attribution",

            "payload": {

                "by_symbol": [],

                "by_direction": {},

                "by_weekday": {},

            },

            "markdown": "📈 **盈亏归因**\n\n暂无交易记录",

        }


    # 计算闭合交易

    lots: Dict[str, List[Dict[str, Any]]] = {}

    closed: List[Dict[str, Any]] = []


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

            closed.append({

                "symbol": symbol,

                "direction": direction,

                "pnl": pnl,

                "time": close_time,

            })

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


    # 按交易对归因

    by_symbol: Dict[str, Dict[str, Any]] = {}

    for x in closed:

        sym = str(x.get("symbol") or "UNKNOWN")

        by_symbol.setdefault(sym, {"symbol": sym, "pnl": 0.0, "trades": 0, "wins": 0})

        by_symbol[sym]["pnl"] += float(x.get("pnl", 0.0))

        by_symbol[sym]["trades"] += 1

        if float(x.get("pnl", 0.0)) > 0:

            by_symbol[sym]["wins"] += 1


    symbol_list = []

    for sym, v in by_symbol.items():

        trades_n = int(v.get("trades") or 0)

        wins_n = int(v.get("wins") or 0)

        symbol_list.append({

            "symbol": sym,

            "pnl": float(v.get("pnl", 0.0)),

            "trades": trades_n,

            "win_rate": (wins_n / trades_n * 100.0) if trades_n else 0.0,

        })

    symbol_list.sort(key=lambda d: float(d.get("pnl", 0.0)), reverse=True)


    # 按方向归因

    by_direction = {"LONG": {"pnl": 0.0, "trades": 0}, "SHORT": {"pnl": 0.0, "trades": 0}}

    for x in closed:

        d = x.get("direction", "LONG")

        by_direction[d]["pnl"] += float(x.get("pnl", 0.0))

        by_direction[d]["trades"] += 1


    # 按星期归因

    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    by_weekday: Dict[str, Dict[str, Any]] = {name: {"pnl": 0.0, "trades": 0} for name in weekday_names}

    for x in closed:

        t = x.get("time")

        if isinstance(t, datetime):

            wd = weekday_names[t.weekday()]

            by_weekday[wd]["pnl"] += float(x.get("pnl", 0.0))

            by_weekday[wd]["trades"] += 1


    # 生成 markdown

    top_symbols = symbol_list[:5]

    symbol_md = ""

    for i, s in enumerate(top_symbols):

        prefix = "└─" if i == len(top_symbols) - 1 else "├─"

        pnl_sign = "+" if s["pnl"] >= 0 else ""

        symbol_md += f"{prefix} {s['symbol']}: {pnl_sign}{s['pnl']:,.2f} USDT ({s['trades']}笔, 胜率{s['win_rate']:.0f}%)\n"


    if not symbol_md:

        symbol_md = "无数据"


    long_pnl = by_direction["LONG"]["pnl"]

    short_pnl = by_direction["SHORT"]["pnl"]


    markdown = (

        f"📈 **盈亏归因**\n"

        f"{'═' * 35}\n\n"

        f"**按交易对 (Top 5)**\n{symbol_md}\n"

        f"**按方向**\n"

        f"├─ 做多: {'+' if long_pnl >= 0 else ''}{long_pnl:,.2f} USDT ({by_direction['LONG']['trades']}笔)\n"

        f"└─ 做空: {'+' if short_pnl >= 0 else ''}{short_pnl:,.2f} USDT ({by_direction['SHORT']['trades']}笔)\n\n"

        f"**按星期**\n"

        + "\n".join([f"├─ {wd}: {'+' if by_weekday[wd]['pnl'] >= 0 else ''}{by_weekday[wd]['pnl']:,.2f} ({by_weekday[wd]['trades']}笔)" for wd in weekday_names[:6]])

        + f"\n└─ {weekday_names[6]}: {'+' if by_weekday[weekday_names[6]]['pnl'] >= 0 else ''}{by_weekday[weekday_names[6]]['pnl']:,.2f} ({by_weekday[weekday_names[6]]['trades']}笔)"

    )


    return {

        "name": "attribution",

        "payload": {

            "by_symbol": symbol_list,

            "by_direction": by_direction,

            "by_weekday": by_weekday,

        },

        "markdown": markdown,

    }


def get_module_info() -> Dict[str, Any]:

    return {

        "name": "attribution",

        "title": "盈亏归因",

        "description": "按交易对、方向、时间等维度分析盈亏来源",

        "version": "1.0.0",

    }


__all__ = ["analyze_attribution", "get_module_info"]
