############################################################
# 📘 文件说明：
# 本文件实现的功能：技能模块：实现 period_stats 相关的业务能力封装与组合调用。
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
# - 依赖（标准库）：__future__, collections, datetime, typing
# - 依赖（第三方）：无
# - 依赖（本地）：..data_provider
#
# 🕒 创建时间：2025-12-19
############################################################

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict

from ..data_provider import safe_float, parse_datetime


def analyze_periods(trades: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    周期性统计模块。
    按日、周、月统计收益，支持自定义周期。
    """
    if not trades:
        return {
            "name": "periods",
            "payload": {
                "daily": {},
                "weekly": {},
                "monthly": {},
                "best_day": None,
                "worst_day": None,
            },
            "markdown": "📅 **周期性统计**\n\n暂无交易记录",
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

    # 按时间分组
    daily_pnl: Dict[str, float] = defaultdict(float)
    weekly_pnl: Dict[str, float] = defaultdict(float)
    monthly_pnl: Dict[str, float] = defaultdict(float)
    daily_trades: Dict[str, int] = defaultdict(int)
    
    for item in closed_pnls:
        t = item.get("time")
        pnl = float(item.get("pnl", 0))
        
        if isinstance(t, datetime):
            day_key = t.strftime("%Y-%m-%d")
            week_key = t.strftime("%Y-W%W")
            month_key = t.strftime("%Y-%m")
            
            daily_pnl[day_key] += pnl
            weekly_pnl[week_key] += pnl
            monthly_pnl[month_key] += pnl
            daily_trades[day_key] += 1
    
    # 找出最佳和最差日
    best_day = max(daily_pnl.items(), key=lambda x: x[1]) if daily_pnl else None
    worst_day = min(daily_pnl.items(), key=lambda x: x[1]) if daily_pnl else None
    
    # 计算统计数据
    total_days = len(daily_pnl)
    profitable_days = sum(1 for v in daily_pnl.values() if v > 0)
    losing_days = sum(1 for v in daily_pnl.values() if v < 0)
    avg_daily_pnl = sum(daily_pnl.values()) / total_days if total_days > 0 else 0
    
    # 最近7天和30天
    now = datetime.now()
    last_7_days = sum(v for k, v in daily_pnl.items() if datetime.strptime(k, "%Y-%m-%d") >= now - timedelta(days=7))
    last_30_days = sum(v for k, v in daily_pnl.items() if datetime.strptime(k, "%Y-%m-%d") >= now - timedelta(days=30))
    
    # 最近几个月
    recent_months = sorted(monthly_pnl.items(), reverse=True)[:6]
    
    # 生成 markdown
    month_md = ""
    for i, (month, pnl) in enumerate(recent_months):
        prefix = "└─" if i == len(recent_months) - 1 else "├─"
        sign = "+" if pnl >= 0 else ""
        color = "🟢" if pnl >= 0 else "🔴"
        month_md += f"{prefix} {month}: {color} {sign}{pnl:,.2f} USDT\n"
    if not month_md:
        month_md = "无数据"
    
    best_day_str = f"{best_day[0]}: +{best_day[1]:,.2f}" if best_day else "无"
    worst_day_str = f"{worst_day[0]}: {worst_day[1]:,.2f}" if worst_day else "无"
    
    markdown = (
        f"📅 **周期性统计**\n"
        f"{'═' * 40}\n\n"
        f"📊 **收益概览**\n"
        f"├─ 最近7天: {'+' if last_7_days >= 0 else ''}{last_7_days:,.2f} USDT\n"
        f"├─ 最近30天: {'+' if last_30_days >= 0 else ''}{last_30_days:,.2f} USDT\n"
        f"└─ 日均收益: {'+' if avg_daily_pnl >= 0 else ''}{avg_daily_pnl:,.2f} USDT\n\n"
        f"**交易日统计**\n"
        f"├─ 总交易天数: {total_days}\n"
        f"├─ 盈利天数: {profitable_days} ({profitable_days/total_days*100:.1f}%)\n" if total_days > 0 else ""
        f"├─ 亏损天数: {losing_days}\n"
        f"├─ 🏆 最佳日: {best_day_str}\n"
        f"└─ 💔 最差日: {worst_day_str}\n\n"
        f"**月度收益 (最近6月)**\n{month_md}"
    )
    
    return {
        "name": "periods",
        "payload": {
            "daily_pnl": dict(daily_pnl),
            "weekly_pnl": dict(weekly_pnl),
            "monthly_pnl": dict(monthly_pnl),
            "daily_trades": dict(daily_trades),
            "total_days": total_days,
            "profitable_days": profitable_days,
            "losing_days": losing_days,
            "avg_daily_pnl": avg_daily_pnl,
            "last_7_days": last_7_days,
            "last_30_days": last_30_days,
            "best_day": {"date": best_day[0], "pnl": best_day[1]} if best_day else None,
            "worst_day": {"date": worst_day[0], "pnl": worst_day[1]} if worst_day else None,
        },
        "markdown": markdown,
    }


def get_module_info() -> Dict[str, Any]:
    return {
        "name": "periods",
        "title": "周期性统计",
        "description": "按日、周、月统计收益，识别最佳和最差交易日",
        "version": "1.0.0",
    }


__all__ = ["analyze_periods", "get_module_info"]
