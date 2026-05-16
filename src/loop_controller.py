#!/usr/bin/env python3
"""
Loop Controller — The main trading loop.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from data_loader import load_csv, get_window, window_summary
from raw_prompt import build_analysis_prompt
from agent_runner import AgentRunner
from consensus_engine import extract_vote, check_consensus, get_trade_params_from_majority
from debate_manager import DebateManager
from trade_executor import TradeExecutor


class LoopController:
    """Runs the infinite trading loop."""

    def __init__(self, configs: Dict, logs_dir: Path):
        self.configs = configs
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(exist_ok=True)

        self.window_size = configs["trading"]["window_size"]
        self.pair = configs["trading"]["pair"]
        self.timeframe = configs["trading"]["timeframe"]

        # Components
        self.agent_runner = AgentRunner(configs["agents"], configs["gateway_client"])
        self.debate_manager = DebateManager(
            self.agent_runner,
            max_rounds=configs["trading"].get("max_debate_rounds", 3),
        )
        self.trade_executor = TradeExecutor(
            min_risk_reward=configs["trading"].get("min_risk_reward", 1.5),
            default_lot=configs["trading"].get("default_lot_size", 0.01),
        )

        # Stats
        self.stats = {
            "total_cycles": 0,
            "trades_executed": 0,
            "trades_skipped": 0,
            "debates_triggered": 0,
            "tp_hits": 0,
            "sl_hits": 0,
            "no_hits": 0,
            "total_pnl": 0.0,
        }

    def _log(self, message: str):
        """Print and write to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line)

        log_file = self.logs_dir / "trading.log"
        with open(log_file, "a") as f:
            f.write(line + "\n")

    def _log_decision(self, cycle: int, window_start: int, action: str, details: Dict):
        """Log decision to decisions.log."""
        entry = {
            "cycle": cycle,
            "window_start": window_start,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            **details,
        }
        log_file = self.logs_dir / "decisions.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _log_trade_result(self, trade_result: Dict, trade_params: Dict):
        """Log trade result."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            **trade_params,
            **trade_result,
        }
        log_file = self.logs_dir / "trades.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _print_stats(self):
        """Print current stats."""
        s = self.stats
        self._log(
            f"📊 Stats: {s['total_cycles']} cycles | "
            f"{s['trades_executed']} trades ({s['tp_hits']} TP, {s['sl_hits']} SL) | "
            f"{s['trades_skipped']} skipped | "
            f"{s['debates_triggered']} debates | "
            f"PnL: {s['total_pnl']:+.5f}"
        )

    def run(self, candles: List[Dict], max_cycles: int = 0):
        """
        Run the trading loop.

        candles: full dataset
        max_cycles: 0 = unlimited, >0 = stop after N cycles
        """
        self._log("=" * 60)
        self._log("🏛️  LLM Round Table Trading System — Starting")
        self._log(f"📊 {self.pair} {self.timeframe} | Window: {self.window_size} candles")
        self._log(f"📁 Dataset: {len(candles)} candles")
        self._log("=" * 60)

        window_start = 0
        cycle = 0

        while window_start + self.window_size <= len(candles):
            cycle += 1
            if max_cycles > 0 and cycle > max_cycles:
                self._log(f"⏹️  Max cycles ({max_cycles}) reached. Stopping.")
                break

            # 1. Get window
            window = get_window(candles, window_start, self.window_size)
            self._log(f"\n{'─'*50}")
            self._log(f"🔄 Cycle {cycle} | Window [{window_start}:{window_start + self.window_size}]")
            self._log(f"   {window_summary(window)}")

            # 2. Build prompt
            prompt = build_analysis_prompt(window, self.pair, self.timeframe)

            # 3. Run 3 agents
            self._log("🤖 Running 3 agents...")
            t0 = time.time()
            responses = self.agent_runner.run_analysis(prompt)
            elapsed = time.time() - t0
            self._log(f"   Agents responded in {elapsed:.1f}s")

            # 4. Extract votes
            votes = [extract_vote(r) for r in responses]
            for i, (r, v) in enumerate(zip(responses, votes)):
                name = r.get("agent_name", r.get("agent_id", f"agent_{i}"))
                conf = r.get("confidence", "?")
                self._log(f"   {name}: {v} (confidence: {conf})")

            # 5. Check consensus
            action, reason = check_consensus(votes)
            self._log(f"⚖️  Consensus: {action} — {reason}")

            if action == "EXECUTE":
                # All 3 agree — execute immediately
                trade_params = get_trade_params_from_majority(responses)
                self._execute_trade(trade_params, candles, window_start, cycle)
                window_start += self._find_exit_candle(trade_params, candles, window_start)

            elif action == "DEBATE":
                # 2 TRADE, 1 SKIP — run debate
                self.stats["debates_triggered"] += 1
                self._log("🗣️  Starting Round Table Debate...")

                debate_result = self.debate_manager.run_debate(
                    initial_responses=responses,
                    candles=window,
                    pair=self.pair,
                    timeframe=self.timeframe,
                )

                self._log(f"   Debate result: {debate_result['action']} — {debate_result['reason']}")
                self._log(f"   Rounds: {len(debate_result['rounds'])}")
                self._log(f"   Final votes: {debate_result['final_votes']}")

                if debate_result["action"] == "EXECUTE":
                    trade_params = get_trade_params_from_majority(debate_result["final_responses"])
                    self._execute_trade(trade_params, candles, window_start, cycle)
                    window_start += self._find_exit_candle(trade_params, candles, window_start)
                else:
                    self.stats["trades_skipped"] += 1
                    self._log("❌ Skipping trade (debate failed to reach consensus)")
                    self._log_decision(cycle, window_start, "SKIP", {"reason": debate_result["reason"]})
                    window_start += self.window_size

            else:
                # Majority SKIP
                self.stats["trades_skipped"] += 1
                self._log("❌ Skipping trade")
                self._log_decision(cycle, window_start, "SKIP", {"reason": reason})
                window_start += self.window_size

            self._print_stats()

        self._log("\n" + "=" * 60)
        self._log("🏁 Trading loop finished.")
        self._print_stats()
        self._log("=" * 60)

    def _execute_trade(self, params: Dict, candles: List[Dict], window_start: int, cycle: int):
        """Execute and monitor a trade."""
        # Find the next candle after window for entry
        entry_candle = window_start + self.window_size
        if entry_candle >= len(candles):
            self._log("⚠️  No candles left to trade")
            self.stats["trades_skipped"] += 1
            return

        valid, msg = self.trade_executor.validate_trade(params)
        if not valid:
            self._log(f"⚠️  Trade invalid: {msg}")
            self.stats["trades_skipped"] += 1
            self._log_decision(cycle, window_start, "SKIP", {"reason": f"invalid: {msg}"})
            return

        self._log(
            f"⚡ EXECUTING: {params['direction']} entry={params['entry']:.5f} "
            f"SL={params['stop_loss']:.5f} TP={params['take_profit']:.5f} "
            f"R:R={params.get('risk_reward', 0):.2f}"
        )

        result = self.trade_executor.simulate_trade(params, candles, entry_candle)
        self.stats["trades_executed"] += 1
        self.stats["total_pnl"] += result["pnl"]

        if result["result"] == "TP_HIT":
            self.stats["tp_hits"] += 1
            emoji = "✅"
        elif result["result"] == "SL_HIT":
            self.stats["sl_hits"] += 1
            emoji = "❌"
        else:
            self.stats["no_hits"] += 1
            emoji = "⏳"

        self._log(
            f"{emoji} Trade result: {result['result']} | "
            f"PnL: {result['pnl']:+.5f} | "
            f"Held: {result['candles_held']} candles | "
            f"Exit candle: {result['exit_candle']}"
        )

        self._log_decision(cycle, window_start, "EXECUTE", {**params, **result})
        self._log_trade_result(result, params)

    def _find_exit_candle(self, params: Dict, candles: List[Dict], window_start: int) -> int:
        """Find how many candles to advance (to the exit candle)."""
        entry_candle = window_start + self.window_size
        result = self.trade_executor.simulate_trade(params, candles, entry_candle)
        # Advance to exit candle + 1
        advance = result["exit_candle"] - window_start + 1
        return max(advance, self.window_size)  # At least move by window size
