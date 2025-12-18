############################################################
# 📘 文件说明：市场结构分析
# 本文件实现的功能：支撑阻力、趋势结构分析
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
# 数据流向：交易所API → 数据处理 → 指标计算 → 分析结果输出
#
# 🧩 文件结构：
# - 函数: analyze_structure, get_module_info
#
# 🔗 主要依赖：__future__, market_analysis, typing
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..data_provider import StandardMarketData


def analyze_structure(data: StandardMarketData, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    市场结构分析模块。
    识别支撑阻力位、趋势结构、关键价位。
    """
    symbol = str(data.metadata.get("symbol") or "BTC/USDT")
    df = data.df
    
    if df is None or len(df) < 20:
        return {
            "name": "structure",
            "payload": {
                "symbol": symbol,
                "structure": "unknown",
                "support_levels": [],
                "resistance_levels": [],
                "key_levels": [],
            },
            "markdown": f"🏗️ **{symbol} 市场结构**\n\n数据不足，无法分析结构",
        }
    
    closes = df["close"].tolist()
    highs = df["high"].tolist()
    lows = df["low"].tolist()
    current_price = closes[-1] if closes else 0
    
    # 识别局部高点和低点
    swing_highs: List[float] = []
    swing_lows: List[float] = []
    
    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            swing_highs.append(highs[i])
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            swing_lows.append(lows[i])
    
    # 确定支撑位 (低于当前价格的摆动低点)
    support_levels = sorted([l for l in swing_lows if l < current_price], reverse=True)[:3]
    
    # 确定阻力位 (高于当前价格的摆动高点)
    resistance_levels = sorted([h for h in swing_highs if h > current_price])[:3]
    
    # 关键价位 (整数关口)
    key_levels: List[Dict[str, Any]] = []
    price_magnitude = 10 ** (len(str(int(current_price))) - 2)
    round_price = round(current_price / price_magnitude) * price_magnitude
    
    for offset in [-2, -1, 0, 1, 2]:
        level = round_price + offset * price_magnitude
        if level > 0:
            distance_pct = (level - current_price) / current_price * 100
            key_levels.append({
                "price": level,
                "type": "round_number",
                "distance_pct": round(distance_pct, 2),
            })
    
    # 判断市场结构
    if len(closes) >= 50:
        sma20 = sum(closes[-20:]) / 20
        sma50 = sum(closes[-50:]) / 50
        
        # 检查高点低点序列
        recent_highs = swing_highs[-4:] if len(swing_highs) >= 4 else swing_highs
        recent_lows = swing_lows[-4:] if len(swing_lows) >= 4 else swing_lows
        
        higher_highs = all(recent_highs[i] > recent_highs[i-1] for i in range(1, len(recent_highs))) if len(recent_highs) >= 2 else False
        higher_lows = all(recent_lows[i] > recent_lows[i-1] for i in range(1, len(recent_lows))) if len(recent_lows) >= 2 else False
        lower_highs = all(recent_highs[i] < recent_highs[i-1] for i in range(1, len(recent_highs))) if len(recent_highs) >= 2 else False
        lower_lows = all(recent_lows[i] < recent_lows[i-1] for i in range(1, len(recent_lows))) if len(recent_lows) >= 2 else False
        
        if higher_highs and higher_lows:
            structure = "uptrend"
            structure_label = "上升趋势"
        elif lower_highs and lower_lows:
            structure = "downtrend"
            structure_label = "下降趋势"
        elif sma20 > sma50 * 1.01:
            structure = "bullish_bias"
            structure_label = "偏多震荡"
        elif sma20 < sma50 * 0.99:
            structure = "bearish_bias"
            structure_label = "偏空震荡"
        else:
            structure = "ranging"
            structure_label = "区间震荡"
    else:
        structure = "unknown"
        structure_label = "未知"
    
    # 计算价格区间
    recent_high = max(highs[-20:]) if len(highs) >= 20 else max(highs)
    recent_low = min(lows[-20:]) if len(lows) >= 20 else min(lows)
    price_range = recent_high - recent_low
    position_in_range = (current_price - recent_low) / price_range * 100 if price_range > 0 else 50
    
    # 生成摘要
    support_str = ", ".join([f"${s:,.2f}" for s in support_levels[:2]]) if support_levels else "无"
    resistance_str = ", ".join([f"${r:,.2f}" for r in resistance_levels[:2]]) if resistance_levels else "无"
    
    summary = f"{symbol} 当前结构: {structure_label}，价格位于近期区间 {position_in_range:.0f}% 位置。支撑: {support_str}，阻力: {resistance_str}"
    
    # 生成 markdown
    support_md = "\n".join([f"├─ ${s:,.2f} ({(current_price - s) / current_price * 100:.2f}% 下方)" for s in support_levels[:-1]]) if len(support_levels) > 1 else ""
    if support_levels:
        support_md += f"\n└─ ${support_levels[-1]:,.2f} ({(current_price - support_levels[-1]) / current_price * 100:.2f}% 下方)" if support_md else f"└─ ${support_levels[-1]:,.2f}"
    else:
        support_md = "无明显支撑"
    
    resistance_md = "\n".join([f"├─ ${r:,.2f} ({(r - current_price) / current_price * 100:.2f}% 上方)" for r in resistance_levels[:-1]]) if len(resistance_levels) > 1 else ""
    if resistance_levels:
        resistance_md += f"\n└─ ${resistance_levels[-1]:,.2f} ({(resistance_levels[-1] - current_price) / current_price * 100:.2f}% 上方)" if resistance_md else f"└─ ${resistance_levels[-1]:,.2f}"
    else:
        resistance_md = "无明显阻力"
    
    markdown = (
        f"🏗️ **{symbol} 市场结构**\n"
        f"{'═' * 35}\n\n"
        f"💰 **当前价格**: ${current_price:,.2f}\n"
        f"📈 **结构判断**: {structure_label}\n"
        f"📊 **区间位置**: {position_in_range:.0f}% (高: ${recent_high:,.2f}, 低: ${recent_low:,.2f})\n\n"
        f"**支撑位**\n{support_md}\n\n"
        f"**阻力位**\n{resistance_md}"
    )
    
    return {
        "name": "structure",
        "payload": {
            "symbol": symbol,
            "current_price": current_price,
            "structure": structure,
            "structure_label": structure_label,
            "support_levels": [{"price": s, "distance_pct": round((current_price - s) / current_price * 100, 2)} for s in support_levels],
            "resistance_levels": [{"price": r, "distance_pct": round((r - current_price) / current_price * 100, 2)} for r in resistance_levels],
            "key_levels": key_levels,
            "price_range": {
                "high": recent_high,
                "low": recent_low,
                "position_pct": round(position_in_range, 1),
            },
        },
        "markdown": markdown,
    }


def get_module_info() -> Dict[str, Any]:
    return {
        "name": "market_structure",
        "title": "市场结构分析",
        "description": "识别支撑阻力位、趋势结构、关键价位",
        "version": "1.0.0",
    }


__all__ = ["analyze_structure", "get_module_info"]
