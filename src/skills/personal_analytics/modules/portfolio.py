############################################################
# 📘 文件说明：组合分析
# 本文件实现的功能：投资组合分析
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
# - 函数: analyze_portfolio, get_module_info
#
# 🔗 主要依赖：__future__, collections, datetime, personal_analytics, typing
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from collections import defaultdict

from ..data_provider import safe_float, parse_datetime


def analyze_portfolio(trades: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    投资组合与持仓分析模块。
    分析资产配置、持仓分布、平均成本、未实现盈亏。
    """
    current_prices = params.get("current_prices") or {}
    account_balance = params.get("account_balance") or {}
    
    if not trades:
        return {
            "name": "portfolio",
            "payload": {
                "total_value_usdt": 0,
                "positions": [],
                "distribution": {},
                "unrealized_pnl": 0,
            },
            "markdown": "💼 **投资组合分析**\n\n暂无交易记录",
        }
    
    # 计算当前持仓和平均成本
    positions: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "symbol": "",
        "qty": 0.0,
        "total_cost": 0.0,
        "avg_cost": 0.0,
        "buy_count": 0,
        "sell_count": 0,
    })
    
    for r in trades:
        symbol = str(r.get("symbol") or r.get("交易对") or "").strip()
        if not symbol:
            continue
        
        side = str(r.get("side") or r.get("方向") or "").upper().strip()
        qty = safe_float(r.get("qty") or r.get("数量"), 0.0)
        price = safe_float(r.get("price") or r.get("价格"), 0.0)
        
        if qty <= 0 or price <= 0:
            continue
        
        pos = positions[symbol]
        pos["symbol"] = symbol
        
        if side == "BUY":
            # 更新平均成本
            old_qty = pos["qty"]
            old_cost = pos["total_cost"]
            new_cost = qty * price
            pos["qty"] = old_qty + qty
            pos["total_cost"] = old_cost + new_cost
            pos["buy_count"] += 1
        elif side == "SELL":
            # 按比例减少持仓
            if pos["qty"] > 0:
                sell_ratio = min(qty / pos["qty"], 1.0)
                pos["total_cost"] *= (1 - sell_ratio)
                pos["qty"] = max(0, pos["qty"] - qty)
            pos["sell_count"] += 1
        
        # 计算平均成本
        if pos["qty"] > 0:
            pos["avg_cost"] = pos["total_cost"] / pos["qty"]
        else:
            pos["avg_cost"] = 0
    
    # 过滤掉零持仓
    active_positions = []
    total_value = 0.0
    total_unrealized_pnl = 0.0
    
    for symbol, pos in positions.items():
        if pos["qty"] > 1e-8:
            # 获取当前价格
            base_symbol = symbol.replace("/USDT", "").replace("USDT", "")
            current_price = current_prices.get(symbol) or current_prices.get(base_symbol) or pos["avg_cost"]
            
            current_value = pos["qty"] * current_price
            cost_basis = pos["total_cost"]
            unrealized_pnl = current_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            active_positions.append({
                "symbol": symbol,
                "qty": pos["qty"],
                "avg_cost": pos["avg_cost"],
                "current_price": current_price,
                "current_value": current_value,
                "cost_basis": cost_basis,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct,
                "buy_count": pos["buy_count"],
                "sell_count": pos["sell_count"],
            })
            
            total_value += current_value
            total_unrealized_pnl += unrealized_pnl
    
    # 按价值排序
    active_positions.sort(key=lambda x: x["current_value"], reverse=True)
    
    # 计算资产分布
    distribution = {}
    for p in active_positions:
        pct = (p["current_value"] / total_value * 100) if total_value > 0 else 0
        distribution[p["symbol"]] = {
            "value": p["current_value"],
            "percentage": pct,
        }
    
    # 添加账户余额（如果有）
    usdt_balance = safe_float(account_balance.get("USDT") or account_balance.get("usdt"), 0)
    if usdt_balance > 0:
        total_value += usdt_balance
        distribution["USDT"] = {
            "value": usdt_balance,
            "percentage": (usdt_balance / total_value * 100) if total_value > 0 else 0,
        }
    
    # 生成 markdown
    positions_md = ""
    for i, p in enumerate(active_positions[:10]):
        prefix = "└─" if i == len(active_positions[:10]) - 1 else "├─"
        pnl_sign = "+" if p["unrealized_pnl"] >= 0 else ""
        pnl_color = "🟢" if p["unrealized_pnl"] >= 0 else "🔴"
        positions_md += (
            f"{prefix} **{p['symbol']}**: {p['qty']:.6f}\n"
            f"   成本: ${p['avg_cost']:,.4f} | 现价: ${p['current_price']:,.4f}\n"
            f"   {pnl_color} 浮盈: {pnl_sign}{p['unrealized_pnl']:,.2f} ({pnl_sign}{p['unrealized_pnl_pct']:.2f}%)\n"
        )
    
    if not positions_md:
        positions_md = "无持仓"
    
    # 资产分布
    dist_md = ""
    sorted_dist = sorted(distribution.items(), key=lambda x: x[1]["percentage"], reverse=True)
    for i, (sym, d) in enumerate(sorted_dist[:5]):
        bar_len = int(d["percentage"] / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        dist_md += f"├─ {sym}: {bar} {d['percentage']:.1f}%\n"
    
    total_pnl_sign = "+" if total_unrealized_pnl >= 0 else ""
    total_pnl_color = "🟢" if total_unrealized_pnl >= 0 else "🔴"
    
    markdown = (
        f"💼 **投资组合分析**\n"
        f"{'═' * 40}\n\n"
        f"📊 **资产总览**\n"
        f"├─ 总资产价值: ${total_value:,.2f} USDT\n"
        f"├─ 持仓数量: {len(active_positions)} 个币种\n"
        f"└─ {total_pnl_color} 总浮盈: {total_pnl_sign}{total_unrealized_pnl:,.2f} USDT\n\n"
        f"**资产分布**\n{dist_md}\n"
        f"**持仓明细**\n{positions_md}"
    )
    
    return {
        "name": "portfolio",
        "payload": {
            "total_value_usdt": total_value,
            "total_unrealized_pnl": total_unrealized_pnl,
            "position_count": len(active_positions),
            "positions": active_positions,
            "distribution": distribution,
        },
        "markdown": markdown,
    }


def get_module_info() -> Dict[str, Any]:
    return {
        "name": "portfolio",
        "title": "投资组合分析",
        "description": "分析资产配置、持仓分布、平均成本、未实现盈亏",
        "version": "1.0.0",
    }


__all__ = ["analyze_portfolio", "get_module_info"]
