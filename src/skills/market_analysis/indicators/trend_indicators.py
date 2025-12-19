from __future__ import annotations


import pandas as pd


def add_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:

    close = df["close"].astype(float)


    df["SMA_7"] = close.rolling(window=7).mean()

    df["SMA_20"] = close.rolling(window=20).mean()

    df["SMA_50"] = close.rolling(window=50).mean()


    df["EMA_12"] = close.ewm(span=12, adjust=False).mean()

    df["EMA_26"] = close.ewm(span=26, adjust=False).mean()


    df["MACD_Line"] = df["EMA_12"] - df["EMA_26"]

    df["Signal_Line"] = df["MACD_Line"].ewm(span=9, adjust=False).mean()

    df["MACD_Hist"] = df["MACD_Line"] - df["Signal_Line"]


    return df
