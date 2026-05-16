#!/usr/bin/env python3
"""
Data Loader — CSV reader + sliding window.
"""

import csv
from typing import List, Dict


def load_csv(filepath: str) -> List[Dict]:
    """Load OHLCV data from CSV file."""
    candles = []
    with open(filepath, "r") as f:
        for row in csv.DictReader(f):
            candles.append({
                "timestamp": row["timestamp"].strip(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
            })
    return candles


def get_window(candles: List[Dict], start: int, size: int) -> List[Dict]:
    """Extract a window of candles starting at index."""
    end = min(start + size, len(candles))
    return candles[start:end]


def window_summary(window: List[Dict]) -> str:
    """One-line summary of a window for logging."""
    if not window:
        return "empty"
    first = window[0]
    last = window[-1]
    return (
        f"candles {first['timestamp']} → {last['timestamp']} | "
        f"close {first['close']:.5f} → {last['close']:.5f}"
    )
