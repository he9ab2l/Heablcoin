"""第一板块：交易前逻辑安检"""
from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional

from market_analysis.data_provider import DataProvider
from utils.smart_logger import get_logger


logger = get_logger('learning')


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


class PreTradeAuditModule:
    """交易前逻辑安检模块"""

    def __init__(self, provider: Optional[DataProvider] = None) -> None:
        self.provider = provider or DataProvider.instance()

    def audit_reason(
        self,
        symbol: str = "BTC/USDT",
        side: str = "buy",
        reason: str = "",
        timeframe: str = "1h",
    ) -> Dict[str, Any]:
        """理由审计官：验证交易理由是否与实际数据匹配"""
        logger.info(f"[理由审计] {symbol} {side} - 理由: {reason[:50]}...")
        
        symbol = str(symbol or "BTC/USDT").upper()
        side = str(side or "buy").lower()
        reason_lower = str(reason or "").lower()

        try:
            std = self.provider.get_standard_data(
                symbol=symbol, timeframe=timeframe, limit=100, include_ticker=True
            )
            df = std.df
            ticker = std.ticker
        except Exception as e:
            logger.error(f"[理由审计] 获取数据失败: {e}")
            return {"error": f"无法获取市场数据: {e}", "passed": False}

        closes = [_safe_float(r["close"], 0.0) for _, r in df.iterrows()]
        current_price = _safe_float(ticker.get("last") if ticker else closes[-1], 0.0)

        # 计算技术指标
        rsi = self._calc_rsi(closes)
        ema20 = self._calc_ema(closes, 20)
        ema50 = self._calc_ema(closes, 50)
        ema200 = self._calc_ema(closes, 200) if len(closes) >= 200 else ema50

        confirmations: List[str] = []
        issues: List[str] = []

        # 检查RSI相关理由
        if "rsi" in reason_lower or "超卖" in reason_lower or "超买" in reason_lower:
            if "超卖" in reason_lower or "oversold" in reason_lower:
                if rsi < 30:
                    confirmations.append(f"✅ RSI确实处于超卖区域 (RSI={rsi:.1f})")
                else:
                    issues.append(f"❌ RSI并未超卖 (RSI={rsi:.1f}，需要<30)")
            elif "超买" in reason_lower or "overbought" in reason_lower:
                if rsi > 70:
                    confirmations.append(f"✅ RSI确实处于超买区域 (RSI={rsi:.1f})")
                else:
                    issues.append(f"❌ RSI并未超买 (RSI={rsi:.1f}，需要>70)")

        # 检查趋势相关理由
        if "趋势" in reason_lower or "trend" in reason_lower or "均线" in reason_lower:
            if side == "buy":
                if current_price > ema20 > ema50:
                    confirmations.append("✅ 价格确实处于上升趋势 (Price>EMA20>EMA50)")
                else:
                    issues.append(f"⚠️ 价格并未明确处于上升趋势 (价格:{current_price:.2f}, EMA20:{ema20:.2f}, EMA50:{ema50:.2f})")
            else:
                if current_price < ema20 < ema50:
                    confirmations.append("✅ 价格确实处于下降趋势 (Price<EMA20<EMA50)")
                else:
                    issues.append(f"⚠️ 价格并未明确处于下降趋势")

        # 检查支撑/阻力相关理由
        if "支撑" in reason_lower or "support" in reason_lower:
            support_level = min(closes[-20:]) if len(closes) >= 20 else min(closes)
            if current_price <= support_level * 1.02:
                confirmations.append(f"✅ 价格接近近期支撑位 ({support_level:.2f})")
            else:
                issues.append(f"⚠️ 价格距离近期支撑位较远 (支撑:{support_level:.2f}, 当前:{current_price:.2f})")

        if "阻力" in reason_lower or "resistance" in reason_lower:
            resistance_level = max(closes[-20:]) if len(closes) >= 20 else max(closes)
            if current_price >= resistance_level * 0.98:
                confirmations.append(f"✅ 价格接近近期阻力位 ({resistance_level:.2f})")
            else:
                issues.append(f"⚠️ 价格距离近期阻力位较远")

        # 如果没有匹配任何关键词
        if not confirmations and not issues:
            issues.append("⚠️ 未能从理由中识别出可验证的技术指标依据")

        passed = len(issues) == 0 and len(confirmations) > 0
        
        result = {
            "passed": passed,
            "confirmations": confirmations,
            "issues": issues,
            "data": {
                "symbol": symbol,
                "current_price": current_price,
                "rsi": round(rsi, 1),
                "ema20": round(ema20, 2),
                "ema50": round(ema50, 2),
                "ema200": round(ema200, 2),
            },
        }
        
        logger.info(f"[理由审计] 结果: {'通过' if passed else '未通过'}")
        return result

    def calculate_risk_reward(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float = 0,
    ) -> Dict[str, Any]:
        """盈亏比计算器"""
        entry = _safe_float(entry_price, 0)
        sl = _safe_float(stop_loss, 0)
        tp = _safe_float(take_profit, 0)
        size = _safe_float(position_size, 0)

        if entry <= 0 or sl <= 0 or tp <= 0:
            return {"error": "价格参数无效"}

        # 判断方向
        if sl < entry < tp:
            side = "long"
            risk = entry - sl
            reward = tp - entry
        elif tp < entry < sl:
            side = "short"
            risk = sl - entry
            reward = entry - tp
        else:
            return {"error": "止损止盈设置逻辑错误"}

        risk_pct = risk / entry * 100
        reward_pct = reward / entry * 100
        rr_ratio = reward / risk if risk > 0 else 0

        # 生成建议
        if rr_ratio >= 2:
            advice = "✅ 盈亏比优秀（>= 1:2），符合良好的交易习惯"
        elif rr_ratio >= 1.5:
            advice = "✅ 盈亏比合格（>= 1:1.5），可以考虑入场"
        elif rr_ratio >= 1:
            advice = "⚠️ 盈亏比一般（1:1），建议调整止盈止损获得更好的盈亏比"
        else:
            advice = "❌ 盈亏比不佳（< 1:1），不建议入场"

        result = {
            "side": side,
            "entry": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "risk_pct": round(risk_pct, 2),
            "reward_pct": round(reward_pct, 2),
            "rr_ratio": round(rr_ratio, 2),
            "advice": advice,
        }

        if size > 0:
            result["risk_amount"] = round(size * risk_pct / 100, 2)
            result["reward_amount"] = round(size * reward_pct / 100, 2)

        logger.info(f"[盈亏比] {side} 入场:{entry} 止损:{sl} 止盈:{tp} RR=1:{rr_ratio:.2f}")
        return result

    def check_trend_alignment(
        self,
        symbol: str = "BTC/USDT",
        side: str = "buy",
        timeframe: str = "1h",
    ) -> Dict[str, Any]:
        """逆势警报器：检查交易方向是否与趋势一致"""
        logger.info(f"[趋势检查] {symbol} {side}")
        
        symbol = str(symbol or "BTC/USDT").upper()
        side = str(side or "buy").lower()

        try:
            std = self.provider.get_standard_data(
                symbol=symbol, timeframe=timeframe, limit=250, include_ticker=True
            )
            df = std.df
            ticker = std.ticker
        except Exception as e:
            logger.error(f"[趋势检查] 获取数据失败: {e}")
            return {"error": f"无法获取市场数据: {e}"}

        closes = [_safe_float(r["close"], 0.0) for _, r in df.iterrows()]
        current_price = _safe_float(ticker.get("last") if ticker else closes[-1], 0.0)

        ema20 = self._calc_ema(closes, 20)
        ema50 = self._calc_ema(closes, 50)
        ema200 = self._calc_ema(closes, 200) if len(closes) >= 200 else ema50

        # 判断趋势
        short_trend = "up" if ema20 > ema50 else "down"
        long_trend = "up" if current_price > ema200 else "down"

        # 检查是否逆势
        if side == "buy":
            if short_trend == "down" and long_trend == "down":
                warning = "❌ 警告：你正在逆势做多！短期和长期趋势都向下，风险较高。"
            elif short_trend == "down":
                warning = "⚠️ 注意：短期趋势向下，做多需谨慎。"
            else:
                warning = "✅ 方向与趋势一致，符合顺势交易原则。"
        else:
            if short_trend == "up" and long_trend == "up":
                warning = "❌ 警告：你正在逆势做空！短期和长期趋势都向上，风险较高。"
            elif short_trend == "up":
                warning = "⚠️ 注意：短期趋势向上，做空需谨慎。"
            else:
                warning = "✅ 方向与趋势一致，符合顺势交易原则。"

        return {
            "symbol": symbol,
            "side": side,
            "current_price": current_price,
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "ema200": round(ema200, 2),
            "short_trend": short_trend,
            "long_trend": long_trend,
            "warning": warning,
        }

    def check_fomo(
        self,
        symbol: str = "BTC/USDT",
        side: str = "buy",
        timeframe: str = "1h",
    ) -> Dict[str, Any]:
        """FOMO检测：检测追涨杀跌行为"""
        logger.info(f"[FOMO检测] {symbol} {side}")
        
        symbol = str(symbol or "BTC/USDT").upper()
        side = str(side or "buy").lower()

        try:
            std = self.provider.get_standard_data(
                symbol=symbol, timeframe=timeframe, limit=100, include_ticker=True
            )
            df = std.df
            ticker = std.ticker
        except Exception as e:
            logger.error(f"[FOMO检测] 获取数据失败: {e}")
            return {"error": f"无法获取市场数据: {e}"}

        closes = [_safe_float(r["close"], 0.0) for _, r in df.iterrows()]
        current_price = _safe_float(ticker.get("last") if ticker else closes[-1], 0.0)

        # 计算短期涨跌幅
        if len(closes) >= 6:
            short_change = (current_price - closes[-6]) / closes[-6] * 100
        else:
            short_change = 0

        # 计算偏离均线程度
        ema20 = self._calc_ema(closes, 20)
        deviation = (current_price - ema20) / ema20 * 100 if ema20 > 0 else 0

        # FOMO检测逻辑
        fomo_detected = False
        if side == "buy":
            if short_change > 5 and deviation > 3:
                fomo_detected = True
                warning = f"🚨 FOMO警告：价格短期暴涨{short_change:.1f}%，已偏离均线{deviation:.1f}%，此时追涨风险极高！"
            elif short_change > 3:
                warning = f"⚠️ 注意：价格短期上涨{short_change:.1f}%，建议等待回调再入场。"
            else:
                warning = "✅ 价格走势平稳，未检测到FOMO行为。"
        else:
            if short_change < -5 and deviation < -3:
                fomo_detected = True
                warning = f"🚨 FOMO警告：价格短期暴跌{abs(short_change):.1f}%，已偏离均线{abs(deviation):.1f}%，此时追空风险极高！"
            elif short_change < -3:
                warning = f"⚠️ 注意：价格短期下跌{abs(short_change):.1f}%，建议等待反弹再做空。"
            else:
                warning = "✅ 价格走势平稳，未检测到FOMO行为。"

        return {
            "symbol": symbol,
            "side": side,
            "current_price": current_price,
            "short_change_pct": round(short_change, 2),
            "deviation_from_ema20_pct": round(deviation, 2),
            "fomo_detected": fomo_detected,
            "warning": warning,
        }

    def _calc_rsi(self, closes: List[float], period: int = 14) -> float:
        if len(closes) < period + 1:
            return 50.0
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _calc_ema(self, closes: List[float], period: int) -> float:
        if len(closes) < period:
            return closes[-1] if closes else 0.0
        k = 2 / (period + 1)
        ema = sum(closes[:period]) / period
        for price in closes[period:]:
            ema = price * k + ema * (1 - k)
        return ema


__all__ = ["PreTradeAuditModule"]
