#!/usr/bin/env python3
"""
Consensus Engine — Count votes, determine action.
"""

from typing import Dict, List, Tuple


def extract_vote(agent_response: Dict) -> str:
    """Extract TRADE/SKIP vote from agent response. Defaults to SKIP on error."""
    if "error" in agent_response:
        return "SKIP"

    decision = agent_response.get("decision", "SKIP")
    if isinstance(decision, str):
        decision = decision.strip().upper()
    return decision if decision in ("TRADE", "SKIP") else "SKIP"


def extract_trade_params(agent_response: Dict) -> Dict:
    """Extract trade parameters from agent response."""
    return {
        "direction": agent_response.get("direction", "BUY"),
        "entry": agent_response.get("entry", 0),
        "stop_loss": agent_response.get("stop_loss", 0),
        "take_profit": agent_response.get("take_profit", 0),
        "risk_reward": agent_response.get("risk_reward", 0),
        "confidence": agent_response.get("confidence", 0),
    }


def check_consensus(votes: List[str]) -> Tuple[str, str]:
    """
    Check consensus from 3 votes.

    Returns: (action, reason)
        action: "EXECUTE" | "DEBATE" | "SKIP"
        reason: human-readable explanation
    """
    trade_count = votes.count("TRADE")
    skip_count = votes.count("SKIP")

    if trade_count == 3:
        return "EXECUTE", "Unanimous TRADE — all 3 agents agree"
    elif trade_count >= 2:
        return "DEBATE", f"Split: {trade_count} TRADE, {skip_count} SKIP — debate required"
    else:
        return "SKIP", f"Majority SKIP: {trade_count} TRADE, {skip_count} SKIP"


def get_trade_params_from_majority(responses: List[Dict]) -> Dict:
    """
    Get trade parameters from agents who voted TRADE.
    Averages entry/SL/TP from all TRADE voters.
    """
    traders = [r for r in responses if extract_vote(r) == "TRADE"]
    if not traders:
        return {}

    # Use the highest confidence trader's direction
    best = max(traders, key=lambda r: r.get("confidence", 0))
    direction = best.get("direction", "BUY")

    # Average the levels
    entries = [t.get("entry", 0) for t in traders if t.get("entry")]
    sls = [t.get("stop_loss", 0) for t in traders if t.get("stop_loss")]
    tps = [t.get("take_profit", 0) for t in traders if t.get("take_profit")]
    rrs = [t.get("risk_reward", 0) for t in traders if t.get("risk_reward")]

    return {
        "direction": direction,
        "entry": sum(entries) / len(entries) if entries else 0,
        "stop_loss": sum(sls) / len(sls) if sls else 0,
        "take_profit": sum(tps) / len(tps) if tps else 0,
        "risk_reward": sum(rrs) / len(rrs) if rrs else 0,
        "confidence": best.get("confidence", 0),
        "consensus_agents": [t["agent_id"] for t in traders],
    }
