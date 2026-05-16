#!/usr/bin/env python3
"""
Trade Executor — Simulate trades, monitor TP/SL.
"""

from typing import Dict, List, Optional, Tuple


class TradeExecutor:
    """Simulates trades against candle data."""

    def __init__(self, min_risk_reward: float = 1.5, default_lot: float = 0.01):
        self.min_risk_reward = min_risk_reward
        self.default_lot = default_lot
        self.trade_log: List[Dict] = []

    def validate_trade(self, params: Dict) -> Tuple[bool, str]:
        """Validate trade parameters."""
        direction = params.get("direction", "").upper()
        entry = params.get("entry", 0)
        sl = params.get("stop_loss", 0)
        tp = params.get("take_profit", 0)

        if direction not in ("BUY", "SELL"):
            return False, f"Invalid direction: {direction}"
        if entry <= 0 or sl <= 0 or tp <= 0:
            return False, f"Invalid levels: entry={entry}, sl={sl}, tp={tp}"

        if direction == "BUY":
            if sl >= entry:
                return False, f"BUY but SL ({sl}) >= entry ({entry})"
            if tp <= entry:
                return False, f"BUY but TP ({tp}) <= entry ({entry})"
            risk = entry - sl
            reward = tp - entry
        else:  # SELL
            if sl <= entry:
                return False, f"SELL but SL ({sl}) <= entry ({entry})"
            if tp >= entry:
                return False, f"SELL but TP ({tp}) >= entry ({entry})"
            risk = sl - entry
            reward = entry - tp

        rr = reward / risk if risk > 0 else 0
        if rr < self.min_risk_reward - 0.001:  # float tolerance
            return False, f"R:R too low: {rr:.2f} (min {self.min_risk_reward})"

        return True, f"Valid: {direction} entry={entry} SL={sl} TP={tp} R:R={rr:.2f}"

    def simulate_trade(
        self,
        params: Dict,
        candles: List[Dict],
        start_index: int,
    ) -> Dict:
        """
        Simulate a trade against future candles.

        Walks through candles from start_index until TP or SL is hit.

        Returns: {
            "result": "TP_HIT" | "SL_HIT" | "NO_HIT",
            "entry_candle": int,
            "exit_candle": int,
            "entry_price": float,
            "exit_price": float,
            "pnl": float,
            "candles_held": int,
        }
        """
        direction = params.get("direction", "BUY").upper()
        entry = params.get("entry", 0)
        sl = params.get("stop_loss", 0)
        tp = params.get("take_profit", 0)

        for i in range(start_index, len(candles)):
            candle = candles[i]
            high = candle["high"]
            low = candle["low"]

            if direction == "BUY":
                # Check SL first (worst case)
                if low <= sl:
                    pnl = sl - entry
                    return self._log_trade("SL_HIT", start_index, i, entry, sl, pnl, i - start_index + 1)
                # Check TP
                if high >= tp:
                    pnl = tp - entry
                    return self._log_trade("TP_HIT", start_index, i, entry, tp, pnl, i - start_index + 1)
            else:  # SELL
                if high >= sl:
                    pnl = entry - sl
                    return self._log_trade("SL_HIT", start_index, i, entry, sl, pnl, i - start_index + 1)
                if low <= tp:
                    pnl = entry - tp
                    return self._log_trade("TP_HIT", start_index, i, entry, tp, pnl, i - start_index + 1)

        # Ran out of candles
        return self._log_trade("NO_HIT", start_index, len(candles) - 1, entry, entry, 0, len(candles) - start_index)

    def _log_trade(
        self,
        result: str,
        entry_candle: int,
        exit_candle: int,
        entry_price: float,
        exit_price: float,
        pnl: float,
        candles_held: int,
    ) -> Dict:
        trade = {
            "result": result,
            "entry_candle": entry_candle,
            "exit_candle": exit_candle,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": round(pnl, 5),
            "candles_held": candles_held,
        }
        self.trade_log.append(trade)
        return trade

