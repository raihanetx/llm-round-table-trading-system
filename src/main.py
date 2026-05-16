#!/usr/bin/env python3
"""
LLM Round Table Trading System — Main Entry Point

Usage:
    python src/main.py
    python src/main.py --dataset data/eurusd_5m_sample.csv
    python src/main.py --cycles 5
    python src/main.py --dry-run
"""

import argparse
import json
import os
import sys
from pathlib import Path

from data_loader import load_csv
from gateway_client import GatewayClient
from loop_controller import LoopController

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"


def load_configs() -> dict:
    """Load all config files."""
    configs = {}

    with open(CONFIG_DIR / "gateway.json") as f:
        configs["gateway"] = json.load(f)

    with open(CONFIG_DIR / "agents.json") as f:
        configs["agents"] = json.load(f)

    with open(CONFIG_DIR / "trading.json") as f:
        configs["trading"] = json.load(f)

    # API key from env or config
    api_key = os.environ.get("OPENCODE_ZEN_API_KEY", configs["gateway"].get("api_key", ""))
    if not api_key or api_key == "<YOUR_API_KEY>":
        print("❌ ERROR: Set OPENCODE_ZEN_API_KEY env var or update config/gateway.json")
        sys.exit(1)

    # Create gateway client
    configs["gateway_client"] = GatewayClient(
        base_url=configs["gateway"]["base_url"],
        api_key=api_key,
        timeout=configs["gateway"].get("timeout_seconds", 30),
        max_retries=configs["gateway"].get("max_retries", 3),
    )

    return configs


def main():
    parser = argparse.ArgumentParser(description="LLM Round Table Trading System")
    parser.add_argument("--dataset", type=str, default=None, help="Path to CSV dataset")
    parser.add_argument("--cycles", type=int, default=0, help="Max cycles (0=unlimited)")
    parser.add_argument("--dry-run", action="store_true", help="Load config and data, don't trade")
    args = parser.parse_args()

    print("=" * 60)
    print("🏛️  LLM Round Table Trading System")
    print("=" * 60)

    # Load config
    configs = load_configs()
    print(f"📊 Pair: {configs['trading']['pair']}")
    print(f"⏱️  Timeframe: {configs['trading']['timeframe']}")
    print(f"🪟  Window: {configs['trading']['window_size']} candles")
    print(f"🌐 Gateway: {configs['gateway']['base_url']}")

    for name, agent in configs["agents"].items():
        print(f"🤖 {name.capitalize()}: {agent['model_id']} ({agent['role']})")

    # Load dataset
    dataset_path = args.dataset or str(DATA_DIR / "eurusd_5m_sample.csv")
    if not Path(dataset_path).exists():
        print(f"\n❌ Dataset not found: {dataset_path}")
        sys.exit(1)

    candles = load_csv(dataset_path)
    print(f"\n📁 Dataset: {len(candles)} candles from {dataset_path}")

    if args.dry_run:
        print("\n🔍 Dry run — config and data loaded successfully.")
        print(f"   Would process {len(candles) // configs['trading']['window_size']} windows")
        return

    # Run the trading loop
    print()
    loop = LoopController(configs, LOGS_DIR)
    loop.run(candles, max_cycles=args.cycles)


if __name__ == "__main__":
    main()
