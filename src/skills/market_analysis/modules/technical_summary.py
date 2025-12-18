############################################################
# 📘 文件说明：技术总结
# 本文件实现的功能：技术分析综合总结
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
# - 函数: analyze_technical_summary
#
# 🔗 主要依赖：__future__, market_analysis, typing
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

from typing import Any, Dict

from ..data_provider import StandardMarketData
from ..indicators.pipeline import calculate_indicators


def analyze_technical_summary(data: StandardMarketData, params: Dict[str, Any]) -> Dict[str, Any]:
    df = calculate_indicators(data.df.copy())
    if len(df) < 2:
        return {"name": "technical", "error": "not_enough_data"}

    curr = df.iloc[-1]
    prev = df.iloc[-2]
    price = float(curr["close"])

    trend = "🟢 看涨" if price > curr["SMA_20"] > curr["SMA_50"] else "🔴 看跌" if price < curr["SMA_20"] < curr["SMA_50"] else "🟡 震荡"

    rsi = float(curr["RSI"])
    rsi_state = "⚠️ 超买" if rsi > 70 else "💎 超卖" if rsi < 30 else "中性"

    macd_signal = (
        "📈 金叉"
        if curr["MACD_Line"] > curr["Signal_Line"] and prev["MACD_Line"] <= prev["Signal_Line"]
        else "📉 死叉"
        if curr["MACD_Line"] < curr["Signal_Line"] and prev["MACD_Line"] >= prev["Signal_Line"]
        else "多头"
        if curr["MACD_Hist"] > 0
        else "空头"
    )

    bb_pos = (price - float(curr["BB_Lower"])) / (float(curr["BB_Upper"]) - float(curr["BB_Lower"])) * 100
    bb_state = "上轨" if bb_pos > 80 else "下轨" if bb_pos < 20 else "中轨"

    vol_ratio = float(curr.get("Volume_Ratio", 0) or 0)
    vol_state = "放量 📊" if vol_ratio > 1.5 else "缩量" if vol_ratio < 0.5 else "正常"

    change_24h = 0.0
    if isinstance(data.ticker, dict):
        try:
            change_24h = float(data.ticker.get("percentage", 0) or 0)
        except Exception:
            change_24h = 0.0

    symbol = str(data.metadata.get("symbol") or "")
    timeframe = str(data.metadata.get("timeframe") or "")

    markdown = (
        f"📊 **{symbol} 技术分析** ({timeframe})\n"
        f"{'═' * 35}\n\n"
        f"💰 **价格**: ${price:,.2f} ({'+' if change_24h >= 0 else ''}{change_24h:.2f}% 24h)\n"
        f"📈 **趋势**: {trend}\n\n"
        f"**技术指标**\n"
        f"├─ RSI(14): {rsi:.1f} ({rsi_state})\n"
        f"├─ MACD: {macd_signal} ({float(curr['MACD_Hist']):.4f})\n"
        f"├─ 布林带: {bb_state} ({bb_pos:.0f}%)\n"
        f"├─ ATR(14): {float(curr['ATR']):.2f}\n"
        f"└─ 成交量: {vol_state} ({vol_ratio:.1f}x)\n\n"
        f"**均线**\n"
        f"├─ SMA7: ${float(curr['SMA_7']):.2f}\n"
        f"├─ SMA20: ${float(curr['SMA_20']):.2f}\n"
        f"└─ SMA50: ${float(curr['SMA_50']):.2f}"
    )

    payload = {
        "price": price,
        "change_24h": change_24h,
        "trend": trend,
        "rsi": rsi,
        "rsi_state": rsi_state,
        "macd_signal": macd_signal,
        "bb_pos": bb_pos,
        "bb_state": bb_state,
        "atr": float(curr["ATR"]),
        "volume_ratio": vol_ratio,
        "volume_state": vol_state,
    }

    return {"name": "technical", "payload": payload, "markdown": markdown}
