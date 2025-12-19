from __future__ import annotations


import json

from typing import Any, Optional


from skills.learning.core import LearningEngine

from skills.learning.storage import list_sessions, load_session, create_session

from skills.learning.discipline import load_rules, save_rules, is_locked_now

from skills.learning.modules.pre_trade import PreTradeAuditModule

from skills.learning.modules.in_trade import InTradeCoachModule

from skills.learning.modules.history import HistorySimModule

from skills.learning.modules.growth import GrowthProfileModule

from skills.learning.modules.utility import UtilityModule

from skills.learning.notifier import send_learning_report, send_training_summary

from core.orchestration.router import build_orchestrator_from_env

from skills.report.query_backup import save_query_backup

from core.mcp_safety import mcp_tool_safe

from utils.smart_logger import get_logger


logger = get_logger()

ai_router = build_orchestrator_from_env()


def register_tools(mcp: Any) -> None:

    engine = LearningEngine()

    auditor = PreTradeAuditModule()

    coach = InTradeCoachModule()

    simulator = HistorySimModule()

    growth = GrowthProfileModule()

    utility = UtilityModule()


    @mcp.tool()

    @mcp_tool_safe

    def get_learning_catalog() -> str:

        """列出可用训练/学习工具目录"""

        data = {

            "modules": [

                {"key": "scan", "title": "市场扫描训练", "description": "从候选币种中找出量价不一致的目标"},

                {"key": "price_action", "title": "价格行为训练", "description": "基于裸K数据识别支撑/阻力位"},

                {"key": "blind_test", "title": "历史盲测", "description": "随机历史K线判断走势"},

                {"key": "backtest", "title": "策略回测", "description": "用自然语言描述策略并验证"},

            ],

            "pre_trade_audit": [

                {"key": "audit_reason", "title": "理由审计官", "description": "验证交易理由是否与数据匹配"},

                {"key": "risk_reward", "title": "盈亏比计算器", "description": "计算止盈止损的风险回报比"},

                {"key": "trend_check", "title": "逆势警报器", "description": "检查是否逆势交易"},

                {"key": "fomo_check", "title": "FOMO检测", "description": "检测追涨杀跌行为"},

            ],

            "in_trade_coaching": [

                {"key": "pattern_hunt", "title": "形态寻宝", "description": "扫描市场找特定技术形态"},

                {"key": "profit_protector", "title": "止盈保姆", "description": "持仓盈利时的建议"},

                {"key": "loss_analysis", "title": "亏损分析", "description": "止损后的复盘与心理按摩"},

            ],

            "history_simulation": [

                {"key": "what_if", "title": "What-If模拟", "description": "假如当时买了会怎样"},

                {"key": "blind_history", "title": "历史重演测验", "description": "盲测历史K线走势"},

                {"key": "strategy_sandbox", "title": "策略验证沙盒", "description": "简单策略回测验证"},

            ],

            "growth_profile": [

                {"key": "trade_journal", "title": "交易日记", "description": "自动记录交易决策"},

                {"key": "habit_tracker", "title": "坏习惯标签", "description": "追踪和警告交易陋习"},

                {"key": "trader_level", "title": "等级系统", "description": "交易员成长等级与成就"},

            ],

            "utility": [

                {"key": "volatility_sizer", "title": "波动率换算", "description": "根据ATR调整仓位"},

                {"key": "event_check", "title": "事件提醒", "description": "重要经济事件提醒"},

                {"key": "market_scan", "title": "快速扫描", "description": "多币种关键指标概览"},

            ],

        }

        return json.dumps(data, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def start_learning_session(

        kind: str = "scan",

        symbol: str = "BTC/USDT",

        timeframe: str = "1h",

        symbols: str = "",

        candidates: int = 10,

        pick: int = 3,

    ) -> str:

        """创建一个学习会话并返回题面与数据"""

        k = str(kind or "").lower().strip()

        if k in {"scan", "market", "scanner"}:

            out = engine.create_scan_session(timeframe=timeframe, symbols=symbols, candidates=candidates, pick=pick)

        elif k in {"price", "price_action", "pa"}:

            out = engine.create_price_action_session(symbol=symbol, timeframe=timeframe)

        else:

            return "❌ 不支持的训练类型"


        try:

            save_query_backup(

                tool_name="start_learning_session",

                title=f"{k}__{symbol}__{timeframe}",

                content=json.dumps(out, ensure_ascii=False, indent=2),

                params={

                    "kind": kind,

                    "symbol": symbol,

                    "timeframe": timeframe,

                    "symbols": symbols,

                    "candidates": candidates,

                    "pick": pick,

                },

                return_format="json",

                extra_meta={"kind": "learning"},

            )

        except Exception:

            pass


        return json.dumps(out, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def submit_learning_answer(session_id: str, answer: str, ai_enhance: bool = False, tone: str = "concise") -> str:

        """提交学习会话答案并返回评分与复盘，可选启用多AI优化输出"""

        result = engine.score_session(session_id=session_id, answer=answer)

        if ai_enhance:

            try:

                enhanced = ai_router.enhance_output(result, context={"module": "learning", "session_id": session_id}, tone=tone)

                result = enhanced.get("final") or result

            except Exception as _e:

                logger.warning(f"AI 优化学习结果失败: {type(_e).__name__}: {_e}")

        try:

            save_query_backup(

                tool_name="submit_learning_answer",

                title=str(session_id or ""),

                content=str(result or ""),

                params={"session_id": session_id, "answer": answer, "ai_enhance": ai_enhance},

                return_format="markdown",

                extra_meta={"kind": "learning"},

            )

        except Exception:

            pass

        return result


    @mcp.tool()

    @mcp_tool_safe

    def get_learning_history(limit: int = 20) -> str:

        """查看近期学习会话记录"""

        items = list_sessions(limit=limit)

        return json.dumps({"sessions": items}, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def get_execution_guard_settings() -> str:

        """获取下单纪律拦截配置与状态"""

        rules = load_rules()

        locked, remain = is_locked_now()

        return json.dumps({"rules": rules, "locked": locked, "remain_seconds": remain}, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def set_execution_guard_settings(

        enabled: Optional[bool] = None,

        trend_guard: Optional[bool] = None,

        trend_timeframe: str = "",

        cooldown_seconds: Optional[int] = None,

    ) -> str:

        """设置下单纪律拦截配置（运行时持久化到本地文件）"""

        rules = load_rules()

        if enabled is not None:

            rules["enabled"] = bool(enabled)

        if trend_guard is not None:

            rules["trend_guard"] = bool(trend_guard)

        if trend_timeframe and str(trend_timeframe).strip():

            rules["trend_timeframe"] = str(trend_timeframe).strip()

        if cooldown_seconds is not None:

            try:

                rules["cooldown_seconds"] = int(cooldown_seconds)

            except Exception:

                pass


        ok = save_rules(rules)

        if not ok:

            return "❌ 保存失败"

        return get_execution_guard_settings()


    # ==================== 第一板块：交易前逻辑安检 ====================


    @mcp.tool()

    @mcp_tool_safe

    def audit_trade_reason(symbol: str = "BTC/USDT", side: str = "buy", reason: str = "", timeframe: str = "1h") -> str:

        """

        理由审计官：验证你的交易理由是否与实际数据匹配。

        例如你说"RSI超卖"，AI会核实RSI是否真的低于30。

        """

        result = auditor.audit_reason(symbol=symbol, side=side, reason=reason, timeframe=timeframe)


        if result.get("passed"):

            md = f"# ✅ 理由审计通过\n\n"

        else:

            md = f"# ❌ 理由审计未通过\n\n"


        for c in result.get("confirmations", []):

            md += f"{c}\n"

        for i in result.get("issues", []):

            md += f"{i}\n"


        data = result.get("data", {})

        if data:

            md += f"\n## 当前市场数据\n"

            md += f"- 价格: {data.get('current_price')}\n"

            md += f"- RSI: {data.get('rsi')}\n"

            md += f"- EMA20/50/200: {data.get('ema20')}/{data.get('ema50')}/{data.get('ema200')}\n"


        return md


    @mcp.tool()

    @mcp_tool_safe

    def calculate_risk_reward(

        entry_price: float,

        stop_loss: float,

        take_profit: float,

        position_size: float = 0,

    ) -> str:

        """

        盈亏比计算器：输入入场价、止损价、止盈价，自动计算风险回报比。

        如果盈亏比低于1:1.5会给出警告。

        """

        result = auditor.calculate_risk_reward(

            entry_price=entry_price,

            stop_loss=stop_loss,

            take_profit=take_profit,

            position_size=position_size,

        )


        if "error" in result:

            return f"❌ {result['error']}"


        md = f"# 盈亏比分析\n\n"

        md += f"**方向**: {'做多' if result['side'] == 'long' else '做空'}\n"

        md += f"**入场价**: {result['entry']}\n"

        md += f"**止损价**: {result['stop_loss']} (风险 {result['risk_pct']}%)\n"

        md += f"**止盈价**: {result['take_profit']} (收益 {result['reward_pct']}%)\n\n"

        md += f"## 盈亏比: 1:{result['rr_ratio']}\n\n"


        if result.get('risk_amount'):

            md += f"- 潜在亏损: {result['risk_amount']} USDT\n"

            md += f"- 潜在盈利: {result['reward_amount']} USDT\n\n"


        md += f"## 建议\n{result['advice']}\n"


        return md


    @mcp.tool()

    @mcp_tool_safe

    def check_trend_alignment(symbol: str = "BTC/USDT", side: str = "buy", timeframe: str = "1h") -> str:

        """

        逆势警报器：检查你的交易方向是否与大趋势一致。

        逆势交易风险更高，会给出警告。

        """

        result = auditor.check_trend_alignment(symbol=symbol, side=side, timeframe=timeframe)


        if "error" in result:

            return f"❌ {result['error']}"


        md = f"# 趋势对齐检查\n\n"

        md += f"**交易对**: {result['symbol']}\n"

        md += f"**方向**: {'买入' if result['side'] == 'buy' else '卖出'}\n"

        md += f"**当前价格**: {result['current_price']}\n\n"

        md += f"**短期趋势** (EMA20 vs EMA50): {'上涨' if result['short_trend'] == 'up' else '下跌'}\n"

        md += f"**长期趋势** (vs EMA200): {'上涨' if result['long_trend'] == 'up' else '下跌'}\n\n"

        md += f"## 判定\n{result['warning']}\n"


        return md


    @mcp.tool()

    @mcp_tool_safe

    def check_fomo(symbol: str = "BTC/USDT", side: str = "buy", timeframe: str = "1h") -> str:

        """

        FOMO检测：检测你是否在追涨杀跌。

        如果价格短期暴涨/暴跌且偏离均线过远，会拦截交易。

        """

        result = auditor.check_fomo(symbol=symbol, side=side, timeframe=timeframe)


        if "error" in result:

            return f"❌ {result['error']}"


        md = f"# FOMO检测\n\n"

        md += f"**交易对**: {result['symbol']}\n"

        md += f"**方向**: {'买入' if result['side'] == 'buy' else '卖出'}\n"

        md += f"**当前价格**: {result['current_price']}\n\n"

        md += f"**短期涨跌幅**: {result['short_change_pct']}%\n"

        md += f"**偏离EMA20**: {result['deviation_from_ema20_pct']}%\n\n"

        md += f"## 判定\n{result['warning']}\n"


        if result['fomo_detected']:

            md += f"\n⛔ **建议**: 请等待回调后再入场！\n"


        return md


    # ==================== 第二板块：盘中实时陪练 ====================


    @mcp.tool()

    @mcp_tool_safe

    def hunt_patterns(pattern: str, symbols: str = "", timeframe: str = "1h") -> str:

        """

        形态寻宝游戏：扫描市场找出符合特定技术形态的币种。

        支持：顶背离、底背离、超买、超卖等。

        """

        result = coach.pattern_hunt(pattern=pattern, symbols=symbols, timeframe=timeframe)


        md = f"# 形态寻宝：{pattern}\n\n"

        md += f"{result['prompt']}\n\n"


        if result['results']:

            md += f"## 发现的标的\n"

            for r in result['results']:

                md += f"\n### {r['symbol']}\n"

                md += f"- {r['description']}\n"

                md += f"- 当前价格: {r['current_price']}\n"

                md += f"- RSI: {r['rsi']}\n"

                md += f"- 建议止损: {r['suggested_stop']}\n"


        return md


    @mcp.tool()

    @mcp_tool_safe

    def get_profit_protection_advice(

        symbol: str = "BTC/USDT",

        entry_price: float = 0,

        side: str = "long",

    ) -> str:

        """

        止盈保姆：当你的持仓盈利时，提供移动止损和保护利润的建议。

        """

        result = coach.profit_protector(symbol=symbol, entry_price=entry_price, side=side)


        md = f"# 止盈保姆建议\n\n"

        md += f"**交易对**: {result['symbol']}\n"

        md += f"**入场价**: {result['entry_price']}\n"

        md += f"**当前价**: {result['current_price']}\n"

        md += f"**浮盈**: {result['pnl_pct']}%\n\n"

        md += f"## 建议\n{result['advice']}\n"


        return md


    @mcp.tool()

    @mcp_tool_safe

    def analyze_loss(

        symbol: str = "BTC/USDT",

        entry_price: float = 0,

        exit_price: float = 0,

        side: str = "long",

        entry_reason: str = "",

    ) -> str:

        """

        亏损心理按摩：止损后的复盘分析，区分"好的亏损"和"坏的亏损"。

        帮助你从亏损中学习而不是沮丧。

        """

        result = coach.loss_analysis(

            symbol=symbol,

            entry_price=entry_price,

            exit_price=exit_price,

            side=side,

            entry_reason=entry_reason,

        )


        md = f"# 亏损复盘分析\n\n"

        md += f"**交易对**: {result['symbol']}\n"

        md += f"**方向**: {'做多' if result['side'] == 'long' else '做空'}\n"

        md += f"**入场价**: {result['entry_price']}\n"

        md += f"**出场价**: {result['exit_price']}\n"

        md += f"**亏损**: {result['pnl_pct']}%\n\n"

        md += f"## 亏损类型: {result['loss_type']}\n\n"

        md += f"## 心理按摩\n{result['comfort_message']}\n\n"

        md += f"## 改进建议\n{result['improvement']}\n"


        # 记录到日记和等级系统

        try:

            growth.log_journal_entry(

                action="止损",

                symbol=symbol,

                side=side,

                reason=entry_reason,

                outcome="loss",

                pnl_pct=result['pnl_pct'],

            )

            growth.record_trade(is_win=False, stop_loss_executed=True)

        except Exception:

            pass


        return md


    # ==================== 第三板块：历史时光机 ====================


    @mcp.tool()

    @mcp_tool_safe

    def simulate_what_if(

        symbol: str = "BTC/USDT",

        hours_ago: int = 1,

        stop_loss_pct: float = 2.0,

        side: str = "buy",

    ) -> str:

        """

        What-If模拟器：假如N小时前买入/卖出会怎样。

        验证你的"踏空焦虑"是否合理。

        """

        result = simulator.what_if(

            symbol=symbol,

            hours_ago=hours_ago,

            stop_loss_pct=stop_loss_pct,

            side=side,

        )


        if "error" in result:

            return f"❌ {result['error']}"


        md = f"# What-If 模拟\n\n"

        md += f"**假设**: {result['hours_ago']}小时前{'买入' if result['side'] == 'buy' else '卖出'} {result['symbol']}\n"

        md += f"**假设入场价**: {result['entry_price']}\n"

        md += f"**当前价格**: {result['current_price']}\n"

        md += f"**止损设置**: {result['stop_loss_pct']}% (止损价: {result['stop_price']})\n\n"


        if result['stopped_out']:

            md += f"⚠️ **结果**: 在第{result['stop_at_hour']}小时被止损出局\n"

        else:

            md += f"**理论盈亏**: {result['final_pnl_pct']}%\n"


        md += f"**期间最大回撤**: {result['max_drawdown_pct']}%\n\n"

        md += f"## 分析\n{result['message']}\n"


        return md


    @mcp.tool()

    @mcp_tool_safe

    def start_blind_history_test(

        symbol: str = "BTC/USDT",

        timeframe: str = "1h",

        candles: int = 30,

    ) -> str:

        """

        历史重演测验：给你一段隐藏时间的历史K线，让你判断走势。

        测试完成后调用 reveal_blind_test 揭晓答案。

        """

        result = simulator.blind_history_test(symbol=symbol, timeframe=timeframe, candles=candles)


        if "error" in result:

            return f"❌ {result['error']}"


        # 保存答案到会话

        from skills.learning.storage import create_session

        session_id = create_session(

            kind="blind_test",

            prompt=result['prompt'],

            payload={"candles": result['candles'], "test_id": result['test_id']},

            answer_key=result['answer'],

        )


        md = f"# 历史重演测验\n\n"

        md += f"**测试ID**: {session_id}\n\n"

        md += result['prompt'] + "\n\n"

        md += f"## K线数据（共{len(result['candles'])}根）\n\n"

        md += "| # | 开 | 高 | 低 | 收 | 量 |\n"

        md += "|---|---|---|---|---|---|\n"


        # 只显示最后10根，避免输出过长

        display_candles = result['candles'][-10:]

        for c in display_candles:

            md += f"| {c['index']} | {c['open']} | {c['high']} | {c['low']} | {c['close']} | {c['volume']} |\n"


        md += f"\n请回答后调用 `reveal_blind_test(session_id='{session_id}', your_choice='买入/卖出/观望')` 揭晓答案。\n"


        return md


    @mcp.tool()

    @mcp_tool_safe

    def reveal_blind_test(session_id: str, your_choice: str) -> str:

        """

        揭晓历史重演测验的答案。

        your_choice: 买入/卖出/观望

        """

        session = load_session(session_id)

        if not session:

            return "❌ 未找到测试会话"


        answer = session.get("answer_key", {})

        result = simulator.reveal_blind_test(your_choice, answer)


        # 记录训练

        try:

            growth.record_training()

        except Exception:

            pass


        md = f"# 测验结果\n\n"

        md += f"**你的选择**: {your_choice}\n"

        md += f"**实际走势**: {'上涨' if answer.get('direction') == 'up' else '下跌' if answer.get('direction') == 'down' else '横盘'} {abs(answer.get('change_pct', 0))}%\n\n"

        md += result


        return md


    @mcp.tool()

    @mcp_tool_safe

    def backtest_strategy(

        symbol: str = "BTC/USDT",

        strategy: str = "",

        days: int = 180,

        initial_capital: float = 10000,

    ) -> str:

        """

        策略验证沙盒：用自然语言描述策略，AI帮你回测验证。

        例如："RSI低于30时买入"

        """

        if not strategy:

            return "❌ 请描述你的策略，例如：'RSI低于30时买入'"


        result = simulator.strategy_backtest(

            symbol=symbol,

            strategy=strategy,

            days=days,

            initial_capital=initial_capital,

        )


        if "error" in result:

            return f"❌ {result['error']}"


        md = f"# 策略回测报告\n\n"

        md += f"**策略**: {result['strategy']}\n"

        md += f"**标的**: {result['symbol']}\n"

        md += f"**回测周期**: {result['test_days']}天\n"

        md += f"**初始资金**: {result['initial_capital']} USDT\n\n"

        md += f"## 结果\n"

        md += f"- 最终资金: {result['final_equity']} USDT\n"

        md += f"- 策略收益: {result['total_return_pct']}%\n"

        md += f"- 买入持有收益: {result['hold_return_pct']}%\n"

        md += f"- 总交易次数: {result['total_trades']}\n"

        md += f"- 胜率: {result['win_rate_pct']}% ({result['wins']}胜/{result['losses']}负)\n\n"

        md += f"## 结论\n{result['verdict']}\n"


        return md


    # ==================== 第四板块：成长与画像 ====================


    @mcp.tool()

    @mcp_tool_safe

    def log_trade_decision(

        action: str,

        symbol: str = "",

        side: str = "",

        reason: str = "",

        ai_warning: str = "",

        outcome: str = "",

        pnl_pct: float = 0,

        tags: str = "",

    ) -> str:

        """

        交易日记：记录一条交易决策（自动或手动）。

        tags用逗号分隔，如："追涨,无止损"

        """

        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []


        ok = growth.log_journal_entry(

            action=action,

            symbol=symbol,

            side=side,

            reason=reason,

            ai_warning=ai_warning,

            outcome=outcome,

            pnl_pct=pnl_pct,

            tags=tag_list,

        )


        if ok:

            return "✅ 交易决策已记录到日记"

        return "❌ 记录失败"


    @mcp.tool()

    @mcp_tool_safe

    def get_trade_journal(limit: int = 20, symbol: str = "", tag: str = "") -> str:

        """查看交易日记记录"""

        entries = growth.get_journal_entries(limit=limit, symbol=symbol, tag=tag)

        summary = growth.get_journal_summary()


        md = f"# 交易日记\n\n"

        md += f"**近30天统计**: {summary['total_entries']}条记录, {summary['wins']}胜/{summary['losses']}负\n"

        md += f"**无视AI警告次数**: {summary['ignored_ai_warnings']}\n\n"


        if entries:

            md += "## 最近记录\n"

            for e in entries[:10]:

                md += f"\n### {e.get('timestamp', '')[:16]} - {e.get('action', '')}\n"

                if e.get('symbol'):

                    md += f"- 交易对: {e['symbol']} ({e.get('side', '')})\n"

                if e.get('reason'):

                    md += f"- 理由: {e['reason']}\n"

                if e.get('ai_warning'):

                    md += f"- AI警告: {e['ai_warning']}\n"

                if e.get('outcome'):

                    md += f"- 结果: {e['outcome']} ({e.get('pnl_pct', 0)}%)\n"

                if e.get('tags'):

                    md += f"- 标签: {', '.join(e['tags'])}\n"


        return md


    @mcp.tool()

    @mcp_tool_safe

    def record_bad_habit(habit: str, context: str = "") -> str:

        """

        记录一次坏习惯。

        常见习惯：扛单、频繁操作、过早止盈、追涨杀跌、逆势交易、情绪化交易、过度自信、仓位过大

        """

        ok = growth.add_habit_record(habit=habit, context=context)

        if ok:

            summary = growth.get_habit_summary()

            md = f"✅ 已记录坏习惯：{habit}\n\n"

            md += f"## 你的坏习惯统计\n"

            for h in summary.get('habits', [])[:5]:

                md += f"- **{h['habit']}** ({h['count']}次) - {h['description']}\n"

            return md

        return "❌ 记录失败"


    @mcp.tool()

    @mcp_tool_safe

    def get_habit_warnings() -> str:

        """获取坏习惯统计和警告"""

        summary = growth.get_habit_summary()


        md = f"# 交易习惯分析\n\n"

        md += f"**总记录**: {summary['total_records']}次\n"


        if summary.get('worst_habit'):

            md += f"**最大问题**: {summary['worst_habit']}\n\n"


        if summary.get('habits'):

            md += "## 坏习惯排行\n"

            for h in summary['habits']:

                severity_icon = "🔴" if h['severity'] == 'high' else "🟡" if h['severity'] == 'medium' else "🟢"

                md += f"- {severity_icon} **{h['habit']}** ({h['count']}次): {h['description']}\n"

        else:

            md += "✨ 暂无坏习惯记录，继续保持！\n"


        return md


    @mcp.tool()

    @mcp_tool_safe

    def get_trader_level() -> str:

        """获取交易员等级和成就进度"""

        profile = growth.get_profile()

        progress = growth.get_level_progress()


        md = f"# 交易员档案\n\n"

        md += f"## 等级: Lv.{progress['level']} 【{progress['title']}】\n\n"

        md += f"**积分**: {progress['score']}\n"

        md += f"**升级进度**: {progress['progress_pct']}%\n"


        if progress.get('next_level_title'):

            md += f"**距离下一级**: {progress['points_to_next_level']}分 → 【{progress['next_level_title']}】\n\n"


        stats = profile.get('stats', {})

        md += f"## 战绩统计\n"

        md += f"- 总交易: {stats.get('total_trades', 0)}笔\n"

        md += f"- 胜负: {stats.get('wins', 0)}胜/{stats.get('losses', 0)}负\n"

        md += f"- 最长连胜: {stats.get('max_consecutive_wins', 0)}连胜\n"

        md += f"- 执行止损: {stats.get('stop_losses_executed', 0)}次\n"

        md += f"- 完成训练: {stats.get('trainings_completed', 0)}次\n\n"


        achievements = profile.get('achievements', [])

        md += f"## 成就 ({len(achievements)}/{progress['total_achievements']})\n"

        for a_key in achievements:

            a_info = growth.ACHIEVEMENTS.get(a_key, {})

            md += f"- 🏆 **{a_info.get('name', a_key)}**: {a_info.get('description', '')}\n"


        return md


    @mcp.tool()

    @mcp_tool_safe

    def record_trade_result(is_win: bool, stop_loss_executed: bool = False) -> str:

        """记录交易结果（用于更新等级和成就）"""

        result = growth.record_trade(is_win=is_win, stop_loss_executed=stop_loss_executed)


        md = f"✅ 交易结果已记录: {'盈利' if is_win else '亏损'}\n\n"


        if result.get('achievements_unlocked'):

            for a in result['achievements_unlocked']:

                md += f"🎉 {a['message']}\n"


        return md


    # ==================== 第五板块：辅助工具 ====================


    @mcp.tool()

    @mcp_tool_safe

    def calculate_volatility_size(

        symbol: str = "DOGE/USDT",

        intended_size_usdt: float = 1000,

        base_symbol: str = "BTC/USDT",

    ) -> str:

        """

        波动率换算：根据ATR调整仓位大小。

        如果目标币种波动率是BTC的3倍，建议仓位缩小到1/3。

        """

        result = utility.calculate_volatility_adjusted_size(

            symbol=symbol,

            intended_size_usdt=intended_size_usdt,

            base_symbol=base_symbol,

        )


        if "error" in result:

            return f"❌ {result['error']}"


        md = f"# 波动率仓位换算\n\n"

        md += f"**目标币种**: {result['symbol']} (ATR: {result['target_atr_pct']}%)\n"

        md += f"**基准币种**: {result['base_symbol']} (ATR: {result['base_atr_pct']}%)\n"

        md += f"**波动率倍数**: {result['volatility_ratio']}x\n\n"

        md += f"**原定仓位**: {result['intended_size']} USDT\n"

        md += f"**建议仓位**: {result['adjusted_size']} USDT\n"


        if result.get('adjusted_quantity'):

            md += f"**建议数量**: {result['adjusted_quantity']} {result['symbol'].split('/')[0]}\n"


        md += f"\n## 建议\n{result['advice']}\n"


        return md


    @mcp.tool()

    @mcp_tool_safe

    def check_market_events(keywords: str = "") -> str:

        """

        重要事件提醒：提醒你注意可能带来高波动的经济事件。

        keywords可选过滤，如"CPI"、"利率"

        """

        result = utility.check_upcoming_events(keywords=keywords)


        md = f"# 重要事件提醒\n\n"


        if result.get('events'):

            md += "## 相关事件\n"

            for e in result['events']:

                impact_icon = "🔴" if e['impact'] == 'high' else "🟡"

                md += f"- {impact_icon} **{e['name']}**: {e['description']}\n"


        md += f"\n{result['advice']}\n"

        md += f"\n**建议**: {result['recommendation']}\n"


        return md


    @mcp.tool()

    @mcp_tool_safe

    def quick_market_overview(symbols: str = "") -> str:

        """

        快速市场扫描：一次性获取多个币种的关键指标。

        symbols用逗号分隔，留空则扫描主流币种。

        """

        result = utility.quick_market_scan(symbols=symbols)


        md = f"# 市场快速扫描\n\n"

        md += f"**扫描币种数**: {result['scanned']}\n\n"


        if result.get('results'):

            md += "| 币种 | 价格 | 24h涨跌 | RSI | 状态 | 趋势 |\n"

            md += "|------|------|---------|-----|------|------|\n"

            for r in result['results']:

                change_icon = "📈" if r['change_24h_pct'] > 0 else "📉" if r['change_24h_pct'] < 0 else "➡️"

                md += f"| {r['symbol']} | {r['price']} | {change_icon} {r['change_24h_pct']}% | {r['rsi']} | {r['rsi_status']} | {r['trend']} |\n"


        return md
