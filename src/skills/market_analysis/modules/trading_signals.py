############################################################
# 📘 文件说明：交易信号
# 本文件实现的功能：买卖信号生成与评估
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
# - 函数: analyze_trading_signals
#
# 🔗 主要依赖：__future__, market_analysis, typing
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ..data_provider import StandardMarketData
from ..indicators.pipeline import calculate_indicators


def analyze_trading_signals(data: StandardMarketData, params: Dict[str, Any]) -> Dict[str, Any]:
    df = calculate_indicators(data.df.copy())
    if len(df) < 2:
        return {"name": "signals", "error": "not_enough_data"}

    curr = df.iloc[-1]
    prev = df.iloc[-2]

    signals: List[Tuple[str, str, str]] = []
    buy_count = 0
    sell_count = 0
    neutral_count = 0

    if float(curr["RSI"]) < 30:
        signals.append(("RSI", "买入", "超卖区域"))
        buy_count += 1
    elif float(curr["RSI"]) > 70:
        signals.append(("RSI", "卖出", "超买区域"))
        sell_count += 1
    else:
        signals.append(("RSI", "中性", f"数值 {float(curr['RSI']):.0f}"))
        neutral_count += 1

    if float(curr["SMA_7"]) > float(curr["SMA_20"]) and float(prev["SMA_7"]) <= float(prev["SMA_20"]):
        signals.append(("SMA 交叉", "买入", "短期均线上穿"))
        buy_count += 1
    elif float(curr["SMA_7"]) < float(curr["SMA_20"]) and float(prev["SMA_7"]) >= float(prev["SMA_20"]):
        signals.append(("SMA 交叉", "卖出", "短期均线下穿"))
        sell_count += 1
    else:
        signals.append(("SMA 交叉", "中性", "无交叉"))
        neutral_count += 1

    if float(curr["MACD_Line"]) > float(curr["Signal_Line"]):
        signals.append(("MACD", "买入", "MACD 在信号线上方"))
        buy_count += 1
    else:
        signals.append(("MACD", "卖出", "MACD 在信号线下方"))
        sell_count += 1

    if float(curr["close"]) < float(curr["BB_Lower"]):
        signals.append(("布林带", "买入", "跌破下轨"))
        buy_count += 1
    elif float(curr["close"]) > float(curr["BB_Upper"]):
        signals.append(("布林带", "卖出", "突破上轨"))
        sell_count += 1
    else:
        signals.append(("布林带", "中性", "在轨道内"))
        neutral_count += 1

    if float(curr.get("Volume_Ratio", 0) or 0) > 1.5 and float(curr["close"]) > float(prev["close"]):
        signals.append(("成交量", "买入", "放量上涨"))
        buy_count += 1
    elif float(curr.get("Volume_Ratio", 0) or 0) > 1.5 and float(curr["close"]) < float(prev["close"]):
        signals.append(("成交量", "卖出", "放量下跌"))
        sell_count += 1
    else:
        signals.append(("成交量", "中性", "量能正常"))
        neutral_count += 1

    if float(curr["close"]) > float(curr["SMA_20"]) > float(curr["SMA_50"]):
        signals.append(("趋势", "买入", "多头排列"))
        buy_count += 1
    elif float(curr["close"]) < float(curr["SMA_20"]) < float(curr["SMA_50"]):
        signals.append(("趋势", "卖出", "空头排列"))
        sell_count += 1
    else:
        signals.append(("趋势", "中性", "震荡"))
        neutral_count += 1

    total = buy_count + sell_count + neutral_count

    if buy_count > sell_count and buy_count > neutral_count:
        recommendation = f"📈 买入 ({buy_count}/{total})"
    elif sell_count > buy_count and sell_count > neutral_count:
        recommendation = f"📉 卖出 ({sell_count}/{total})"
    else:
        recommendation = f"⏸️ 持有 ({neutral_count}/{total})"

    buy_bar = "█" * buy_count + "░" * (total - buy_count)
    sell_bar = "█" * sell_count + "░" * (total - sell_count)
    neutral_bar = "█" * neutral_count + "░" * (total - neutral_count)

    symbol = str(data.metadata.get("symbol") or "")

    report = (
        f"📊 **{symbol} 信号汇总**\n\n"
        f"买入信号: {buy_bar} {buy_count}/{total}\n"
        f"卖出信号: {sell_bar} {sell_count}/{total}\n"
        f"中性信号: {neutral_bar} {neutral_count}/{total}\n\n"
        f"**综合建议**: {recommendation}\n\n"
        f"**信号明细**:\n"
    )

    for sig in signals:
        emoji = "✅" if sig[1] == "买入" else "❌" if sig[1] == "卖出" else "⚪"
        report += f"{emoji} {sig[0]} → {sig[1]} ({sig[2]})\n"

    return {
        "name": "signals",
        "payload": {
            "buy": buy_count,
            "sell": sell_count,
            "neutral": neutral_count,
            "total": total,
            "recommendation": recommendation,
            "signals": [{"indicator": a, "action": b, "reason": c} for a, b, c in signals],
        },
        "markdown": report.strip(),
    }
