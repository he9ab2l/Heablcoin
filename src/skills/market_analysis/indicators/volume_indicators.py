from __future__ import annotations


import pandas as pd


def add_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:

    df["Volume_SMA"] = df["volume"].astype(float).rolling(window=20).mean()

    df["Volume_Ratio"] = df["volume"].astype(float) / df["Volume_SMA"]

    return df
