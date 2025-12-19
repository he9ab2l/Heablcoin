from __future__ import annotations

import pandas as pd


def add_volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)

    std = close.rolling(window=20).std()
    df["BB_Upper"] = df["SMA_20"] + (std * 2)
    df["BB_Lower"] = df["SMA_20"] - (std * 2)
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / df["SMA_20"] * 100

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(window=14).mean()

    return df
