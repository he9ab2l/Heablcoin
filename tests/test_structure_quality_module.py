import pandas as pd


from skills.market_analysis.data_provider import StandardMarketData

from skills.market_analysis.modules.structure_quality import analyze_structure_quality


def _sample_df(trend: float) -> pd.DataFrame:

    rows = []

    price = 100.0

    for idx in range(20):

        price += trend

        rows.append([idx, price - 1, price + 1, price - 2, price, 10])

    return pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])


def test_structure_quality_module_without_network():

    base_df = _sample_df(0.5)

    std = StandardMarketData(

        ohlcv=base_df.values.tolist(),

        ticker={"last": base_df["close"].iloc[-1]},

        df=base_df,

        metadata={"symbol": "BTC/USDT", "timeframe": "1h"},

    )

    synthetic = {

        "15m": _sample_df(0.3).values.tolist(),

        "4h": _sample_df(0.7).values.tolist(),

    }

    result = analyze_structure_quality(

        std,

        {

            "synthetic_frames": synthetic,

            "timeframes": ["1h", "15m", "4h"],

            "skip_fetch": True,

        },

    )

    assert result["module"] == "structure_quality"

    assert result["structure_alignment_score"] > 60

    assert result["volatility"]["label"] in {"calm", "balanced", "elevated"}
