from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from personal_analytics.data_provider import safe_float, parse_datetime


def get_funds_path() -> Path:
    """获取出入金记录文件路径"""
    return Path(__file__).resolve().parent.parent.parent / "funds_history.json"


def load_funds_history() -> List[Dict[str, Any]]:
    """加载出入金记录"""
    p = get_funds_path()
    if not p.exists():
        return []
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("records", [])
    except Exception:
        return []


def save_funds_history(records: List[Dict[str, Any]]) -> bool:
    """保存出入金记录"""
    p = get_funds_path()
    try:
        with p.open("w", encoding="utf-8") as f:
            json.dump({"records": records}, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def add_funds_record(
    amount: float,
    record_type: str,
    currency: str = "USDT",
    note: str = "",
    date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    添加出入金记录。
    
    Args:
        amount: 金额（正数）
        record_type: 类型 "deposit" (入金) 或 "withdraw" (出金)
        currency: 币种，默认 USDT
        note: 备注
        date: 日期，格式 YYYY-MM-DD，默认今天
    """
    records = load_funds_history()
    
    record_date = date or datetime.now().strftime("%Y-%m-%d")
    
    new_record = {
        "id": f"F{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "type": record_type.lower(),
        "amount": abs(float(amount)),
        "currency": currency.upper(),
        "date": record_date,
        "note": note,
        "created_at": datetime.now().isoformat(),
    }
    
    records.append(new_record)
    
    if save_funds_history(records):
        return {"success": True, "record": new_record}
    return {"success": False, "message": "保存失败"}


def analyze_funds(trades: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    出入金分析模块。
    分析资金流动，计算净入金、净值增长等。
    """
    # 加载出入金记录
    funds_records = load_funds_history()
    
    # 计算总入金和总出金
    total_deposit = sum(r["amount"] for r in funds_records if r.get("type") == "deposit")
    total_withdraw = sum(r["amount"] for r in funds_records if r.get("type") == "withdraw")
    net_deposit = total_deposit - total_withdraw
    
    # 按月份分组
    monthly_funds: Dict[str, Dict[str, float]] = {}
    for r in funds_records:
        date = r.get("date", "")
        if len(date) >= 7:
            month = date[:7]
            if month not in monthly_funds:
                monthly_funds[month] = {"deposit": 0, "withdraw": 0}
            if r.get("type") == "deposit":
                monthly_funds[month]["deposit"] += r["amount"]
            else:
                monthly_funds[month]["withdraw"] += r["amount"]
    
    # 计算已实现盈亏（从交易数据）
    # 这里简化处理，假设总盈亏已在其他模块计算
    total_realized_pnl = params.get("total_realized_pnl", 0)
    
    # 计算净值增长
    # 净值增长 = 当前总资产 - 净入金
    current_balance = safe_float(params.get("current_balance"), 0)
    net_growth = current_balance - net_deposit if current_balance > 0 else total_realized_pnl
    net_growth_pct = (net_growth / net_deposit * 100) if net_deposit > 0 else 0
    
    # 最近记录
    recent_records = sorted(funds_records, key=lambda x: x.get("created_at", ""), reverse=True)[:10]
    
    # 生成 markdown
    recent_md = ""
    for r in recent_records[:5]:
        icon = "📥" if r.get("type") == "deposit" else "📤"
        recent_md += f"├─ {icon} {r.get('date')} | {r.get('type').upper()} | {r.get('amount'):,.2f} {r.get('currency')}\n"
    if not recent_md:
        recent_md = "无出入金记录\n"
    
    # 月度汇总
    monthly_md = ""
    sorted_months = sorted(monthly_funds.items(), reverse=True)[:6]
    for month, data in sorted_months:
        net = data["deposit"] - data["withdraw"]
        sign = "+" if net >= 0 else ""
        monthly_md += f"├─ {month}: 入{data['deposit']:,.0f} | 出{data['withdraw']:,.0f} | 净{sign}{net:,.0f}\n"
    if not monthly_md:
        monthly_md = "无数据\n"
    
    growth_color = "🟢" if net_growth >= 0 else "🔴"
    growth_sign = "+" if net_growth >= 0 else ""
    
    markdown = (
        f"💰 **出入金分析**\n"
        f"{'═' * 40}\n\n"
        f"📊 **资金概览**\n"
        f"├─ 总入金: {total_deposit:,.2f} USDT\n"
        f"├─ 总出金: {total_withdraw:,.2f} USDT\n"
        f"├─ 净入金: {net_deposit:,.2f} USDT\n"
        f"└─ {growth_color} 净值增长: {growth_sign}{net_growth:,.2f} ({growth_sign}{net_growth_pct:.2f}%)\n\n"
        f"**月度汇总**\n{monthly_md}\n"
        f"**最近记录**\n{recent_md}\n"
        f"💡 使用 `add_funds_record` 添加出入金记录"
    )
    
    return {
        "name": "funds",
        "payload": {
            "total_deposit": total_deposit,
            "total_withdraw": total_withdraw,
            "net_deposit": net_deposit,
            "net_growth": net_growth,
            "net_growth_pct": net_growth_pct,
            "record_count": len(funds_records),
            "monthly_funds": monthly_funds,
            "recent_records": recent_records,
        },
        "markdown": markdown,
    }


def get_module_info() -> Dict[str, Any]:
    return {
        "name": "funds",
        "title": "出入金分析",
        "description": "记录和分析资金充值、提现，计算净值增长",
        "version": "1.0.0",
    }


__all__ = ["analyze_funds", "add_funds_record", "load_funds_history", "get_module_info"]
