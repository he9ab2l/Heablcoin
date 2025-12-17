from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from collections import defaultdict

from personal_analytics.data_provider import safe_float, parse_datetime


def analyze_costs(trades: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    交易成本核算模块。
    汇总手续费、资金费率、滑点成本等，并分析成本对盈亏的影响。
    """
    if not trades:
        return {
            "name": "costs",
            "payload": {
                "total_fees": 0,
                "fee_breakdown": {},
                "cost_ratio": 0,
            },
            "markdown": "💸 **交易成本分析**\n\n暂无交易记录",
        }
    
    # 汇总各类成本
    total_fees = 0.0
    total_funding = 0.0
    total_volume = 0.0
    
    fee_by_symbol: Dict[str, float] = defaultdict(float)
    fee_by_type: Dict[str, float] = defaultdict(float)
    trades_with_fees = 0
    
    for r in trades:
        symbol = str(r.get("symbol") or r.get("交易对") or "").strip() or "UNKNOWN"
        
        # 手续费
        fee = safe_float(r.get("fee") or r.get("手续费"), 0.0)
        if fee > 0:
            total_fees += fee
            fee_by_symbol[symbol] += fee
            fee_by_type["手续费"] += fee
            trades_with_fees += 1
        
        # 资金费率（合约）
        funding = safe_float(r.get("funding") or r.get("资金费率"), 0.0)
        if funding != 0:
            total_funding += funding
            fee_by_type["资金费率"] += abs(funding)
        
        # 交易量
        qty = safe_float(r.get("qty") or r.get("数量"), 0.0)
        price = safe_float(r.get("price") or r.get("价格"), 0.0)
        cost = safe_float(r.get("cost") or r.get("总额"), qty * price)
        total_volume += cost
    
    # 计算成本占比
    cost_ratio = (total_fees / total_volume * 100) if total_volume > 0 else 0
    avg_fee_per_trade = total_fees / trades_with_fees if trades_with_fees > 0 else 0
    
    # 按币种排序
    fee_by_symbol_sorted = sorted(fee_by_symbol.items(), key=lambda x: x[1], reverse=True)
    
    # 估算滑点成本（基于成交价与预期价差，如果有的话）
    slippage_estimate = 0.0
    # 这里可以根据实际数据计算，暂时设为0
    
    total_cost = total_fees + abs(total_funding) + slippage_estimate
    
    # 生成 markdown
    fee_type_md = ""
    for fee_type, amount in fee_by_type.items():
        fee_type_md += f"├─ {fee_type}: {amount:,.4f} USDT\n"
    if not fee_type_md:
        fee_type_md = "├─ 无费用记录\n"
    
    fee_symbol_md = ""
    for i, (sym, amount) in enumerate(fee_by_symbol_sorted[:5]):
        prefix = "└─" if i == len(fee_by_symbol_sorted[:5]) - 1 else "├─"
        fee_symbol_md += f"{prefix} {sym}: {amount:,.4f} USDT\n"
    if not fee_symbol_md:
        fee_symbol_md = "无数据"
    
    # 成本影响分析
    impact_md = ""
    if cost_ratio >= 1:
        impact_md = "⚠️ 成本占比较高，建议优化交易频率或选择更低费率"
    elif cost_ratio >= 0.5:
        impact_md = "🟡 成本占比中等，可适度关注"
    else:
        impact_md = "🟢 成本控制良好"
    
    markdown = (
        f"💸 **交易成本分析**\n"
        f"{'═' * 40}\n\n"
        f"📊 **成本总览**\n"
        f"├─ 总成本: {total_cost:,.4f} USDT\n"
        f"├─ 总交易量: {total_volume:,.2f} USDT\n"
        f"├─ 成本占比: {cost_ratio:.4f}%\n"
        f"└─ 平均每笔: {avg_fee_per_trade:,.4f} USDT\n\n"
        f"**成本分类**\n{fee_type_md}\n"
        f"**按交易对 (Top 5)**\n{fee_symbol_md}\n"
        f"**成本影响评估**\n└─ {impact_md}"
    )
    
    return {
        "name": "costs",
        "payload": {
            "total_fees": total_fees,
            "total_funding": total_funding,
            "total_volume": total_volume,
            "total_cost": total_cost,
            "cost_ratio": cost_ratio,
            "avg_fee_per_trade": avg_fee_per_trade,
            "trades_with_fees": trades_with_fees,
            "fee_by_symbol": dict(fee_by_symbol),
            "fee_by_type": dict(fee_by_type),
        },
        "markdown": markdown,
    }


def get_module_info() -> Dict[str, Any]:
    return {
        "name": "costs",
        "title": "交易成本分析",
        "description": "汇总手续费、资金费率、滑点成本等，分析成本对盈亏的影响",
        "version": "1.0.0",
    }


__all__ = ["analyze_costs", "get_module_info"]
