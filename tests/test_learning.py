"""学习模块单元测试"""
from __future__ import annotations
import sys
import os


# 添加项目根目录与 src 到路径（支持直接运行本文件）
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)
passed = 0
failed = 0


def test(name: str, condition: bool, msg: str = "") -> None:
    global passed, failed
    if condition:
        print(f"✅ 通过: {name}")
        passed += 1
    else:
        print(f"❌ 失败: {name} - {msg}")
        failed += 1


def main():
    global passed, failed
    print("=" * 60)
    print("🧪 学习模块单元测试")
    print("=" * 60)
    print()
    # ==================== 测试1: 模块导入 ====================
    print("📝 测试1: 模块导入")
    try:
        from skills.learning.registry import LearningRegistry, LearningModule
        from skills.learning.modules.pre_trade import PreTradeAuditModule
        from skills.learning.modules.in_trade import InTradeCoachModule
        from skills.learning.modules.history import HistorySimModule
        from skills.learning.modules.growth import GrowthProfileModule
        from skills.learning.modules.utility import UtilityModule
        from skills.learning.notifier import send_learning_report


        test("模块导入", True)
    except Exception as e:
        test("模块导入", False, str(e))
        return
    # ==================== 测试2: 注册器功能 ====================
    print("\n📝 测试2: 注册器功能")
    try:
        registry = LearningRegistry()
        registry.register(
            name="test_module",
            title="测试模块",
            description="用于测试",
            handler=lambda: {"status": "ok"},
            enabled_by_default=True,
        )
        module = registry.get("test_module")
        test("注册器注册", module is not None)
        test("注册器获取", module.name == "test_module")
        test("注册器列表", "test_module" in registry.list())
        test("注册器默认", "test_module" in registry.defaults())
        catalog = registry.catalog()
        test("注册器目录", len(catalog) > 0 and catalog[0]["key"] == "test_module")
    except Exception as e:
        test("注册器功能", False, str(e))
    # ==================== 测试3: 盈亏比计算 ====================
    print("\n📝 测试3: 盈亏比计算")
    try:
        auditor = PreTradeAuditModule()
        result = auditor.calculate_risk_reward(
            entry_price=100,
            stop_loss=95,
            take_profit=115,
            position_size=1000,
        )
        test("盈亏比-无错误", "error" not in result)
        test("盈亏比-方向正确", result.get("side") == "long")
        test("盈亏比-比值计算", result.get("rr_ratio") == 3.0)
        test("盈亏比-风险金额", result.get("risk_amount") == 50.0)
        test("盈亏比-收益金额", result.get("reward_amount") == 150.0)
    except Exception as e:
        test("盈亏比计算", False, str(e))
    # ==================== 测试4: 成长档案 ====================
    print("\n📝 测试4: 成长档案")
    try:
        growth = GrowthProfileModule()
        # 获取档案
        profile = growth.get_profile()
        test("成长档案-获取", isinstance(profile, dict))
        test("成长档案-包含score", "score" in profile)
        test("成长档案-包含stats", "stats" in profile)
        # 获取等级进度
        progress = growth.get_level_progress()
        test("等级进度-获取", isinstance(progress, dict))
        test("等级进度-包含level", "level" in progress)
        test("等级进度-包含title", "title" in progress)
    except Exception as e:
        test("成长档案", False, str(e))
    # ==================== 测试5: 交易日记 ====================
    print("\n📝 测试5: 交易日记")
    try:
        growth = GrowthProfileModule()
        # 记录日记
        ok = growth.log_journal_entry(
            action="测试交易",
            symbol="BTC/USDT",
            side="buy",
            reason="单元测试",
            outcome="win",
            pnl_pct=5.0,
            tags=["test"],
        )
        test("交易日记-记录", ok)
        # 获取日记
        entries = growth.get_journal_entries(limit=5, tag="test")
        test("交易日记-获取", len(entries) > 0)
        # 获取统计
        summary = growth.get_journal_summary()
        test("交易日记-统计", "total_entries" in summary)
    except Exception as e:
        test("交易日记", False, str(e))
    # ==================== 测试6: 坏习惯追踪 ====================
    print("\n📝 测试6: 坏习惯追踪")
    try:
        growth = GrowthProfileModule()
        # 记录坏习惯
        ok = growth.add_habit_record(habit="测试习惯", context="单元测试")
        test("坏习惯-记录", ok)
        # 获取统计
        summary = growth.get_habit_summary()
        test("坏习惯-统计", "total_records" in summary)
        test("坏习惯-习惯列表", "habits" in summary)
    except Exception as e:
        test("坏习惯追踪", False, str(e))
    # ==================== 测试7: 辅助工具 ====================
    print("\n📝 测试7: 辅助工具")
    try:
        utility = UtilityModule()
        # 事件提醒
        events = utility.check_upcoming_events(keywords="CPI")
        test("事件提醒-获取", "events" in events)
        test("事件提醒-建议", "advice" in events)
    except Exception as e:
        test("辅助工具", False, str(e))
    # ==================== 测试8: 邮件通知（配置检查） ====================
    print("\n📝 测试8: 邮件通知配置")
    try:
        from skills.learning.notifier import send_learning_report


        # 不发送，只检查函数存在
        test("邮件通知-函数存在", callable(send_learning_report))
        # 检查其他函数
        from skills.learning.notifier import send_training_summary, send_daily_learning_report


        test("邮件通知-训练总结函数", callable(send_training_summary))
        test("邮件通知-每日报告函数", callable(send_daily_learning_report))
    except Exception as e:
        test("邮件通知配置", False, str(e))
    # ==================== 结果汇总 ====================
    print()
    print("=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    return failed == 0
if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
