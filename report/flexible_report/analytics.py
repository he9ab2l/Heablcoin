############################################################
# 📘 文件说明：报告分析
# 本文件实现的功能：报告数据分析功能
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
# - 函数: compute_trade_analytics, push_lot, pop_close, apply_trade
#
# 🔗 主要依赖：__future__, datetime, math, report, statistics, typing
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

from datetime import datetime
import math
import statistics
from typing import Any, Dict, List, Optional

from report.flexible_report.trade_log import parse_dt, safe_float


def compute_trade_analytics(rows: List[Dict[str, Any]], initial_capital_usdt: Optional[float] = None) -> Dict[str, Any]:
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
            entry_time = lot.get("time")
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

            hold_s = None
            if isinstance(entry_time, datetime) and isinstance(close_time, datetime):
                hold_s = max(0, int((close_time - entry_time).total_seconds()))

            entry_value = entry_price * match_qty
            ret = (pnl / entry_value) if entry_value else 0.0
            closed.append(
                {
                    "symbol": symbol,
                    "direction": direction,
                    "entry_time": entry_time.isoformat() if isinstance(entry_time, datetime) else "",
                    "exit_time": close_time.isoformat() if isinstance(close_time, datetime) else "",
                    "qty": match_qty,
                    "entry_price": entry_price,
                    "exit_price": close_price,
                    "pnl": pnl,
                    "return": ret,
                    "holding_seconds": hold_s,
                    "closing_side": closing_side,
                }
            )
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

    for r in rows:
        symbol = str(r.get("交易对") or "").strip() or "UNKNOWN"
        side = str(r.get("方向") or "").strip()
        qty = safe_float(r.get("数量"), 0.0)
        price = safe_float(r.get("价格"), 0.0)
        t = parse_dt(r.get("时间"))
        apply_trade(symbol, side, qty, price, t)

    closed_cnt = len(closed)
    total_pnl = sum(float(x.get("pnl", 0.0)) for x in closed)
    gross_profit = sum(float(x.get("pnl", 0.0)) for x in closed if float(x.get("pnl", 0.0)) > 0)
    gross_loss = sum(float(x.get("pnl", 0.0)) for x in closed if float(x.get("pnl", 0.0)) < 0)
    wins = sum(1 for x in closed if float(x.get("pnl", 0.0)) > 0)
    losses = sum(1 for x in closed if float(x.get("pnl", 0.0)) < 0)
    win_rate = (wins / closed_cnt * 100.0) if closed_cnt else 0.0

    avg_win = (gross_profit / wins) if wins else 0.0
    avg_loss = (gross_loss / losses) if losses else 0.0
    rr_ratio = (avg_win / abs(avg_loss)) if avg_loss else (float("inf") if avg_win else 0.0)
    profit_factor = (gross_profit / abs(gross_loss)) if gross_loss else (float("inf") if gross_profit else 0.0)

    holding = [int(x.get("holding_seconds") or 0) for x in closed if x.get("holding_seconds") is not None]
    avg_holding_s = int(sum(holding) / len(holding)) if holding else 0

    rets = [float(x.get("return", 0.0)) for x in closed]
    if len(rets) >= 2 and statistics.pstdev(rets) > 0:
        sharpe = (statistics.mean(rets) / statistics.pstdev(rets)) * math.sqrt(len(rets))
    else:
        sharpe = 0.0

    entry_exposure = sum(float(x.get("entry_price", 0.0)) * float(x.get("qty", 0.0)) for x in closed)
    exposure_base = entry_exposure if entry_exposure > 0 else 1.0
    roi_pct = (total_pnl / exposure_base) * 100.0

    capital = initial_capital_usdt
    if capital is None:
        capital = exposure_base
    capital = float(capital) if capital and float(capital) > 0 else exposure_base

    eq = capital
    peak = eq
    mdd = 0.0
    mdd_pct = 0.0
    ordered = sorted([(x.get("exit_time") or "", float(x.get("pnl", 0.0))) for x in closed], key=lambda z: z[0])
    for _, pnl in ordered:
        eq += pnl
        if eq > peak:
            peak = eq
        dd = peak - eq
        if dd > mdd:
            mdd = dd
            mdd_pct = (dd / peak * 100.0) if peak > 0 else 0.0

    by_symbol: Dict[str, Dict[str, Any]] = {}
    for x in closed:
        sym = str(x.get("symbol") or "UNKNOWN")
        by_symbol.setdefault(sym, {"symbol": sym, "pnl": 0.0, "trades": 0, "wins": 0})
        by_symbol[sym]["pnl"] += float(x.get("pnl", 0.0))
        by_symbol[sym]["trades"] += 1
        if float(x.get("pnl", 0.0)) > 0:
            by_symbol[sym]["wins"] += 1

    attribution: List[Dict[str, Any]] = []
    for sym, v in by_symbol.items():
        trades_n = int(v.get("trades") or 0)
        wins_n = int(v.get("wins") or 0)
        attribution.append({"symbol": sym, "pnl": float(v.get("pnl", 0.0)), "trades": trades_n, "win_rate": (wins_n / trades_n * 100.0) if trades_n else 0.0})
    attribution.sort(key=lambda d: float(d.get("pnl", 0.0)), reverse=True)

    open_positions = []
    for sym, book in lots.items():
        net = sum(float(l.get("qty", 0.0)) for l in book)
        if abs(net) > 1e-12:
            open_positions.append({"symbol": sym, "net_qty": net, "lots": len(book)})

    review = [f"交易记录条数: {len(rows)}", f"可闭合成交段数: {closed_cnt}"]
    if open_positions:
        review.append(f"未闭合仓位: {len(open_positions)} 个交易对")

    return {
        "total_pnl": total_pnl,
        "roi_pct": roi_pct,
        "win_rate": win_rate,
        "max_drawdown_usdt": mdd,
        "max_drawdown_pct": mdd_pct,
        "sharpe": sharpe,
        "profit_factor": profit_factor,
        "rr_ratio": rr_ratio,
        "avg_holding_seconds": avg_holding_s,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "wins": wins,
        "losses": losses,
        "closed_trades": closed,
        "attribution": attribution,
        "review": review,
        "open_positions": open_positions,
    }


__all__ = ["compute_trade_analytics"]
