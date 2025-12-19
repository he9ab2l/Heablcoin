from __future__ import annotations

from datetime import datetime
from collections import Counter
from typing import Any, Dict, List, Optional

from ..data_provider import safe_float, parse_datetime


def analyze_behavior(trades: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    交易行为分析模块。
    分析交易频率、时间分布、偏好等行为特征。
    """
    if not trades:
        return {
            "name": "behavior",
            "payload": {
                "total_trades": 0,
                "avg_trades_per_day": 0,
                "favorite_symbols": [],
                "active_hours": [],
            },
            "markdown": "🎯 **交易行为分析**\n\n暂无交易记录",
        }
    
    # 解析交易时间
    trade_times: List[datetime] = []
    symbols: List[str] = []
    sides: List[str] = []
    
    for r in trades:
        t = r.get("time") if isinstance(r.get("time"), datetime) else parse_datetime(r.get("时间") or r.get("time"))
        if t:
            trade_times.append(t)
        sym = str(r.get("symbol") or r.get("交易对") or "").strip()
        if sym:
            symbols.append(sym)
        side = str(r.get("side") or r.get("方向") or "").upper().strip()
        if side:
            sides.append(side)
    
    total_trades = len(trades)
    
    # 交易频率
    if trade_times:
        min_time = min(trade_times)
        max_time = max(trade_times)
        days_span = max(1, (max_time - min_time).days + 1)
        avg_trades_per_day = total_trades / days_span
    else:
        avg_trades_per_day = 0
        days_span = 0
    
    # 偏好交易对
    symbol_counter = Counter(symbols)
    favorite_symbols = [{"symbol": s, "count": c, "pct": c / total_trades * 100} for s, c in symbol_counter.most_common(5)]
    
    # 买卖比例
    side_counter = Counter(sides)
    buy_count = side_counter.get("BUY", 0)
    sell_count = side_counter.get("SELL", 0)
    buy_ratio = buy_count / total_trades * 100 if total_trades else 0
    
    # 活跃时段分析
    hour_counter = Counter(t.hour for t in trade_times)
    active_hours = [{"hour": h, "count": c} for h, c in sorted(hour_counter.items(), key=lambda x: -x[1])[:5]]
    
    # 最活跃时段
    if active_hours:
        peak_hour = active_hours[0]["hour"]
        peak_period = f"{peak_hour:02d}:00-{(peak_hour+1) % 24:02d}:00"
    else:
        peak_period = "未知"
    
    # 星期分布
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday_counter = Counter(t.weekday() for t in trade_times)
    weekday_dist = {weekday_names[i]: weekday_counter.get(i, 0) for i in range(7)}
    most_active_day = max(weekday_dist.items(), key=lambda x: x[1])[0] if weekday_dist else "未知"
    
    # 交易规模分析
    trade_sizes = [safe_float(r.get("cost") or r.get("总额") or (safe_float(r.get("qty") or r.get("数量")) * safe_float(r.get("price") or r.get("价格")))) for r in trades]
    trade_sizes = [s for s in trade_sizes if s > 0]
    avg_trade_size = sum(trade_sizes) / len(trade_sizes) if trade_sizes else 0
    max_trade_size = max(trade_sizes) if trade_sizes else 0
    min_trade_size = min(trade_sizes) if trade_sizes else 0
    
    # 生成 markdown
    symbols_md = ""
    for i, s in enumerate(favorite_symbols):
        prefix = "└─" if i == len(favorite_symbols) - 1 else "├─"
        symbols_md += f"{prefix} {s['symbol']}: {s['count']}笔 ({s['pct']:.1f}%)\n"
    if not symbols_md:
        symbols_md = "无数据"
    
    hours_md = ", ".join([f"{h['hour']:02d}时({h['count']}笔)" for h in active_hours[:3]]) if active_hours else "无数据"
    
    markdown = (
        f"🎯 **交易行为分析**\n"
        f"{'═' * 35}\n\n"
        f"**交易频率**\n"
        f"├─ 总交易笔数: {total_trades}\n"
        f"├─ 统计天数: {days_span} 天\n"
        f"└─ 日均交易: {avg_trades_per_day:.1f} 笔\n\n"
        f"**偏好交易对**\n{symbols_md}\n"
        f"**买卖分布**\n"
        f"├─ 买入: {buy_count} 笔 ({buy_ratio:.1f}%)\n"
        f"└─ 卖出: {sell_count} 笔 ({100 - buy_ratio:.1f}%)\n\n"
        f"**时间偏好**\n"
        f"├─ 最活跃时段: {peak_period}\n"
        f"├─ 活跃小时: {hours_md}\n"
        f"└─ 最活跃星期: {most_active_day}\n\n"
        f"**交易规模**\n"
        f"├─ 平均规模: {avg_trade_size:,.2f} USDT\n"
        f"├─ 最大单笔: {max_trade_size:,.2f} USDT\n"
        f"└─ 最小单笔: {min_trade_size:,.2f} USDT"
    )

    return {
        "name": "behavior",
        "payload": {
            "total_trades": total_trades,
            "days_span": days_span,
            "avg_trades_per_day": avg_trades_per_day,
            "favorite_symbols": favorite_symbols,
            "buy_count": buy_count,
            "sell_count": sell_count,
            "buy_ratio": buy_ratio,
            "active_hours": active_hours,
            "peak_period": peak_period,
            "most_active_day": most_active_day,
            "weekday_distribution": weekday_dist,
            "avg_trade_size": avg_trade_size,
            "max_trade_size": max_trade_size,
            "min_trade_size": min_trade_size,
        },
        "markdown": markdown,
    }


def get_module_info() -> Dict[str, Any]:
    return {
        "name": "behavior",
        "title": "交易行为分析",
        "description": "分析交易频率、时间分布、偏好等行为特征",
        "version": "1.0.0",
    }


__all__ = ["analyze_behavior", "get_module_info"]
