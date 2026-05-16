#!/usr/bin/env python3
"""
Debate Manager — Multi-round debate protocol.
"""

from typing import Dict, List
from raw_prompt import build_debate_prompt
from consensus_engine import extract_vote, check_consensus


class DebateManager:
    """Manages the round table debate when agents are split."""

    def __init__(self, agent_runner, max_rounds: int = 3):
        self.runner = agent_runner
        self.max_rounds = max_rounds

    def run_debate(
        self,
        initial_responses: List[Dict],
        candles: List[Dict],
        pair: str = "EUR/USD",
        timeframe: str = "5min",
    ) -> Dict:
        """
        Run debate rounds until consensus or max rounds reached.

        Returns: {
            "action": "EXECUTE" | "SKIP",
            "rounds": [...],
            "final_votes": [...],
            "reason": str,
        }
        """
        current_responses = initial_responses
        debate_history = []

        for round_num in range(1, self.max_rounds + 1):
            # Identify majority and minority
            votes = [extract_vote(r) for r in current_responses]
            trade_agents = [r for r in current_responses if extract_vote(r) == "TRADE"]
            skip_agents = [r for r in current_responses if extract_vote(r) == "SKIP"]

            # Build debate prompts for each agent
            debate_prompts = {}
            for agent in current_responses:
                agent_id = agent["agent_id"]
                my_vote = extract_vote(agent)
                my_reasoning = agent.get("reasoning", agent.get("raw_response", ""))

                # Build "other agents" list
                others = []
                for other in current_responses:
                    if other["agent_id"] != agent_id:
                        others.append({
                            "name": other.get("agent_name", other["agent_id"]),
                            "vote": extract_vote(other),
                            "reasoning": other.get("reasoning", other.get("raw_response", "")),
                        })

                debate_prompts[agent_id] = build_debate_prompt(
                    current_vote=my_vote,
                    my_reasoning=my_reasoning,
                    other_agents=others,
                    candles=candles,
                    pair=pair,
                    timeframe=timeframe,
                )

            # Run debate round
            debate_responses = self.runner.run_debate_round(debate_prompts)

            # Check if any agent changed their vote
            new_votes = []
            for resp in debate_responses:
                if "error" in resp:
                    # Keep original vote on error
                    orig = next(
                        (r for r in current_responses if r["agent_id"] == resp["agent_id"]),
                        None,
                    )
                    new_votes.append(extract_vote(orig) if orig else "SKIP")
                else:
                    vote_change = resp.get("vote_change", False)
                    if vote_change:
                        new_vote = resp.get("new_vote", "SKIP").strip().upper()
                        new_votes.append(new_vote if new_vote in ("TRADE", "SKIP") else "SKIP")
                    else:
                        new_votes.append(extract_vote(resp))

            # Update responses with new votes
            updated_responses = []
            for i, resp in enumerate(debate_responses):
                if "error" not in resp:
                    resp["decision"] = new_votes[i]
                    resp["debate_round"] = round_num
                updated_responses.append(resp)

            current_responses = updated_responses

            # Record debate round
            debate_history.append({
                "round": round_num,
                "votes": new_votes,
                "responses": [
                    {
                        "agent": r.get("agent_id"),
                        "vote": new_votes[i],
                        "counter_argument": r.get("counter_argument", ""),
                        "vote_change": r.get("vote_change", False),
                        "reason_for_change": r.get("reason_for_change", ""),
                    }
                    for i, r in enumerate(debate_responses)
                ],
            })

            # Check consensus
            action, reason = check_consensus(new_votes)
            if action == "EXECUTE":
                return {
                    "action": "EXECUTE",
                    "rounds": debate_history,
                    "final_votes": new_votes,
                    "final_responses": current_responses,
                    "reason": reason,
                }
            elif action == "SKIP":
                return {
                    "action": "SKIP",
                    "rounds": debate_history,
                    "final_votes": new_votes,
                    "final_responses": current_responses,
                    "reason": reason,
                }
            # If still DEBATE, continue to next round

        # Max rounds reached — default to SKIP (safety)
        final_votes = [extract_vote(r) for r in current_responses]
        return {
            "action": "SKIP",
            "rounds": debate_history,
            "final_votes": final_votes,
            "final_responses": current_responses,
            "reason": f"Max debate rounds ({self.max_rounds}) reached — defaulting to SKIP",
        }
