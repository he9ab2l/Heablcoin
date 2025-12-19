"""第三板块：历史时光机"""
from __future__ import annotations

import random
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from skills.market_analysis.data_provider import DataProvider
from utils.smart_logger import get_logger


logger = get_logger('learning')


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


class HistorySimModule:
    """历史时光机模块"""

    def __init__(self, provider: Optional[DataProvider] = None) -> None:
        self.provider = provider or DataProvider.instance()

    def what_if(
        self,
        symbol: str = "BTC/USDT",
        hours_ago: int = 1,
        stop_loss_pct: float = 2.0,
        side: str = "buy",
    ) -> Dict[str, Any]:
        """What-If模拟器：假如N小时前买入/卖出会怎样"""
        logger.info(f"[What-If] {symbol} {side} {hours_ago}小时前")
        
        symbol = str(symbol or "BTC/USDT").upper()
        hours = max(1, min(int(hours_ago), 168))  # 最多7天
        sl_pct = _safe_float(stop_loss_pct, 2.0)
        side = str(side or "buy").lower()

        try:
            std = self.provider.get_standard_data(
                symbol=symbol, timeframe="1h", limit=hours + 10, include_ticker=True
            )
            df = std.df
            ticker = std.ticker
        except Exception as e:
            logger.error(f"[What-If] 获取数据失败: {e}")
            return {"error": f"无法获取市场数据: {e}"}

        if len(df) < hours:
            return {"error": f"历史数据不足，只有{len(df)}根K线"}

        # 获取入场价格（N小时前的收盘价）
        entry_idx = -(hours + 1)
        entry_price = _safe_float(df.iloc[entry_idx]["close"], 0.0)
        current_price = _safe_float(ticker.get("last") if ticker else df.iloc[-1]["close"], 0.0)

        # 计算止损价
        if side == "buy":
            stop_price = entry_price * (1 - sl_pct / 100)
        else:
            stop_price = entry_price * (1 + sl_pct / 100)

        # 模拟持仓过程
        stopped_out = False
        stop_at_hour = 0
        max_drawdown = 0
        max_profit = 0

        for i in range(entry_idx + 1, 0):
            candle_low = _safe_float(df.iloc[i]["low"], 0.0)
            candle_high = _safe_float(df.iloc[i]["high"], 0.0)
            candle_close = _safe_float(df.iloc[i]["close"], 0.0)

            if side == "buy":
                # 检查是否触发止损
                if candle_low <= stop_price:
                    stopped_out = True
                    stop_at_hour = i - entry_idx
                    break
                # 计算回撤和利润
                pnl = (candle_close - entry_price) / entry_price * 100
                drawdown = (entry_price - candle_low) / entry_price * 100
            else:
                if candle_high >= stop_price:
                    stopped_out = True
                    stop_at_hour = i - entry_idx
                    break
                pnl = (entry_price - candle_close) / entry_price * 100
                drawdown = (candle_high - entry_price) / entry_price * 100

            max_profit = max(max_profit, pnl)
            max_drawdown = max(max_drawdown, drawdown)

        # 最终盈亏
        if stopped_out:
            final_pnl = -sl_pct
        else:
            if side == "buy":
                final_pnl = (current_price - entry_price) / entry_price * 100
            else:
                final_pnl = (entry_price - current_price) / entry_price * 100

        # 生成分析
        if stopped_out:
            message = f"⚠️ 如果{hours}小时前{side}入场，会在第{stop_at_hour}小时被止损出局，亏损{sl_pct}%。这说明止损设置合理，保护了资金。"
        elif final_pnl > 0:
            message = f"✅ 如果{hours}小时前{side}入场，现在盈利{final_pnl:.1f}%。但请注意，期间最大回撤{max_drawdown:.1f}%，你能承受这个波动吗？"
        else:
            message = f"❌ 如果{hours}小时前{side}入场，现在亏损{abs(final_pnl):.1f}%。这验证了你当时不入场的决定是正确的。"

        return {
            "symbol": symbol,
            "side": side,
            "hours_ago": hours,
            "entry_price": round(entry_price, 4),
            "current_price": round(current_price, 4),
            "stop_loss_pct": sl_pct,
            "stop_price": round(stop_price, 4),
            "stopped_out": stopped_out,
            "stop_at_hour": stop_at_hour,
            "final_pnl_pct": round(final_pnl, 2),
            "max_profit_pct": round(max_profit, 2),
            "max_drawdown_pct": round(max_drawdown, 2),
            "message": message,
        }

    def blind_history_test(
        self,
        symbol: str = "BTC/USDT",
        timeframe: str = "1h",
        candles: int = 30,
    ) -> Dict[str, Any]:
        """历史重演测验：隐藏时间的历史K线判断走势"""
        logger.info(f"[历史盲测] {symbol} {timeframe} {candles}根K线")
        
        symbol = str(symbol or "BTC/USDT").upper()
        n_candles = max(20, min(int(candles), 100))

        try:
            # 获取足够多的历史数据
            std = self.provider.get_standard_data(
                symbol=symbol, timeframe=timeframe, limit=500, include_ticker=False
            )
            df = std.df
        except Exception as e:
            logger.error(f"[历史盲测] 获取数据失败: {e}")
            return {"error": f"无法获取市场数据: {e}"}

        if len(df) < n_candles + 50:
            return {"error": "历史数据不足"}

        # 随机选择一个起始点（不是最新的数据）
        max_start = len(df) - n_candles - 20
        start_idx = random.randint(50, max_start)
        end_idx = start_idx + n_candles

        # 提取K线数据（隐藏时间）
        test_candles = []
        for i, (_, row) in enumerate(df.iloc[start_idx:end_idx].iterrows()):
            test_candles.append({
                "index": i + 1,
                "open": round(_safe_float(row["open"], 0.0), 4),
                "high": round(_safe_float(row["high"], 0.0), 4),
                "low": round(_safe_float(row["low"], 0.0), 4),
                "close": round(_safe_float(row["close"], 0.0), 4),
                "volume": round(_safe_float(row.get("volume", 0), 0.0), 2),
            })

        # 获取后续20根K线的走势作为答案
        future_closes = [_safe_float(df.iloc[i]["close"], 0.0) for i in range(end_idx, min(end_idx + 20, len(df)))]
        last_close = test_candles[-1]["close"]
        
        if future_closes:
            future_price = future_closes[-1]
            change_pct = (future_price - last_close) / last_close * 100
            if change_pct > 2:
                direction = "up"
            elif change_pct < -2:
                direction = "down"
            else:
                direction = "sideways"
        else:
            direction = "unknown"
            change_pct = 0

        test_id = str(uuid.uuid4())[:8]

        prompt = (
            f"📊 历史盲测题目 #{test_id}\n\n"
            f"这是{symbol}在某个历史时段的{n_candles}根{timeframe}K线数据。\n"
            f"时间已被隐藏，请根据技术分析判断：\n"
            f"**接下来20根K线，你会选择 买入/卖出/观望？**"
        )

        return {
            "test_id": test_id,
            "symbol": symbol,
            "timeframe": timeframe,
            "prompt": prompt,
            "candles": test_candles,
            "answer": {
                "direction": direction,
                "change_pct": round(change_pct, 2),
                "future_closes": [round(c, 4) for c in future_closes[:5]],
            },
        }

    def reveal_blind_test(self, user_choice: str, answer: Dict[str, Any]) -> str:
        """揭晓历史盲测答案"""
        direction = answer.get("direction", "unknown")
        change_pct = answer.get("change_pct", 0)

        choice_lower = str(user_choice or "").lower()
        if "买" in choice_lower or "buy" in choice_lower or "多" in choice_lower:
            user_direction = "buy"
        elif "卖" in choice_lower or "sell" in choice_lower or "空" in choice_lower:
            user_direction = "sell"
        else:
            user_direction = "hold"

        # 评估正确性
        if direction == "up":
            if user_direction == "buy":
                result = f"✅ 正确！后续上涨{change_pct:.1f}%，你的判断很准确！"
                score = 100
            elif user_direction == "hold":
                result = f"⚠️ 可以接受。后续上涨{change_pct:.1f}%，错过了机会但没有损失。"
                score = 50
            else:
                result = f"❌ 错误。后续上涨{change_pct:.1f}%，做空会亏损。"
                score = 0
        elif direction == "down":
            if user_direction == "sell":
                result = f"✅ 正确！后续下跌{abs(change_pct):.1f}%，你的判断很准确！"
                score = 100
            elif user_direction == "hold":
                result = f"⚠️ 可以接受。后续下跌{abs(change_pct):.1f}%，观望规避了风险。"
                score = 50
            else:
                result = f"❌ 错误。后续下跌{abs(change_pct):.1f}%，做多会亏损。"
                score = 0
        else:
            if user_direction == "hold":
                result = f"✅ 正确！后续横盘震荡，观望是最佳选择。"
                score = 100
            else:
                result = f"⚠️ 一般。后续横盘震荡{change_pct:.1f}%，没有明显趋势。"
                score = 50

        logger.info(f"[历史盲测] 用户选择:{user_choice} 实际:{direction} 得分:{score}")
        return f"{result}\n\n**得分: {score}/100**"

    def strategy_backtest(
        self,
        symbol: str = "BTC/USDT",
        strategy: str = "",
        days: int = 180,
        initial_capital: float = 10000,
    ) -> Dict[str, Any]:
        """策略验证沙盒：简单策略回测"""
        logger.info(f"[策略回测] {symbol} 策略:{strategy[:30]}... {days}天")
        
        symbol = str(symbol or "BTC/USDT").upper()
        strategy_desc = str(strategy or "").lower()
        test_days = max(30, min(int(days), 365))
        capital = _safe_float(initial_capital, 10000)

        # 解析策略
        buy_condition = None
        sell_condition = None

        if "rsi" in strategy_desc:
            if "30" in strategy_desc or "超卖" in strategy_desc:
                buy_condition = lambda rsi, **_: rsi < 30
                sell_condition = lambda rsi, **_: rsi > 70
            elif "70" in strategy_desc or "超买" in strategy_desc:
                buy_condition = lambda rsi, **_: rsi > 70
                sell_condition = lambda rsi, **_: rsi < 30

        if "均线" in strategy_desc or "ema" in strategy_desc or "ma" in strategy_desc:
            if "金叉" in strategy_desc or "上穿" in strategy_desc:
                buy_condition = lambda ema20, ema50, **_: ema20 > ema50
                sell_condition = lambda ema20, ema50, **_: ema20 < ema50
            elif "死叉" in strategy_desc or "下穿" in strategy_desc:
                buy_condition = lambda ema20, ema50, **_: ema20 < ema50
                sell_condition = lambda ema20, ema50, **_: ema20 > ema50

        if buy_condition is None:
            # 默认RSI策略
            buy_condition = lambda rsi, **_: rsi < 30
            sell_condition = lambda rsi, **_: rsi > 70

        try:
            # 获取日线数据
            std = self.provider.get_standard_data(
                symbol=symbol, timeframe="1d", limit=test_days + 100, include_ticker=False
            )
            df = std.df
        except Exception as e:
            logger.error(f"[策略回测] 获取数据失败: {e}")
            return {"error": f"无法获取市场数据: {e}"}

        if len(df) < test_days:
            return {"error": f"历史数据不足，只有{len(df)}天"}

        # 回测
        closes = [_safe_float(r["close"], 0.0) for _, r in df.iterrows()]
        test_closes = closes[-test_days:]

        equity = capital
        position = 0
        trades = []
        entry_price = 0

        for i in range(50, len(test_closes)):
            window = test_closes[max(0, i-50):i+1]
            rsi = self._calc_rsi(window)
            ema20 = self._calc_ema(window, 20)
            ema50 = self._calc_ema(window, 50)
            price = test_closes[i]

            indicators = {"rsi": rsi, "ema20": ema20, "ema50": ema50, "price": price}

            if position == 0 and buy_condition(**indicators):
                position = equity / price
                entry_price = price
                equity = 0
            elif position > 0 and sell_condition(**indicators):
                equity = position * price
                pnl_pct = (price - entry_price) / entry_price * 100
                trades.append({"entry": entry_price, "exit": price, "pnl_pct": pnl_pct})
                position = 0

        # 如果还有持仓，按最后价格平仓
        if position > 0:
            final_price = test_closes[-1]
            equity = position * final_price
            pnl_pct = (final_price - entry_price) / entry_price * 100
            trades.append({"entry": entry_price, "exit": final_price, "pnl_pct": pnl_pct})

        # 统计
        wins = sum(1 for t in trades if t["pnl_pct"] > 0)
        losses = len(trades) - wins
        total_return = (equity - capital) / capital * 100

        # 买入持有收益
        hold_return = (test_closes[-1] - test_closes[0]) / test_closes[0] * 100

        # 判定
        if total_return > hold_return:
            verdict = f"✅ 策略跑赢买入持有 ({total_return:.1f}% vs {hold_return:.1f}%)"
        elif total_return > 0:
            verdict = f"⚠️ 策略盈利但跑输买入持有 ({total_return:.1f}% vs {hold_return:.1f}%)"
        else:
            verdict = f"❌ 策略亏损 ({total_return:.1f}%)，需要优化"

        return {
            "symbol": symbol,
            "strategy": strategy,
            "test_days": test_days,
            "initial_capital": capital,
            "final_equity": round(equity, 2),
            "total_return_pct": round(total_return, 2),
            "hold_return_pct": round(hold_return, 2),
            "total_trades": len(trades),
            "wins": wins,
            "losses": losses,
            "win_rate_pct": round(wins / len(trades) * 100, 1) if trades else 0,
            "verdict": verdict,
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


__all__ = ["HistorySimModule"]
