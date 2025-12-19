from skills.risk.fund_allocator import FundAllocator
from skills.risk.volatility_positioning import VolatilityPositionSizer
from skills.risk.circuit_breaker import CircuitBreaker


def test_fund_allocator_isolates_capital(tmp_path):
    path = tmp_path / "funds.json"
    allocator = FundAllocator(storage_path=path)
    state = allocator.set_pool("alpha", 1_000.0, max_drawdown_pct=0.3, notes="swing")
    assert state["capital"] == 1000.0
    allocator.allocate("alpha", 400.0)
    state = allocator.release("alpha", 200.0, realized_pnl=-50.0)
    assert state["locked"] == 200.0
    assert state["total_pnl"] == -50.0
    assert state["status"] in {"active", "frozen"}


def test_volatility_sizer_scales_positions():
    sizer = VolatilityPositionSizer(provider=None, min_scale=0.1, max_scale=1.5)
    prices = [100 + idx for idx in range(20)]
    result = sizer.suggest_notional(
        account_balance=10_000.0,
        risk_pct=0.02,
        symbol="BTC/USDT",
        timeframe="1h",
        target_vol=0.02,
        synthetic_prices=prices,
    )
    assert 0.1 <= result.scale <= 1.5
    assert result.suggested_notional > 0


def test_circuit_breaker_triggers(tmp_path):
    path = tmp_path / "cb.json"
    breaker = CircuitBreaker(storage_path=path)
    status = breaker.configure("BTC/USDT", threshold_pct=0.03, cooldown_minutes=5)
    assert status["threshold_pct"] == 3.0
    state = breaker.check_move("BTC/USDT", move_pct=0.05, liquidity_score=0.2, reason="spike")
    assert state["triggered"] is True
    assert state["halt_reasons"]
