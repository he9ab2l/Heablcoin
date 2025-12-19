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
