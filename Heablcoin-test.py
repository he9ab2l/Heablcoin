"""
Heablcoin-test - Heablcoin 终端综合测试入口
===========================================

目的：
- 在无需 MCP 客户端的情况下，对 Heablcoin 的核心能力做一键自检
- 默认无参数跑全量：连接/分析/账户/策略/日志/报告/通知开关/风控与白名单自检

说明：
- 这是一个“终端测试脚本”，允许使用 print 输出。
- MCP Server 进程严禁 print 到 stdout（会污染 JSONRPC），本脚本不受该限制。

用法示例：
  python Heablcoin-test.py --quick
  python Heablcoin-test.py --report
  python Heablcoin-test.py --self-check
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Heablcoin import (
    get_exchange,
    calculate_indicators,
    get_market_sentiment,
    get_comprehensive_analysis,
    get_account_summary,
    get_trade_history,
    get_trade_statistics,
    get_server_logs,
    get_system_status,
    get_multi_symbol_overview,
    get_available_strategies,
    calculate_position_size,
    execute_strategy,
    place_order,
    get_open_orders,
    get_ai_trading_advice,
    get_market_overview,
    get_trading_signals,
    get_position_recommendation,
    generate_analysis_report,
    get_notification_settings,
    set_notification_settings,
)

import pandas as pd


def _env_bool(name: str, default: bool = True) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if not v:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def _allowed_symbols() -> set:
    default = "BTC/USDT,ETH/USDT,BNB/USDT,ADA/USDT,XRP/USDT,SOL/USDT,DOT/USDT,DOGE/USDT,AVAX/USDT,LINK/USDT,MATIC/USDT,UNI/USDT,ATOM/USDT,LTC/USDT,ETC/USDT"
    s = os.getenv("ALLOWED_SYMBOLS", default)
    return {p.strip() for p in s.split(",") if p.strip()}


def print_header(title: str):
    print("\n" + "═" * 70)
    print(f"  {title}")
    print("═" * 70)


def print_section(title: str):
    print(f"\n--- {title} ---")


def test_connection() -> bool:
    print_header("🔌 交易所连接测试")
    try:
        exchange = get_exchange()
        ticker = exchange.fetch_ticker("BTC/USDT")
        print("✅ 连接成功!")
        print(f"   BTC/USDT: ${ticker['last']:,.2f}")
        if "percentage" in ticker:
            print(f"   24h 涨跌: {ticker['percentage']:.2f}%")
        return True
    except Exception as e:
        print(f"❌ 连接失败: {type(e).__name__}: {e}")
        return False


def test_system_status():
    print_header("⚙️ 系统状态")
    print(get_system_status())


def test_market_analysis():
    print_header("📊 市场分析测试")
    print_section("综合技术分析 (BTC/USDT)")
    print(get_comprehensive_analysis("BTC/USDT", "1h"))

    print_section("市场情绪分析 (BTC/USDT)")
    print(get_market_sentiment("BTC/USDT"))


def test_multi_overview():
    print_header("📈 多币种快速概览")
    print(get_multi_symbol_overview())


def test_account():
    print_header("💼 账户信息测试")

    print_section("账户资产摘要")
    print(get_account_summary())

    print_section("当前挂单")
    print(get_open_orders())


def test_trade_history():
    print_header("📜 交易历史测试")

    print_section("最近交易记录")
    print(get_trade_history(5))

    print_section("交易统计")
    print(get_trade_statistics())


def test_risk_management():
    print_header("🛡️ 风险管理测试")
    print("场景: 账户 $10000, 入场 $100000, 止损 $95000, 风险 2%")
    print(
        calculate_position_size(
            account_balance=10000,
            entry_price=100000,
            stop_loss=95000,
            risk_percent=2.0,
        )
    )


def test_strategies():
    print_header("🤖 自动策略测试")

    print_section("可用策略列表")
    print(get_available_strategies())

    print_section("策略信号检测 (不实际下单)")
    try:
        exchange = get_exchange()
        ohlcv = exchange.fetch_ohlcv("BTC/USDT", "1h", limit=60)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = calculate_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]

        print("\n当前指标:")
        print(f"  RSI: {curr['RSI']:.1f}")
        print(f"  SMA20: ${curr['SMA_20']:.2f}")
        print(f"  SMA50: ${curr['SMA_50']:.2f}")
        print(f"  布林带: ${curr['BB_Lower']:.2f} - ${curr['BB_Upper']:.2f}")
        print(f"  当前价: ${curr['close']:.2f}")

        print("\n策略触发检测:")
        print(f"  RSI_Oversold: {'✅ 触发' if curr['RSI'] < 30 else '⏸️ 未触发'}")
        print(f"  RSI_Overbought: {'✅ 触发' if curr['RSI'] > 70 else '⏸️ 未触发'}")

        ma_cross = "无"
        if prev["SMA_20"] <= prev["SMA_50"] and curr["SMA_20"] > curr["SMA_50"]:
            ma_cross = "金叉 ✅"
        elif prev["SMA_20"] >= prev["SMA_50"] and curr["SMA_20"] < curr["SMA_50"]:
            ma_cross = "死叉 ✅"
        print(f"  MA_Crossover: {ma_cross}")

        bb_break = "无"
        if curr["close"] < curr["BB_Lower"]:
            bb_break = "下轨突破 ✅"
        elif curr["close"] > curr["BB_Upper"]:
            bb_break = "上轨突破 ✅"
        print(f"  BB_Breakout: {bb_break}")

    except Exception as e:
        print(f"❌ 检测失败: {type(e).__name__}: {e}")


def test_logs():
    print_header("📋 日志测试")
    print(get_server_logs(10))


def test_ai_analysis():
    print_header("🤖 AI 智能分析测试")

    print_section("AI 交易建议 - 简单模式")
    print(get_ai_trading_advice("BTC/USDT", "simple"))

    print_section("AI 交易建议 - 专业模式")
    print(get_ai_trading_advice("BTC/USDT", "professional"))

    print_section("市场全景分析 - 简单模式")
    print(get_market_overview("simple"))

    print_section("市场全景分析 - 专业模式")
    print(get_market_overview("professional"))

    print_section("交易信号汇总")
    print(get_trading_signals("BTC/USDT"))

    print_section("智能仓位建议 - 保守型")
    print(get_position_recommendation("BTC/USDT", 10000, "conservative"))

    print_section("智能仓位建议 - 稳健型")
    print(get_position_recommendation("BTC/USDT", 10000, "moderate"))


def test_notification_controls():
    print_header("🔔 通知开关测试（不发送邮件）")
    print_section("当前通知设置")
    print(get_notification_settings())

    print_section("临时关闭交易执行通知（运行时覆盖）")
    print(set_notification_settings(notify_trade_execution=False))

    print_section("恢复为 env 默认（清空覆盖）")
    print(set_notification_settings(clear_overrides=True))


def test_safety_quick_checks():
    """不下真实单：只验证“白名单拦截/风控拦截”是否能在下单前生效。"""
    print_header("🧪 安全自检（白名单/风控拦截）")

    allowed = _allowed_symbols()
    max_amt = _env_float("MAX_TRADE_AMOUNT", 1000.0)

    print_section("白名单拦截：使用不在白名单的交易对")
    r1 = place_order("NOT_IN_LIST/USDT", "buy", 1.0, order_type="market")
    print(r1)

    print_section("风控拦截：构造大额金额（不会真实下单）")
    try:
        exchange = get_exchange()
        ticker = exchange.fetch_ticker("BTC/USDT")
        last_price = float(ticker.get("last", 0.0))
        if last_price <= 0:
            print("⚠️ 无法获取有效价格，跳过风控拦截测试")
            return

        amount = (max_amt * 2) / last_price
        r2 = place_order("BTC/USDT", "buy", amount, order_type="market")
        print(r2)
    except Exception as e:
        print(f"⚠️ 风控拦截测试依赖行情获取，当前失败: {type(e).__name__}: {e}")

    print_section("当前 env 关键配置")
    print(f"- EMAIL_NOTIFICATIONS_ENABLED={_env_bool('EMAIL_NOTIFICATIONS_ENABLED', False)}")
    print(f"- MAX_TRADE_AMOUNT={max_amt}")
    print(f"- DAILY_TRADE_LIMIT={_env_float('DAILY_TRADE_LIMIT', 5000.0)}")
    print(f"- ALLOWED_SYMBOLS(数量)={len(allowed)}")


def test_report(args):
    print_header("🧾 报告生成测试")
    try:
        result = generate_analysis_report(
            symbol=args.report_symbol,
            mode=args.report_mode,
            timeframe=args.report_timeframe,
            save_local=True,
            send_email_report=bool(args.report_email),
        )
        print(result)
    except Exception as e:
        print(f"❌ 报告生成失败: {type(e).__name__}: {e}")


def test_trading(dry_run: bool = True):
    print_header("🚀 交易测试")

    if dry_run:
        print("⚠️ 模式: 模拟运行 (不实际下单)")
        print("   使用 --trade 参数进行实际测试")
        return

    max_amt = _env_float("MAX_TRADE_AMOUNT", 1000.0)
    daily_limit = _env_float("DAILY_TRADE_LIMIT", 5000.0)

    print("⚠️ 模式: 实际测试 (将在测试网下单)")
    print("   交易对: BTC/USDT")
    print("   数量: 0.0001 BTC")
    print(f"   单笔限额: ${max_amt}")
    print(f"   每日限额: ${daily_limit}")

    confirm = input("\n确认执行测试下单? (y/N): ")
    if confirm.lower() != "y":
        print("已取消")
        return

    print(place_order("BTC/USDT", "buy", 0.0001, order_type="market"))


def main():
    parser = argparse.ArgumentParser(description="Heablcoin-test - Heablcoin 终端综合测试入口")
    parser.add_argument("--quick", action="store_true", help="快速测试 (连接 + 状态 + 分析 + AI)")
    parser.add_argument("--trade", action="store_true", help="包含实际下单测试（测试网）")
    parser.add_argument("--ai-only", action="store_true", help="仅测试 AI 分析功能")

    parser.add_argument("--report", action="store_true", help="生成一份分析报告（保存到本地 reports/）")
    parser.add_argument("--report-email", action="store_true", help="生成报告并尝试发送到邮箱（正文内嵌，受 NOTIFY_DAILY_REPORT 控制）")
    parser.add_argument("--report-symbol", default="BTC/USDT", help="报告交易对 (默认 BTC/USDT)")
    parser.add_argument("--report-mode", default="simple", help="报告模式 simple/professional (默认 simple)")
    parser.add_argument("--report-timeframe", default="1h", help="报告周期 (默认 1h)")

    parser.add_argument("--self-check", action="store_true", help="安全自检（白名单/风控拦截/通知开关展示）")
    parser.add_argument("--notify-test", action="store_true", help="通知开关测试（只切换设置，不发送邮件）")

    args = parser.parse_args()

    print("=" * 70)
    print("Heablcoin-test  |  Heablcoin 终端综合测试")
    print("=" * 70)

    allowed = _allowed_symbols()
    print(f"📋 允许交易: {len(allowed)} 个币种")
    print(
        f"💰 单笔限额: ${_env_float('MAX_TRADE_AMOUNT', 1000.0):,.0f} | 每日限额: ${_env_float('DAILY_TRADE_LIMIT', 5000.0):,.0f}"
    )

    full_run = not any(
        [
            args.quick,
            args.ai_only,
            args.trade,
            args.report,
            args.report_email,
            args.self_check,
            args.notify_test,
        ]
    )

    if args.self_check or full_run:
        test_safety_quick_checks()

    if not test_connection():
        print("\n❌ 无法连接交易所，请检查 .env 配置")
        return

    if args.ai_only:
        test_ai_analysis()
    elif args.quick:
        test_system_status()
        test_market_analysis()
        test_ai_analysis()
    else:
        test_system_status()
        test_market_analysis()
        test_multi_overview()
        test_account()
        test_trade_history()
        test_risk_management()
        test_strategies()
        test_ai_analysis()
        test_logs()
        test_trading(dry_run=not args.trade)

        test_notification_controls()

        args.report = True
        args.report_email = False
        test_report(args)

    if args.notify_test and not full_run:
        test_notification_controls()

    if (args.report or args.report_email) and not full_run:
        test_report(args)

    print("\n" + "═" * 70)
    print("  🎉 测试完成!")
    print("═" * 70)


if __name__ == "__main__":
    main()
