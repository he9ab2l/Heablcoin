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
