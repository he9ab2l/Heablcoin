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
