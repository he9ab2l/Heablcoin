from skills.strategy.registry import StrategyRegistry


def test_strategy_registry_basic(tmp_path):

    registry = StrategyRegistry(storage_path=tmp_path / "strategies.json")

    registry.register(

        name="trend_alpha",

        version="1.0",

        owner="deskA",

        symbol="BTC/USDT",

        timeframe="1h",

        direction="long",

        risk_level="medium",

        description="trend follower",

        tags=["trend", "momentum"],

    )

    registry.register(

        name="reversion_guard",

        version="0.3",

        owner="deskB",

        symbol="BTC/USDT",

        timeframe="1h",

        direction="short",

        risk_level="high",

        description="mean reversion",

    )

    result = registry.list(include_conflicts=True)

    assert len(result["strategies"]) == 2

    assert result["conflicts"], "Opposite directions should flag conflict"


    registry.set_enabled("trend_alpha", False)

    result = registry.list(filter_active=True)

    assert len(result["strategies"]) == 1
