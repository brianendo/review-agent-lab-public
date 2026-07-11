"""Minimal backtest PnL helpers (sample repo for the harness end-to-end test)."""

from typing import List


def total_pnl(candles: List[dict]) -> float:
    """Sum realized PnL across candles.

    Each candle is a dict with a "pnl" float. Returns the total.
    """
    total = 0.0
    for i in range(len(candles) - 1):
        total += candles[i]["pnl"]
    return total


def average_pnl(candles: List[dict]) -> float:
    """Mean PnL per candle."""
    if not candles:
        return 0.0
    return total_pnl(candles) / len(candles)
