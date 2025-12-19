############################################################
# 📘 文件说明：
# 本文件实现的功能：测试用例：验证 test_strategy_performance 相关逻辑的正确性与回归。
#
# 📋 程序整体伪代码（中文）：
# 1. 初始化主要依赖与变量
# 2. 加载输入数据或接收外部请求
# 3. 执行主要逻辑步骤（如计算、处理、训练、渲染等）
# 4. 输出或返回结果
# 5. 异常处理与资源释放
#
# 🔄 程序流程图（逻辑流）：
# ┌──────────┐
# │  输入数据 │
# └─────┬────┘
#       ↓
# ┌────────────┐
# │  核心处理逻辑 │
# └─────┬──────┘
#       ↓
# ┌──────────┐
# │  输出结果 │
# └──────────┘
#
# 📊 数据管道说明：
# 数据流向：输入源 → 数据清洗/转换 → 核心算法模块 → 输出目标（文件 / 接口 / 终端）
#
# 🧩 文件结构：
# - 依赖（标准库）：无
# - 依赖（第三方）：无
# - 依赖（本地）：skills.strategy.performance_tracker
#
# 🕒 创建时间：2025-12-19
############################################################

from skills.strategy.performance_tracker import StrategyPerformanceTracker


def test_strategy_performance_tracking(tmp_path):
    tracker = StrategyPerformanceTracker(storage_path=tmp_path / "perf.json")
    tracker.record_trade("alpha", pnl=120.0, exposure_minutes=30, tags=["trend"])
    tracker.record_trade("alpha", pnl=-30.0, exposure_minutes=10)
    tracker.record_trade("beta", pnl=-10.0, exposure_minutes=5)
    report = tracker.report()
    assert len(report["strategies"]) == 2
    alpha = next(item for item in report["strategies"] if item["name"] == "alpha")
    assert alpha["trades"] == 2
    assert alpha["total_pnl"] == 90.0
    drags = [item["name"] for item in report["drags"]]
    assert "beta" in drags
