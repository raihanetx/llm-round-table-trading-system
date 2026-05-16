#!/usr/bin/env python3
"""
Prompt Builder — Raw OHLCV data only. No indicators, no charts.
"""

from typing import List, Dict


def build_analysis_prompt(candles: List[Dict], pair: str = "EUR/USD", timeframe: str = "5min") -> str:
    """Build analysis prompt from raw candle data."""
    lines = []
    for i, c in enumerate(candles):
        lines.append(f"{i+1},{c['timestamp']},{c['open']},{c['high']},{c['low']},{c['close']},{c['volume']}")

    return f"""Analyze this {pair} {timeframe} chart. {len(candles)} candles.

candle#,timestamp,open,high,low,close,volume
{chr(10).join(lines)}

TRADE or SKIP? Respond JSON:
{{"decision":"TRADE"|"SKIP","confidence":0-100,"reasoning":"your analysis","direction":"BUY"|"SELL","entry":0.0,"stop_loss":0.0,"take_profit":0.0,"risk_reward":0.0}}"""


def build_debate_prompt(
    current_vote: str,
    my_reasoning: str,
    other_agents: List[Dict],
    candles: List[Dict],
    pair: str = "EUR/USD",
    timeframe: str = "5min",
) -> str:
    """
    Build debate prompt.

    other_agents: list of {"name": "Agent Alpha", "vote": "TRADE", "reasoning": "..."}
    """
    # Re-include the data (compact)
    lines = []
    for i, c in enumerate(candles):
        lines.append(f"{i+1},{c['timestamp']},{c['open']},{c['high']},{c['low']},{c['close']},{c['volume']}")

    others_text = ""
    for agent in other_agents:
        others_text += f"\n--- {agent['name']} (voted: {agent['vote']}) ---\n{agent['reasoning']}\n"

    return f"""You are in a ROUND TABLE DEBATE.

{pair} {timeframe} data ({len(candles)} candles):
candle#,timestamp,open,high,low,close,volume
{chr(10).join(lines)}

YOUR VOTE: {current_vote}
YOUR REASONING: {my_reasoning}

OTHER AGENTS:{others_text}

TASK:
1. Counter their points with specific candle evidence
2. Address each argument directly
3. Re-evaluate: do you CHANGE your vote?

Respond JSON:
{{"counter_argument":"your argument","vote_change":true|false,"new_vote":"TRADE"|"SKIP","reason_for_change":"why"}}"""
