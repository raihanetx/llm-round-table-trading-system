#!/usr/bin/env python3
"""
Agent Runner — Fire 3 LLM agents and collect their votes.
"""

import json
import re
import time
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from gateway_client import GatewayClient


def parse_json_response(text: str) -> Dict:
    """Extract JSON from LLM response (handles markdown fences)."""
    # Try direct parse
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # Try extracting from ```json ... ```
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding first { ... }
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {"error": "Could not parse JSON", "raw": text[:500]}


class AgentRunner:
    """Runs multiple LLM agents and collects structured votes."""

    def __init__(self, agents_config: Dict, gateway: GatewayClient):
        """
        agents_config: {
            "alpha": {"model_id": "...", "name": "Agent Alpha", "role": "..."},
            "beta":  {"model_id": "...", "name": "Agent Beta",  "role": "..."},
            "gamma": {"model_id": "...", "name": "Agent Gamma", "role": "..."},
        }
        """
        self.agents = agents_config
        self.gateway = gateway

    def _build_system_prompt(self, agent_name: str, agent_cfg: Dict) -> str:
        """Build system prompt for an agent."""
        return (
            f"You are {agent_cfg['name']}, a {agent_cfg['role']} specialist. "
            f"Analyze the data and respond with valid JSON only. "
            f"Be specific — reference candle numbers. "
            f"Your analysis style: {agent_cfg['role']}."
        )

    def _run_single_agent(self, agent_id: str, agent_cfg: Dict, prompt: str) -> Dict:
        """Run a single agent and return parsed result."""
        system = self._build_system_prompt(agent_id, agent_cfg)
        result = self.gateway.chat_completion(
            model=agent_cfg["model_id"],
            prompt=prompt,
            system_prompt=system,
            temperature=agent_cfg.get("temperature", 0.3),
            max_tokens=agent_cfg.get("max_tokens", 1500),
        )

        if "error" in result:
            return {
                "agent_id": agent_id,
                "agent_name": agent_cfg["name"],
                "error": result["error"],
            }

        parsed = parse_json_response(result["content"])
        parsed["agent_id"] = agent_id
        parsed["agent_name"] = agent_cfg["name"]
        parsed["raw_response"] = result["content"]
        parsed["usage"] = result.get("usage", {})
        return parsed

    def run_analysis(self, prompt: str) -> List[Dict]:
        """
        Run all 3 agents in parallel on the same prompt.

        Returns list of 3 agent responses (dicts).
        """
        results = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._run_single_agent, aid, acfg, prompt): aid
                for aid, acfg in self.agents.items()
            }
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    agent_id = futures[future]
                    results.append({
                        "agent_id": agent_id,
                        "agent_name": self.agents[agent_id]["name"],
                        "error": str(e),
                    })

        # Sort by agent order (alpha, beta, gamma)
        order = list(self.agents.keys())
        results.sort(key=lambda r: order.index(r.get("agent_id", "")))
        return results

    def run_debate_round(self, debate_prompts: Dict[str, str]) -> List[Dict]:
        """
        Run a debate round — each agent gets their own debate prompt.

        debate_prompts: {"alpha": "...", "beta": "...", "gamma": "..."}
        """
        results = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._run_single_agent, aid, self.agents[aid], debate_prompts[aid]): aid
                for aid in self.agents if aid in debate_prompts
            }
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    agent_id = futures[future]
                    results.append({
                        "agent_id": agent_id,
                        "error": str(e),
                    })

        order = list(self.agents.keys())
        results.sort(key=lambda r: order.index(r.get("agent_id", "")))
        return results
