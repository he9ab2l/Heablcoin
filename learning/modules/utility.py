############################################################
# 📘 文件说明：学习工具函数
# 本文件实现的功能：学习模块的通用工具函数
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
# - 类: UtilityModule
# - 函数: calculate_volatility_adjusted_size, check_upcoming_events, quick_market_scan
#
# 🔗 主要依赖：__future__, datetime, market_analysis, typing, utils
#
# 🕒 创建时间：2025-12-18
############################################################

"""第五板块：辅助工具"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from market_analysis.data_provider import DataProvider
from utils.smart_logger import get_logger


logger = get_logger('learning')


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


class UtilityModule:
    """辅助工具模块"""

    DEFAULT_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]

    # 常见经济事件（可扩展）
    ECONOMIC_EVENTS = [
        {"name": "美国CPI", "impact": "high", "description": "通常带来5%以上的剧烈波动"},
        {"name": "美联储利率决议", "impact": "high", "description": "可能引发趋势反转"},
        {"name": "非农就业数据", "impact": "high", "description": "短期剧烈波动"},
        {"name": "美国PPI", "impact": "medium", "description": "可能影响通胀预期"},
        {"name": "美联储会议纪要", "impact": "medium", "description": "可能透露政策信号"},
        {"name": "GDP数据", "impact": "medium", "description": "影响市场情绪"},
        {"name": "ETF决议", "impact": "high", "description": "可能引发大幅波动"},
        {"name": "减半", "impact": "high", "description": "长期利好但短期可能震荡"},
    ]

    def __init__(self, provider: Optional[DataProvider] = None) -> None:
        self.provider = provider or DataProvider.instance()

    def calculate_volatility_adjusted_size(
        self,
        symbol: str,
        intended_size_usdt: float,
        base_symbol: str = "BTC/USDT",
        timeframe: str = "1d",
    ) -> Dict[str, Any]:
        """波动率换算：根据ATR调整仓位大小"""
        logger.info(f"[波动率换算] {symbol} vs {base_symbol}")
        
        symbol = str(symbol or "BTC/USDT").upper()
        base = str(base_symbol or "BTC/USDT").upper()
        size = _safe_float(intended_size_usdt, 1000)

        try:
            # 获取目标币种数据
            std_target = self.provider.get_standard_data(
                symbol=symbol, timeframe=timeframe, limit=30, include_ticker=True
            )
            df_target = std_target.df
            ticker_target = std_target.ticker
            target_price = _safe_float(ticker_target.get("last") if ticker_target else 0, 0.0)

            # 获取基准币种数据
            std_base = self.provider.get_standard_data(
                symbol=base, timeframe=timeframe, limit=30, include_ticker=True
            )
            df_base = std_base.df
        except Exception as e:
            logger.error(f"[波动率换算] 获取数据失败: {e}")
            return {"error": f"无法获取数据: {e}"}

        # 计算ATR
        target_atr = self._calc_atr(df_target)
        base_atr = self._calc_atr(df_base)

        if target_atr == 0 or base_atr == 0:
            return {"error": "无法计算ATR"}

        # 计算ATR百分比
        target_close = _safe_float(df_target.iloc[-1]["close"], 1.0)
        base_close = _safe_float(df_base.iloc[-1]["close"], 1.0)

        target_atr_pct = target_atr / target_close * 100
        base_atr_pct = base_atr / base_close * 100

        # 波动率倍数
        volatility_ratio = target_atr_pct / base_atr_pct if base_atr_pct > 0 else 1.0

        # 调整后的仓位
        adjusted_size = size / volatility_ratio

        # 生成建议
        if volatility_ratio > 1.5:
            advice = (
                f"⚠️ {symbol}的波动率是{base}的{volatility_ratio:.1f}倍。"
                f"如果你平时习惯买{size:.0f}U的{base}，那么买{symbol}你只能买{adjusted_size:.0f}U，"
                f"否则风险敞口太大。"
            )
        elif volatility_ratio < 0.7:
            advice = (
                f"📊 {symbol}的波动率只有{base}的{volatility_ratio:.1f}倍。"
                f"如果你想保持相同的风险敞口，可以买{adjusted_size:.0f}U的{symbol}。"
            )
        else:
            advice = f"✅ {symbol}和{base}的波动率接近，仓位无需大幅调整。"

        return {
            "symbol": symbol,
            "base_symbol": base,
            "intended_size": size,
            "adjusted_size": round(adjusted_size, 2),
            "target_atr_pct": round(target_atr_pct, 2),
            "base_atr_pct": round(base_atr_pct, 2),
            "volatility_ratio": round(volatility_ratio, 2),
            "target_price": target_price,
            "adjusted_quantity": round(adjusted_size / target_price, 6) if target_price > 0 else 0,
            "advice": advice,
        }

    def check_upcoming_events(self, keywords: str = "") -> Dict[str, Any]:
        """检查重要事件：提醒用户注意高波动事件"""
        logger.info(f"[事件提醒] 关键词: {keywords}")
        
        keywords_lower = str(keywords or "").lower()

        matched_events = []
        for event in self.ECONOMIC_EVENTS:
            if not keywords or event["name"].lower() in keywords_lower or keywords_lower in event["name"].lower():
                matched_events.append(event)

        general_advice = (
            "📅 重要提醒：\n"
            "1. 重大经济数据公布前后，市场波动剧烈\n"
            "2. 建议在CPI、利率决议等重要事件前减仓或空仓观望\n"
            "3. 数据公布后等待市场消化再入场\n"
            "4. 请自行查阅财经日历确认具体时间"
        )

        return {
            "events": matched_events,
            "advice": general_advice,
            "recommendation": "建议在重大事件前空仓观望，等数据出炉后再进场",
        }

    def quick_market_scan(self, symbols: str = "") -> Dict[str, Any]:
        """快速市场扫描：返回多个币种的关键指标"""
        logger.info(f"[市场扫描] 币种: {symbols or '默认'}")
        
        sym_list = [s.strip().upper() for s in (symbols or "").split(",") if s.strip()]
        if not sym_list:
            sym_list = self.DEFAULT_SYMBOLS

        results: List[Dict[str, Any]] = []

        for sym in sym_list[:10]:
            try:
                std = self.provider.get_standard_data(
                    symbol=sym, timeframe="1h", limit=100, include_ticker=True
                )
                df = std.df
                ticker = std.ticker

                closes = [_safe_float(r["close"], 0.0) for _, r in df.iterrows()]
                current_price = _safe_float(ticker.get("last") if ticker else closes[-1], 0.0)

                # 计算关键指标
                rsi = self._calc_rsi(closes)
                ema20 = self._calc_ema(closes, 20)
                ema50 = self._calc_ema(closes, 50)

                # 24h变化
                change_24h = ((current_price - closes[-24]) / closes[-24] * 100) if len(closes) >= 24 else 0

                # 趋势判断
                if current_price > ema20 > ema50:
                    trend = "强势上涨"
                elif current_price > ema20:
                    trend = "温和上涨"
                elif current_price < ema20 < ema50:
                    trend = "强势下跌"
                elif current_price < ema20:
                    trend = "温和下跌"
                else:
                    trend = "盘整"

                # RSI状态
                if rsi > 70:
                    rsi_status = "超买"
                elif rsi < 30:
                    rsi_status = "超卖"
                else:
                    rsi_status = "中性"

                results.append({
                    "symbol": sym,
                    "price": round(current_price, 4),
                    "change_24h_pct": round(change_24h, 2),
                    "rsi": round(rsi, 1),
                    "rsi_status": rsi_status,
                    "trend": trend,
                })
            except Exception as e:
                logger.debug(f"[市场扫描] {sym} 获取失败: {e}")
                continue

        logger.info(f"[市场扫描] 完成，扫描 {len(results)} 个币种")
        return {
            "scanned": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

    def _calc_atr(self, df, period: int = 14) -> float:
        if len(df) < period:
            return 0.0
        tr_list = []
        for i in range(1, len(df)):
            high = _safe_float(df.iloc[i]["high"], 0.0)
            low = _safe_float(df.iloc[i]["low"], 0.0)
            prev_close = _safe_float(df.iloc[i - 1]["close"], 0.0)
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_list.append(tr)
        if len(tr_list) < period:
            return sum(tr_list) / len(tr_list) if tr_list else 0.0
        return sum(tr_list[-period:]) / period

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


__all__ = ["UtilityModule"]
