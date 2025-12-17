from __future__ import annotations

import pandas as pd

from market_analysis.indicators.momentum_indicators import add_momentum_indicators
from market_analysis.indicators.trend_indicators import add_trend_indicators
from market_analysis.indicators.volatility_indicators import add_volatility_indicators
from market_analysis.indicators.volume_indicators import add_volume_indicators


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = add_momentum_indicators(df)
    df = add_trend_indicators(df)
    df = add_volatility_indicators(df)
    df = add_volume_indicators(df)
    return df.bfill().ffill()
