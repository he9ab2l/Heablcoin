from __future__ import annotations
from datetime import datetime
import math
import statistics
from typing import Any, Dict, List, Optional
from ..data_provider import safe_float, parse_datetime


def analyze_performance(trades: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    绩效分析模块。
    计算 ROI、胜率、盈亏比、夏普比率等核心绩效指标。
    """
    initial_capital = params.get("initial_capital")
    if not trades:
        return {
            "name": "performance",
            "payload": {
                "total_pnl": 0,
                "roi_pct": 0,
                "win_rate": 0,
                "total_trades": 0,
            },
            "markdown": "📊 **绩效分析**\n\n暂无交易记录",
        }
    # 计算闭合交易的盈亏
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
            closed.append({
                "symbol": symbol,
                "direction": direction,
                "entry_price": entry_price,
                "exit_price": close_price,
                "qty": match_qty,
                "pnl": pnl,
                "return": ret,
                "holding_seconds": hold_s,
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
    # 计算指标
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
    # 持仓时间
    holding = [int(x.get("holding_seconds") or 0) for x in closed if x.get("holding_seconds") is not None]
    avg_holding_s = int(sum(holding) / len(holding)) if holding else 0
    # 夏普比率
    rets = [float(x.get("return", 0.0)) for x in closed]
    if len(rets) >= 2 and statistics.pstdev(rets) > 0:
        sharpe = (statistics.mean(rets) / statistics.pstdev(rets)) * math.sqrt(len(rets))
    else:
        sharpe = 0.0
    # ROI
    entry_exposure = sum(float(x.get("entry_price", 0.0)) * float(x.get("qty", 0.0)) for x in closed)
    exposure_base = entry_exposure if entry_exposure > 0 else 1.0
    roi_pct = (total_pnl / exposure_base) * 100.0
    # 格式化持仓时间
    holding_txt = "-"
    if avg_holding_s > 0:
        hrs = avg_holding_s // 3600
        mins = (avg_holding_s % 3600) // 60
        holding_txt = f"{hrs}h {mins}m" if hrs else f"{mins}m"
    def fmt_pf(v: Any) -> str:
        try:
            fv = float(v)
            if math.isinf(fv):
                return "∞"
            return f"{fv:.2f}"
        except Exception:
            return str(v)
    # 生成 markdown
    pnl_color = "🟢" if total_pnl >= 0 else "🔴"
    markdown = (
        f"📊 **绩效分析**\n"
        f"{'═' * 35}\n\n"
        f"{pnl_color} **总盈亏**: {total_pnl:+,.2f} USDT ({roi_pct:+.2f}%)\n\n"
        f"**核心指标**\n"
        f"├─ 胜率: {win_rate:.1f}% ({wins}胜/{losses}负)\n"
        f"├─ 盈亏比: {fmt_pf(rr_ratio)}\n"
        f"├─ 盈利因子: {fmt_pf(profit_factor)}\n"
        f"├─ 夏普比率: {sharpe:.2f}\n"
        f"└─ 平均持仓: {holding_txt}\n\n"
        f"**盈亏明细**\n"
        f"├─ 毛利润: +{gross_profit:,.2f} USDT\n"
        f"├─ 毛亏损: {gross_loss:,.2f} USDT\n"
        f"└─ 闭合交易: {closed_cnt} 笔"
    )
    return {
        "name": "performance",
        "payload": {
            "total_pnl": total_pnl,
            "roi_pct": roi_pct,
            "win_rate": win_rate,
            "wins": wins,
            "losses": losses,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "profit_factor": profit_factor,
            "rr_ratio": rr_ratio,
            "sharpe": sharpe,
            "avg_holding_seconds": avg_holding_s,
            "closed_trades": closed_cnt,
        },
        "markdown": markdown,
    }


def get_module_info() -> Dict[str, Any]:
    return {
        "name": "performance",
        "title": "绩效分析",
        "description": "计算 ROI、胜率、盈亏比、夏普比率等核心绩效指标",
        "version": "1.0.0",
    }
__all__ = ["analyze_performance", "get_module_info"]
