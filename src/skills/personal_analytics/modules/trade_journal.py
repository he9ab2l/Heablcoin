############################################################
# 📘 文件说明：交易日志
# 本文件实现的功能：交易记录和日志管理
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
# - 函数: get_journal_path, load_journal, save_journal, analyze_journal, add_trade_note
#
# 🔗 主要依赖：__future__, datetime, json, os, pathlib, personal_analytics, typing
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..data_provider import safe_float, parse_datetime
from utils.project_paths import PROJECT_ROOT


def get_journal_path() -> Path:
    """获取交易日记文件路径"""
    return PROJECT_ROOT / "trade_journal.json"


def load_journal() -> Dict[str, Any]:
    """加载交易日记"""
    p = get_journal_path()
    if not p.exists():
        return {"notes": {}, "tags": {}}
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"notes": {}, "tags": {}}


def save_journal(data: Dict[str, Any]) -> bool:
    """保存交易日记"""
    p = get_journal_path()
    try:
        with p.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def analyze_journal(trades: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    交易复盘工具模块。
    提供交易筛选、复盘笔记、出入金记录等功能。
    """
    # 加载现有日记
    journal = load_journal()
    notes = journal.get("notes", {})
    
    if not trades:
        return {
            "name": "journal",
            "payload": {
                "trade_count": 0,
                "notes_count": len(notes),
                "recent_trades": [],
                "trades_with_notes": [],
            },
            "markdown": "📓 **交易复盘**\n\n暂无交易记录",
        }
    
    # 筛选参数
    filter_symbol = params.get("filter_symbol")
    filter_side = params.get("filter_side")
    filter_start = params.get("filter_start")
    filter_end = params.get("filter_end")
    filter_min_pnl = params.get("filter_min_pnl")
    filter_max_pnl = params.get("filter_max_pnl")
    
    # 应用筛选
    filtered_trades = []
    for r in trades:
        symbol = str(r.get("symbol") or r.get("交易对") or "").strip()
        side = str(r.get("side") or r.get("方向") or "").upper().strip()
        t = r.get("time") if isinstance(r.get("time"), datetime) else parse_datetime(r.get("时间") or r.get("time"))
        
        # 筛选条件
        if filter_symbol and filter_symbol.upper() not in symbol.upper():
            continue
        if filter_side and filter_side.upper() != side:
            continue
        if filter_start and t and t < filter_start:
            continue
        if filter_end and t and t > filter_end:
            continue
        
        filtered_trades.append({
            "order_id": str(r.get("order_id") or r.get("订单ID") or ""),
            "symbol": symbol,
            "side": side,
            "qty": safe_float(r.get("qty") or r.get("数量"), 0.0),
            "price": safe_float(r.get("price") or r.get("价格"), 0.0),
            "cost": safe_float(r.get("cost") or r.get("总额"), 0.0),
            "fee": safe_float(r.get("fee") or r.get("手续费"), 0.0),
            "time": t.isoformat() if t else None,
            "time_display": t.strftime("%Y-%m-%d %H:%M") if t else "",
        })
    
    # 按时间倒序
    filtered_trades.sort(key=lambda x: x.get("time") or "", reverse=True)
    
    # 获取带笔记的交易
    trades_with_notes = []
    for trade in filtered_trades:
        order_id = trade.get("order_id")
        if order_id and order_id in notes:
            trade["note"] = notes[order_id]
            trades_with_notes.append(trade)
    
    # 最近交易
    recent_trades = filtered_trades[:20]
    
    # 统计
    total_trades = len(filtered_trades)
    buy_count = sum(1 for t in filtered_trades if t["side"] == "BUY")
    sell_count = sum(1 for t in filtered_trades if t["side"] == "SELL")
    
    # 按币种分组统计
    symbol_stats: Dict[str, Dict[str, int]] = {}
    for t in filtered_trades:
        sym = t["symbol"]
        if sym not in symbol_stats:
            symbol_stats[sym] = {"count": 0, "buy": 0, "sell": 0}
        symbol_stats[sym]["count"] += 1
        if t["side"] == "BUY":
            symbol_stats[sym]["buy"] += 1
        else:
            symbol_stats[sym]["sell"] += 1
    
    symbol_stats_sorted = sorted(symbol_stats.items(), key=lambda x: x[1]["count"], reverse=True)
    
    # 生成 markdown
    recent_md = ""
    for i, t in enumerate(recent_trades[:10]):
        side_icon = "🟢" if t["side"] == "BUY" else "🔴"
        has_note = "📝" if t.get("note") else ""
        recent_md += (
            f"├─ {side_icon} {t['time_display']} | {t['symbol']} | "
            f"{t['side']} {t['qty']:.6f} @ ${t['price']:,.4f} {has_note}\n"
        )
    if not recent_md:
        recent_md = "无记录"
    
    symbol_md = ""
    for i, (sym, stats) in enumerate(symbol_stats_sorted[:5]):
        symbol_md += f"├─ {sym}: {stats['count']}笔 (买{stats['buy']}/卖{stats['sell']})\n"
    if not symbol_md:
        symbol_md = "无数据"
    
    notes_md = f"已记录 {len(notes)} 条交易笔记" if notes else "暂无交易笔记"
    
    markdown = (
        f"📓 **交易复盘**\n"
        f"{'═' * 40}\n\n"
        f"📊 **交易统计**\n"
        f"├─ 总交易笔数: {total_trades}\n"
        f"├─ 买入: {buy_count} | 卖出: {sell_count}\n"
        f"└─ {notes_md}\n\n"
        f"**按交易对**\n{symbol_md}\n"
        f"**最近交易**\n{recent_md}\n"
        f"💡 使用 `add_trade_note` 为交易添加复盘笔记"
    )
    
    return {
        "name": "journal",
        "payload": {
            "trade_count": total_trades,
            "buy_count": buy_count,
            "sell_count": sell_count,
            "notes_count": len(notes),
            "symbol_stats": dict(symbol_stats),
            "recent_trades": recent_trades,
            "trades_with_notes": trades_with_notes,
        },
        "markdown": markdown,
    }


def add_trade_note(order_id: str, note: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    为交易添加复盘笔记。
    
    Args:
        order_id: 订单ID
        note: 笔记内容（交易理由、心得、总结等）
        tags: 标签列表（如 "错误", "成功", "止损" 等）
    """
    journal = load_journal()
    
    journal["notes"][order_id] = {
        "note": note,
        "tags": tags or [],
        "created_at": datetime.now().isoformat(),
    }
    
    if save_journal(journal):
        return {"success": True, "message": f"笔记已保存: {order_id}"}
    return {"success": False, "message": "保存失败"}


def search_trades(
    trades: List[Dict[str, Any]],
    symbol: Optional[str] = None,
    side: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    搜索和筛选交易记录。
    """
    results = []
    
    start_dt = parse_datetime(start_date) if start_date else None
    end_dt = parse_datetime(end_date) if end_date else None
    
    for r in trades:
        sym = str(r.get("symbol") or r.get("交易对") or "").strip()
        s = str(r.get("side") or r.get("方向") or "").upper().strip()
        t = r.get("time") if isinstance(r.get("time"), datetime) else parse_datetime(r.get("时间") or r.get("time"))
        cost = safe_float(r.get("cost") or r.get("总额"), 0.0)
        
        if symbol and symbol.upper() not in sym.upper():
            continue
        if side and side.upper() != s:
            continue
        if start_dt and t and t < start_dt:
            continue
        if end_dt and t and t > end_dt:
            continue
        if min_amount is not None and cost < min_amount:
            continue
        if max_amount is not None and cost > max_amount:
            continue
        
        results.append(r)
    
    return results


def get_module_info() -> Dict[str, Any]:
    return {
        "name": "journal",
        "title": "交易复盘",
        "description": "交易记录筛选、复盘笔记、交易统计",
        "version": "1.0.0",
    }


__all__ = ["analyze_journal", "add_trade_note", "search_trades", "get_module_info"]
