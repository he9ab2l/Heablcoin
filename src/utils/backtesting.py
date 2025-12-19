"""

Simple Backtesting Module

------------------------


The backtesting module provides a lightweight way to evaluate trading

strategies on historical price data. In contrast to the

production-grade engine that is on the roadmap, this implementation

focuses on ease of use and minimal dependencies. It can operate on

preloaded arrays or pandas Series when available. No network

connectivity is required, making it ideal for offline development

environments.


Functions

---------

run_backtest(prices, signals)

    Runs a simple backtest by buying when a signal is positive and

    selling when negative. Computes cumulative returns and summary

    statistics.

"""


from __future__ import annotations


from typing import Iterable, Tuple


try:

    import numpy as np

except ImportError:

    # fallback minimal implementation using Python lists

    np = None  # type: ignore


def run_backtest(prices: Iterable[float], signals: Iterable[int]) -> Tuple[float, float]:

    """Runs a simple backtest and returns total return and win rate.


    Parameters

    ----------

    prices : Iterable[float]

        Sequence of historical closing prices.

    signals : Iterable[int]

        Sequence of trading signals. Use 1 for long/buy, -1 for short/sell,

        and 0 for neutral/no position. Length must match prices.


    Returns

    -------

    total_return : float

        The cumulative return of the strategy (in percentage terms).

    win_rate : float

        Proportion of trades that were profitable.


    Notes

    -----

    This is a simplistic implementation that does not account for

    transaction costs, slippage, or margin. It is intended for quick

    prototyping and verifying indicator logic.

    """

    prices_list = list(prices)

    signals_list = list(signals)

    if len(prices_list) != len(signals_list):

        raise ValueError("Prices and signals must have the same length")


    returns = []

    position = 0  # current position (1 long, -1 short, 0 flat)

    entry_price = 0.0

    wins = 0

    trades = 0


    for price, signal in zip(prices_list, signals_list):

        # enter or exit position when signal changes

        if signal != position:

            # exit current position if open

            if position != 0:

                pnl = position * (price - entry_price) / entry_price

                returns.append(pnl)

                if pnl > 0:

                    wins += 1

                trades += 1

                entry_price = 0.0

                position = 0

            # open new position

            if signal != 0:

                position = signal

                entry_price = price


    # close any open position at the end of data

    if position != 0 and entry_price != 0:

        pnl = position * (prices_list[-1] - entry_price) / entry_price

        returns.append(pnl)

        if pnl > 0:

            wins += 1

        trades += 1


    total_return = sum(returns)

    win_rate = wins / trades if trades > 0 else 0.0

    return total_return * 100.0, win_rate
