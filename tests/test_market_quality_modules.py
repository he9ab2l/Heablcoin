import pandas as pd

from skills.market_analysis.data_provider import StandardMarketData
from skills.market_analysis.modules.flow_pressure import analyze_flow_pressure
from skills.market_analysis.modules.market_quality import analyze_market_quality


def _sample_df():
    rows = []
    price = 100.0
    for idx in range(60):
        price += 0.3 if idx % 2 == 0 else -0.1
        rows.append([idx, price - 0.5, price + 0.5, price - 1, price, 50 + idx])
    return pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])


def test_flow_pressure_without_network():
    df = _sample_df()
    data = StandardMarketData(
        ohlcv=df.values.tolist(),
        ticker={"last": df["close"].iloc[-1]},
        df=df,
        metadata={"symbol": "BTC/USDT", "timeframe": "1h"},
    )
    payload = analyze_flow_pressure(data, {})
    assert payload["name"] == "flow_pressure"
    assert payload["state"] in {"buying", "selling", "balanced"}


def test_market_quality_combines_modules():
    df = _sample_df()
    data = StandardMarketData(
        ohlcv=df.values.tolist(),
        ticker={"last": df["close"].iloc[-1]},
        df=df,
        metadata={"symbol": "BTC/USDT", "timeframe": "1h"},
    )
    payload = analyze_market_quality(data, {"skip_fetch": True})
    assert payload["name"] == "market_quality"
    assert 0 <= payload["quality_score"] <= 100
