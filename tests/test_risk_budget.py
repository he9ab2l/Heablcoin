############################################################
# 📘 文件说明：
# 本文件实现的功能：测试用例：验证 test_risk_budget 相关逻辑的正确性与回归。
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
# - 依赖（本地）：skills.risk.budget_manager
#
# 🕒 创建时间：2025-12-19
############################################################

from skills.risk.budget_manager import RiskBudgetManager


def test_risk_budget_manager_freeze(tmp_path):
    path = tmp_path / "risk.json"
    manager = RiskBudgetManager(storage_path=path, budgets={"daily": 100.0, "weekly": 300.0, "monthly": 900.0})
    status = manager.get_status()
    assert status["periods"]["daily"]["budget"] == 100.0

    manager.record_event(60.0, tag="test", note="first loss")
    manager.record_event(50.0, tag="test", note="second loss")
    status = manager.get_status()
    assert status["periods"]["daily"]["frozen"] is True
    assert status["periods"]["daily"]["remaining"] == 0.0

    manager.update_budget("daily", 150.0, unfreeze=True)
    status = manager.get_status()
    assert status["periods"]["daily"]["budget"] == 150.0
    assert status["periods"]["daily"]["frozen"] is False


def test_risk_budget_reset(tmp_path):
    path = tmp_path / "risk.json"
    manager = RiskBudgetManager(storage_path=path, budgets={"daily": 50.0, "weekly": 200.0, "monthly": 500.0})
    manager.record_event(20.0)
    status = manager.get_status()
    assert status["periods"]["daily"]["used"] == 20.0
    manager.reset_period("daily")
    status = manager.get_status()
    assert status["periods"]["daily"]["used"] == 0.0
