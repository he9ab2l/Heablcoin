from __future__ import annotations

from typing import Any, Dict, List, Optional

from market_analysis.data_provider import StandardMarketData


def detect_patterns(data: StandardMarketData, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    K线形态识别模块。
    识别常见的蜡烛图形态和价格模式。
    """
    symbol = str(data.metadata.get("symbol") or "BTC/USDT")
    df = data.df
    
    if df is None or len(df) < 5:
        return {
            "name": "patterns",
            "payload": {"symbol": symbol, "patterns": [], "pattern_count": 0},
            "markdown": f"🕯️ **{symbol} 形态识别**\n\n数据不足，无法识别形态",
        }
    
    patterns: List[Dict[str, Any]] = []
    
    # 获取最近几根K线数据
    opens = df["open"].tolist()
    highs = df["high"].tolist()
    lows = df["low"].tolist()
    closes = df["close"].tolist()
    
    # recent_data: list of tuples (open, high, low, close)
    recent = [(opens[i], highs[i], lows[i], closes[i]) for i in range(-min(5, len(opens)), 0)]
    if not recent:
        recent = [(opens[-1], highs[-1], lows[-1], closes[-1])]
    
    def candle_body(c: tuple) -> float:
        # c = (open, high, low, close)
        return abs(c[3] - c[0])
    
    def candle_range(c: tuple) -> float:
        return c[1] - c[2]  # high - low
    
    def is_bullish(c: tuple) -> bool:
        return c[3] > c[0]  # close > open
    
    def is_bearish(c: tuple) -> bool:
        return c[3] < c[0]  # close < open
    
    # 锤子线 (Hammer)
    last = recent[-1]
    body = candle_body(last)
    full_range = candle_range(last)
    lower_shadow = min(last[0], last[3]) - last[2]  # min(open,close) - low
    upper_shadow = last[1] - max(last[0], last[3])  # high - max(open,close)
    
    if full_range > 0 and body > 0:
        if lower_shadow > body * 2 and upper_shadow < body * 0.5:
            patterns.append({
                "name": "锤子线",
                "type": "reversal",
                "direction": "bullish",
                "confidence": 70,
                "description": "下影线长度超过实体2倍，可能预示底部反转",
            })
        
        # 倒锤子线 (Inverted Hammer)
        if upper_shadow > body * 2 and lower_shadow < body * 0.5:
            patterns.append({
                "name": "倒锤子线",
                "type": "reversal",
                "direction": "bullish",
                "confidence": 60,
                "description": "上影线长度超过实体2倍，需要后续确认",
            })
    
    # 吞没形态 (Engulfing) - tuples are (open, high, low, close) indexed 0,1,2,3
    if len(recent) >= 2:
        prev, curr = recent[-2], recent[-1]
        prev_body = candle_body(prev)
        curr_body = candle_body(curr)
        
        # 看涨吞没
        if is_bearish(prev) and is_bullish(curr):
            if curr[3] > prev[0] and curr[0] < prev[3] and curr_body > prev_body:
                patterns.append({
                    "name": "看涨吞没",
                    "type": "reversal",
                    "direction": "bullish",
                    "confidence": 75,
                    "description": "阳线完全吞没前一根阴线，强烈看涨信号",
                })
        
        # 看跌吞没
        if is_bullish(prev) and is_bearish(curr):
            if curr[0] > prev[3] and curr[3] < prev[0] and curr_body > prev_body:
                patterns.append({
                    "name": "看跌吞没",
                    "type": "reversal",
                    "direction": "bearish",
                    "confidence": 75,
                    "description": "阴线完全吞没前一根阳线，强烈看跌信号",
                })
    
    # 十字星 (Doji)
    if full_range > 0 and body / full_range < 0.1:
        patterns.append({
            "name": "十字星",
            "type": "indecision",
            "direction": "neutral",
            "confidence": 50,
            "description": "开盘价与收盘价几乎相等，市场犹豫不决",
        })
    
    # 三连阳/三连阴
    if len(recent) >= 3:
        last_three = recent[-3:]
        if all(is_bullish(c) for c in last_three):
            patterns.append({
                "name": "三连阳",
                "type": "continuation",
                "direction": "bullish",
                "confidence": 65,
                "description": "连续三根阳线，上涨动能强劲",
            })
        elif all(is_bearish(c) for c in last_three):
            patterns.append({
                "name": "三连阴",
                "type": "continuation",
                "direction": "bearish",
                "confidence": 65,
                "description": "连续三根阴线，下跌动能强劲",
            })
    
    # 生成摘要
    if patterns:
        bullish = sum(1 for p in patterns if p.get("direction") == "bullish")
        bearish = sum(1 for p in patterns if p.get("direction") == "bearish")
        if bullish > bearish:
            bias = "偏多"
        elif bearish > bullish:
            bias = "偏空"
        else:
            bias = "中性"
        summary = f"识别到 {len(patterns)} 个形态，整体 {bias}"
    else:
        summary = "未识别到明显形态"
    
    # 生成 markdown
    patterns_md = ""
    if patterns:
        for i, p in enumerate(patterns):
            prefix = "└─" if i == len(patterns) - 1 else "├─"
            patterns_md += f"{prefix} {p['name']} ({p['direction']}, {p['confidence']}%): {p['description']}\n"
    else:
        patterns_md = "无明显形态"
    
    markdown = (
        f"🕯️ **{symbol} 形态识别**\n"
        f"{'═' * 35}\n\n"
        f"📊 **识别结果**: {summary}\n\n"
        f"**形态列表**\n{patterns_md}"
    )
    
    return {
        "name": "patterns",
        "payload": {
            "symbol": symbol,
            "patterns": patterns,
            "pattern_count": len(patterns),
        },
        "markdown": markdown,
    }


def get_module_info() -> Dict[str, Any]:
    return {
        "name": "patterns",
        "title": "K线形态识别",
        "description": "识别锤子线、吞没形态、十字星等常见K线形态",
        "version": "1.0.0",
    }


__all__ = ["detect_patterns", "get_module_info"]
