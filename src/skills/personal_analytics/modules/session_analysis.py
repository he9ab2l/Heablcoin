from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from collections import defaultdict
from ..data_provider import safe_float, parse_datetime


def analyze_sessions(trades: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    交易时段分析模块。
    分析不同时段（亚洲盘、欧洲盘、美洲盘）的交易绩效。
    """
    if not trades:
        return {
            "name": "sessions",
            "payload": {
                "by_session": {},
                "by_hour": {},
                "best_session": None,
                "worst_session": None,
            },
            "markdown": "🌍 **交易时段分析**\n\n暂无交易记录",
        }
    # 定义交易时段 (UTC+8)
    sessions = {
        "亚洲盘": (0, 8),    # 00:00 - 08:00
        "欧洲盘": (8, 16),   # 08:00 - 16:00
        "美洲盘": (16, 24),  # 16:00 - 24:00
    }
    # 计算闭合交易盈亏
    lots: Dict[str, List[Dict[str, Any]]] = {}
    closed_pnls: List[Dict[str, Any]] = []
    def push_lot(symbol: str, qty: float, price: float, t: Optional[datetime]) -> None:
        lots.setdefault(symbol, []).append({"qty": qty, "price": price, "time": t})
    def pop_close(symbol: str, qty_to_close: float, close_price: float, close_time: Optional[datetime]) -> float:
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
                pop_close(symbol, to_close, price, t)
                remain = qty - to_close
                if remain > 1e-12:
                    push_lot(symbol, remain, price, t)
            else:
                push_lot(symbol, qty, price, t)
        elif s == "SELL":
            if long_qty > 1e-12:
                to_close = min(qty, long_qty)
                pop_close(symbol, to_close, price, t)
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
    # 按时段和小时分组
    by_session: Dict[str, Dict[str, Any]] = {name: {"pnl": 0.0, "trades": 0, "wins": 0} for name in sessions}
    by_hour: Dict[int, Dict[str, Any]] = {h: {"pnl": 0.0, "trades": 0, "wins": 0} for h in range(24)}
    for item in closed_pnls:
        t = item.get("time")
        pnl = float(item.get("pnl", 0))
        if isinstance(t, datetime):
            hour = t.hour
            # 按时段分类
            for session_name, (start, end) in sessions.items():
                if start <= hour < end:
                    by_session[session_name]["pnl"] += pnl
                    by_session[session_name]["trades"] += 1
                    if pnl > 0:
                        by_session[session_name]["wins"] += 1
                    break
            # 按小时分类
            by_hour[hour]["pnl"] += pnl
            by_hour[hour]["trades"] += 1
            if pnl > 0:
                by_hour[hour]["wins"] += 1
    # 计算胜率
    for session in by_session.values():
        session["win_rate"] = (session["wins"] / session["trades"] * 100) if session["trades"] > 0 else 0
    for hour_data in by_hour.values():
        hour_data["win_rate"] = (hour_data["wins"] / hour_data["trades"] * 100) if hour_data["trades"] > 0 else 0
    # 找出最佳和最差时段
    active_sessions = [(k, v) for k, v in by_session.items() if v["trades"] > 0]
    best_session = max(active_sessions, key=lambda x: x[1]["pnl"]) if active_sessions else None
    worst_session = min(active_sessions, key=lambda x: x[1]["pnl"]) if active_sessions else None
    # 找出最佳交易小时
    active_hours = [(h, v) for h, v in by_hour.items() if v["trades"] > 0]
    best_hours = sorted(active_hours, key=lambda x: x[1]["pnl"], reverse=True)[:3]
    worst_hours = sorted(active_hours, key=lambda x: x[1]["pnl"])[:3]
    # 生成 markdown
    session_md = ""
    for name in ["亚洲盘", "欧洲盘", "美洲盘"]:
        s = by_session[name]
        if s["trades"] > 0:
            sign = "+" if s["pnl"] >= 0 else ""
            color = "🟢" if s["pnl"] >= 0 else "🔴"
            session_md += f"├─ {name}: {color} {sign}{s['pnl']:,.2f} USDT ({s['trades']}笔, 胜率{s['win_rate']:.0f}%)\n"
        else:
            session_md += f"├─ {name}: 无交易\n"
    best_hours_md = ", ".join([f"{h:02d}时({'+' if v['pnl']>=0 else ''}{v['pnl']:,.0f})" for h, v in best_hours]) if best_hours else "无"
    worst_hours_md = ", ".join([f"{h:02d}时({v['pnl']:,.0f})" for h, v in worst_hours]) if worst_hours else "无"
    # 交易建议
    if best_session and worst_session:
        if best_session[1]["pnl"] > 0 and worst_session[1]["pnl"] < 0:
            advice = f"💡 建议增加 {best_session[0]} 交易，减少 {worst_session[0]} 交易"
        else:
            advice = "💡 各时段表现均衡"
    else:
        advice = "💡 数据不足，暂无建议"
    markdown = (
        f"🌍 **交易时段分析**\n"
        f"{'═' * 40}\n\n"
        f"📊 **时段绩效**\n{session_md}\n"
        f"**最佳交易时间**\n"
        f"├─ 盈利最多: {best_hours_md}\n"
        f"└─ 亏损最多: {worst_hours_md}\n\n"
        f"**交易建议**\n└─ {advice}"
    )
    return {
        "name": "sessions",
        "payload": {
            "by_session": by_session,
            "by_hour": {str(k): v for k, v in by_hour.items()},
            "best_session": {"name": best_session[0], **best_session[1]} if best_session else None,
            "worst_session": {"name": worst_session[0], **worst_session[1]} if worst_session else None,
            "best_hours": [{"hour": h, **v} for h, v in best_hours],
            "worst_hours": [{"hour": h, **v} for h, v in worst_hours],
        },
        "markdown": markdown,
    }


def get_module_info() -> Dict[str, Any]:
    return {
        "name": "sessions",
        "title": "交易时段分析",
        "description": "分析亚洲盘、欧洲盘、美洲盘的交易绩效差异",
        "version": "1.0.0",
    }
__all__ = ["analyze_sessions", "get_module_info"]
