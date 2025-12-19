from __future__ import annotations

import pandas as pd

from .momentum_indicators import add_momentum_indicators
from .trend_indicators import add_trend_indicators
from .volatility_indicators import add_volatility_indicators
from .volume_indicators import add_volume_indicators


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = add_momentum_indicators(df)
    df = add_trend_indicators(df)
    df = add_volatility_indicators(df)
    df = add_volume_indicators(df)
    return df.bfill().ffill()
