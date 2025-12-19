from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..data_provider import StandardMarketData


def analyze_sentiment(data: StandardMarketData, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    市场情绪分析模块。
    基于多维度数据评估市场情绪状态。
    """
    symbol = str(data.metadata.get("symbol") or "BTC/USDT")
    df = data.df
    
    if df is None or len(df) < 14:
        return {
            "name": "sentiment",
            "payload": {
                "symbol": symbol,
                "fear_greed_index": 50,
                "sentiment_label": "中性",
                "trend_bias": "震荡",
                "confidence": 0,
                "factors": [],
            },
            "markdown": f"📊 **{symbol} 情绪分析**\n\n数据不足，无法分析情绪",
        }
    
    closes = df["close"].tolist()
    volumes = df["volume"].tolist() if "volume" in df.columns else []
    
    if len(closes) < 14:
        return {
            "name": "sentiment",
            "payload": {
                "symbol": symbol,
                "fear_greed_index": 50,
                "sentiment_label": "中性",
                "trend_bias": "震荡",
                "confidence": 0,
                "factors": [],
            },
            "markdown": f"📊 **{symbol} 情绪分析**\n\n历史数据不足",
        }
    
    factors: List[Dict[str, Any]] = []
    score = 50.0
    
    # 价格动量因子
    price_change_24h = (closes[-1] - closes[-24]) / closes[-24] * 100 if len(closes) >= 24 else 0
    if price_change_24h > 5:
        score += 15
        factors.append({"name": "价格动量", "value": f"+{price_change_24h:.2f}%", "impact": "正面"})
    elif price_change_24h < -5:
        score -= 15
        factors.append({"name": "价格动量", "value": f"{price_change_24h:.2f}%", "impact": "负面"})
    else:
        factors.append({"name": "价格动量", "value": f"{price_change_24h:+.2f}%", "impact": "中性"})
    
    # 成交量因子
    if len(volumes) >= 20:
        avg_vol = sum(volumes[-20:]) / 20
        recent_vol = volumes[-1] if volumes else 0
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        if vol_ratio > 1.5:
            score += 10
            factors.append({"name": "成交量", "value": f"{vol_ratio:.2f}x 均值", "impact": "活跃"})
        elif vol_ratio < 0.5:
            score -= 5
            factors.append({"name": "成交量", "value": f"{vol_ratio:.2f}x 均值", "impact": "低迷"})
        else:
            factors.append({"name": "成交量", "value": f"{vol_ratio:.2f}x 均值", "impact": "正常"})
    
    # 趋势因子 (SMA20 vs SMA50)
    if len(closes) >= 50:
        sma20 = sum(closes[-20:]) / 20
        sma50 = sum(closes[-50:]) / 50
        if sma20 > sma50 * 1.02:
            score += 10
            factors.append({"name": "趋势", "value": "上升趋势", "impact": "正面"})
        elif sma20 < sma50 * 0.98:
            score -= 10
            factors.append({"name": "趋势", "value": "下降趋势", "impact": "负面"})
        else:
            factors.append({"name": "趋势", "value": "横盘整理", "impact": "中性"})
    
    # 波动率因子
    if len(closes) >= 14:
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        volatility = (sum(r**2 for r in returns[-14:]) / 14) ** 0.5 * 100
        if volatility > 5:
            factors.append({"name": "波动率", "value": f"{volatility:.2f}%", "impact": "高波动"})
        elif volatility < 1:
            factors.append({"name": "波动率", "value": f"{volatility:.2f}%", "impact": "低波动"})
        else:
            factors.append({"name": "波动率", "value": f"{volatility:.2f}%", "impact": "正常"})
    
    # 限制分数范围
    score = max(0, min(100, score))
    
    # 情绪标签
    if score >= 75:
        label = "极度贪婪"
    elif score >= 55:
        label = "贪婪"
    elif score >= 45:
        label = "中性"
    elif score >= 25:
        label = "恐惧"
    else:
        label = "极度恐惧"
    
    # 趋势偏向
    if score >= 60:
        trend_bias = "看涨"
    elif score <= 40:
        trend_bias = "看跌"
    else:
        trend_bias = "震荡"
    
    # 生成 markdown
    factors_md = "\n".join([f"├─ {f['name']}: {f['value']} ({f['impact']})" for f in factors[:-1]])
    if factors:
        factors_md += f"\n└─ {factors[-1]['name']}: {factors[-1]['value']} ({factors[-1]['impact']})"
    
    markdown = (
        f"🎭 **{symbol} 情绪分析**\n"
        f"{'═' * 35}\n\n"
        f"📊 **情绪指数**: {score:.0f} ({label})\n"
        f"📈 **市场偏向**: {trend_bias}\n"
        f"🎯 **置信度**: {min(80, len(factors) * 20)}%\n\n"
        f"**影响因子**\n{factors_md}"
    )
    
    return {
        "name": "sentiment",
        "payload": {
            "symbol": symbol,
            "fear_greed_index": round(score),
            "sentiment_label": label,
            "trend_bias": trend_bias,
            "confidence": min(80, len(factors) * 20),
            "factors": factors,
        },
        "markdown": markdown,
    }


def get_module_info() -> Dict[str, Any]:
    return {
        "name": "sentiment",
        "title": "市场情绪分析",
        "description": "基于价格动量、成交量、趋势等多因子评估市场情绪",
        "version": "1.0.0",
    }


__all__ = ["analyze_sentiment", "get_module_info"]
