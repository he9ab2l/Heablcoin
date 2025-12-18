############################################################
# 📘 文件说明：交易中分析
# 本文件实现的功能：持仓期间的实时分析与提醒
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
# - 类: InTradeCoachModule
# - 函数: pattern_hunt, profit_protector, loss_analysis
#
# 🔗 主要依赖：__future__, market_analysis, typing, utils
#
# 🕒 创建时间：2025-12-18
############################################################

"""第二板块：盘中实时陪练"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from skills.market_analysis.data_provider import DataProvider
from utils.smart_logger import get_logger


logger = get_logger('learning')


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


class InTradeCoachModule:
    """盘中实时陪练模块"""

    DEFAULT_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "DOGE/USDT"]

    def __init__(self, provider: Optional[DataProvider] = None) -> None:
        self.provider = provider or DataProvider.instance()

    def pattern_hunt(
        self,
        pattern: str,
        symbols: str = "",
        timeframe: str = "1h",
    ) -> Dict[str, Any]:
        """形态寻宝：扫描市场找出符合特定技术形态的币种"""
        logger.info(f"[形态寻宝] 搜索形态: {pattern}")
        
        pattern_lower = str(pattern or "").lower()
        sym_list = [s.strip().upper() for s in (symbols or "").split(",") if s.strip()]
        if not sym_list:
            sym_list = self.DEFAULT_SYMBOLS

        results: List[Dict[str, Any]] = []
        prompt = f"正在扫描市场寻找【{pattern}】形态..."

        for sym in sym_list:
            try:
                std = self.provider.get_standard_data(
                    symbol=sym, timeframe=timeframe, limit=100, include_ticker=True
                )
                df = std.df
                ticker = std.ticker
                
                closes = [_safe_float(r["close"], 0.0) for _, r in df.iterrows()]
                current_price = _safe_float(ticker.get("last") if ticker else closes[-1], 0.0)
                rsi = self._calc_rsi(closes)

                match_info = self._check_pattern(pattern_lower, df, closes, rsi)
                if match_info["matched"]:
                    results.append({
                        "symbol": sym,
                        "description": match_info["description"],
                        "current_price": round(current_price, 4),
                        "rsi": round(rsi, 1),
                        "suggested_stop": round(current_price * (0.97 if "多" in pattern or "买" in pattern else 1.03), 4),
                    })
            except Exception as e:
                logger.debug(f"[形态寻宝] {sym} 获取数据失败: {e}")
                continue

        logger.info(f"[形态寻宝] 找到 {len(results)} 个匹配结果")
        return {
            "pattern": pattern,
            "prompt": prompt,
            "scanned": len(sym_list),
            "results": results,
        }

    def _check_pattern(
        self, pattern: str, df, closes: List[float], rsi: float
    ) -> Dict[str, Any]:
        """检查是否匹配特定形态"""
        # 底背离
        if "底背离" in pattern or "bullish divergence" in pattern:
            if len(closes) >= 20:
                price_low = min(closes[-10:])
                prev_price_low = min(closes[-20:-10])
                if price_low < prev_price_low and rsi > 30:
                    return {"matched": True, "description": "价格创新低但RSI未创新低，可能形成底背离"}
        
        # 顶背离
        if "顶背离" in pattern or "bearish divergence" in pattern:
            if len(closes) >= 20:
                price_high = max(closes[-10:])
                prev_price_high = max(closes[-20:-10])
                if price_high > prev_price_high and rsi < 70:
                    return {"matched": True, "description": "价格创新高但RSI未创新高，可能形成顶背离"}

        # 超卖
        if "超卖" in pattern or "oversold" in pattern:
            if rsi < 30:
                return {"matched": True, "description": f"RSI={rsi:.1f}，处于超卖区域"}

        # 超买
        if "超买" in pattern or "overbought" in pattern:
            if rsi > 70:
                return {"matched": True, "description": f"RSI={rsi:.1f}，处于超买区域"}

        # 突破
        if "突破" in pattern or "breakout" in pattern:
            if len(closes) >= 20:
                recent_high = max(closes[-20:-1])
                if closes[-1] > recent_high:
                    return {"matched": True, "description": f"突破近20根K线高点 {recent_high:.4f}"}

        # 跌破
        if "跌破" in pattern or "breakdown" in pattern:
            if len(closes) >= 20:
                recent_low = min(closes[-20:-1])
                if closes[-1] < recent_low:
                    return {"matched": True, "description": f"跌破近20根K线低点 {recent_low:.4f}"}

        return {"matched": False, "description": ""}

    def profit_protector(
        self,
        symbol: str = "BTC/USDT",
        entry_price: float = 0,
        side: str = "long",
    ) -> Dict[str, Any]:
        """止盈保姆：持仓盈利时提供建议"""
        logger.info(f"[止盈保姆] {symbol} {side} 入场:{entry_price}")
        
        symbol = str(symbol or "BTC/USDT").upper()
        entry = _safe_float(entry_price, 0)
        side = str(side or "long").lower()

        try:
            std = self.provider.get_standard_data(
                symbol=symbol, timeframe="1h", limit=100, include_ticker=True
            )
            ticker = std.ticker
            df = std.df
        except Exception as e:
            logger.error(f"[止盈保姆] 获取数据失败: {e}")
            return {"error": f"无法获取市场数据: {e}"}

        closes = [_safe_float(r["close"], 0.0) for _, r in df.iterrows()]
        current_price = _safe_float(ticker.get("last") if ticker else closes[-1], 0.0)

        if entry <= 0:
            entry = closes[-10] if len(closes) >= 10 else current_price

        # 计算盈亏
        if side == "long":
            pnl_pct = (current_price - entry) / entry * 100
        else:
            pnl_pct = (entry - current_price) / entry * 100

        # 计算ATR作为移动止损参考
        atr = self._calc_atr(df)
        
        # 生成建议
        if pnl_pct >= 10:
            advice = (
                f"🎉 浮盈{pnl_pct:.1f}%，建议：\n"
                f"1. 移动止损到入场价+{atr*1.5:.4f}（保本止损）\n"
                f"2. 考虑分批止盈，先平掉50%仓位锁定利润\n"
                f"3. 剩余仓位可以继续持有追踪"
            )
        elif pnl_pct >= 5:
            advice = (
                f"📈 浮盈{pnl_pct:.1f}%，建议：\n"
                f"1. 移动止损到盈亏平衡点附近\n"
                f"2. 观察是否有趋势延续信号\n"
                f"3. 设置合理的止盈目标"
            )
        elif pnl_pct >= 2:
            advice = (
                f"📊 小幅浮盈{pnl_pct:.1f}%，建议：\n"
                f"1. 保持原有止损不变\n"
                f"2. 耐心等待趋势发展\n"
                f"3. 不要过早止盈"
            )
        elif pnl_pct >= 0:
            advice = f"持仓微利{pnl_pct:.1f}%，继续持有观察。"
        else:
            advice = f"⚠️ 持仓浮亏{abs(pnl_pct):.1f}%，请确认止损位置是否合理。"

        return {
            "symbol": symbol,
            "entry_price": entry,
            "current_price": current_price,
            "side": side,
            "pnl_pct": round(pnl_pct, 2),
            "atr": round(atr, 4),
            "advice": advice,
        }

    def loss_analysis(
        self,
        symbol: str = "BTC/USDT",
        entry_price: float = 0,
        exit_price: float = 0,
        side: str = "long",
        entry_reason: str = "",
    ) -> Dict[str, Any]:
        """亏损心理按摩：止损后的复盘分析"""
        logger.info(f"[亏损分析] {symbol} {side} 入场:{entry_price} 出场:{exit_price}")
        
        entry = _safe_float(entry_price, 0)
        exit_p = _safe_float(exit_price, 0)
        side = str(side or "long").lower()

        if entry <= 0 or exit_p <= 0:
            return {"error": "请提供有效的入场和出场价格"}

        # 计算亏损
        if side == "long":
            pnl_pct = (exit_p - entry) / entry * 100
        else:
            pnl_pct = (entry - exit_p) / entry * 100

        # 判断亏损类型
        if abs(pnl_pct) <= 3:
            loss_type = "好的亏损 ✅"
            comfort_message = (
                "这是一次纪律性止损，亏损控制在合理范围内。"
                "每个成功的交易员都会经历亏损，关键是控制损失大小。"
                "你做得很好，继续保持这种纪律性！"
            )
            improvement = "继续保持严格的止损纪律，这是长期盈利的基础。"
        elif abs(pnl_pct) <= 5:
            loss_type = "一般的亏损 ⚠️"
            comfort_message = (
                "亏损略大于理想范围，但仍在可接受范围内。"
                "不要太自责，市场有时会快速波动导致滑点。"
            )
            improvement = "考虑在入场时使用更紧凑的止损，或在波动大时减少仓位。"
        else:
            loss_type = "需要反思的亏损 ❌"
            comfort_message = (
                "这次亏损较大，需要认真复盘。"
                "但请记住：认识到问题是进步的第一步。"
                "每次失败都是学习的机会。"
            )
            improvement = (
                "1. 检查是否设置了止损\n"
                "2. 是否存在扛单行为\n"
                "3. 仓位是否过大\n"
                "4. 入场理由是否充分"
            )

        return {
            "symbol": symbol,
            "side": side,
            "entry_price": entry,
            "exit_price": exit_p,
            "pnl_pct": round(pnl_pct, 2),
            "loss_type": loss_type,
            "comfort_message": comfort_message,
            "improvement": improvement,
            "entry_reason": entry_reason,
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

    def _calc_atr(self, df, period: int = 14) -> float:
        if len(df) < period:
            return 0.0
        tr_list = []
        for i in range(1, len(df)):
            high = _safe_float(df.iloc[i]["high"], 0.0)
            low = _safe_float(df.iloc[i]["low"], 0.0)
            prev_close = _safe_float(df.iloc[i-1]["close"], 0.0)
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_list.append(tr)
        if len(tr_list) < period:
            return sum(tr_list) / len(tr_list) if tr_list else 0.0
        return sum(tr_list[-period:]) / period


__all__ = ["InTradeCoachModule"]
