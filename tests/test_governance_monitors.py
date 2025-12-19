############################################################
# 📘 文件说明：
# 本文件实现的功能：测试用例：验证 test_governance_monitors 相关逻辑的正确性与回归。
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
# - 依赖（标准库）：json
# - 依赖（第三方）：无
# - 依赖（本地）：skills.governance.ai_confidence, skills.governance.audit_trail, skills.governance.bias_monitor
#
# 🕒 创建时间：2025-12-19
############################################################

import json

from skills.governance.ai_confidence import DecisionConfidenceMonitor
from skills.governance.bias_monitor import BiasMonitor
from skills.governance.audit_trail import AuditTrail


def test_confidence_monitor_scoring(tmp_path):
    monitor = DecisionConfidenceMonitor(storage_path=tmp_path / "conf.json")
    entry = monitor.score(
        "decision-1",
        inputs={"signal_strength": 0.9, "data_quality": 0.8, "risk_alignment": 0.7, "latency": 0.6},
        rationale="multi-signal confirmation",
        tags=["trend"],
    )
    assert entry["action"] in {"auto_execute", "human_confirm", "advisory"}
    assert entry["score"] > 0
    log = monitor.recent()
    assert log["entries"]


def test_bias_monitor_diagnosis(tmp_path):
    monitor = BiasMonitor(storage_path=tmp_path / "bias.json")
    for _ in range(12):
        monitor.record("long", "win", 5.0, "trend")
    report = monitor.diagnose()
    assert report["sample_count"] >= 12
    assert isinstance(report["warnings"], list)


def test_audit_trail(tmp_path):
    trail = AuditTrail(storage_path=tmp_path / "audit.json")
    entry = trail.log("task_publish", "info", payload={"task": "rebalance"}, requires_ack=True)
    assert entry["requires_ack"] is True
    events = trail.list_events()
    assert events["events"]
