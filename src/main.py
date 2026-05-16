#!/usr/bin/env python3
"""
LLM Round Table Trading System — Main Entry Point

This is the skeleton/entry point for the trading system.
The actual implementation will be built in subsequent phases.

Usage:
    python src/main.py
    python src/main.py --config config/gateway.json
    python src/main.py --dataset data/eurusd_5m_1000.csv
"""

import json
import os
import sys
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create logs directory if it doesn't exist
LOGS_DIR.mkdir(exist_ok=True)

# Import text chart generator (no vision/image needed)
sys.path.insert(0, str(Path(__file__).parent))
from text_chart import load_csv, generate_analysis_text, generate_llm_prompt


def load_config():
    """Load all configuration files"""
    configs = {}
    
    # Gateway config
    with open(CONFIG_DIR / "gateway.json") as f:
        configs["gateway"] = json.load(f)
    
    # Agents config
    with open(CONFIG_DIR / "agents.json") as f:
        configs["agents"] = json.load(f)
    
    # Trading config
    with open(CONFIG_DIR / "trading.json") as f:
        configs["trading"] = json.load(f)
    
    # Override API key from environment if set
    env_key = os.environ.get("OPENCODE_ZEN_API_KEY")
    if env_key:
        configs["gateway"]["api_key"] = env_key
    
    return configs


def load_prompt(prompt_name):
    """Load a prompt template"""
    with open(PROMPTS_DIR / f"{prompt_name}.txt") as f:
        return f.read()


def load_system_prompt(agent_name):
    """Load system prompt for an agent"""
    with open(PROMPTS_DIR / "system_prompts" / f"{agent_name}.txt") as f:
        return f.read()


def main():
    """
    Main entry point — runs the infinite trading loop.
    
    Flow:
    1. Load configuration
    2. Load dataset
    3. LOOP:
        a. Take window of candles → build chart
        b. Send chart to 3 LLM agents
        c. Collect decisions + reasoning
        d. Check consensus
        e. If split → debate
        f. If unanimous → execute trade
        g. Monitor TP/SL
        h. Rebuild chart from hit point
        i. Repeat
    """
    print("=" * 60)
    print("🏛️  LLM Round Table Trading System")
    print("=" * 60)
    
    # Load config
    configs = load_config()
    
    print(f"\n📊 Pair: {configs['trading']['pair']}")
    print(f"⏱️  Timeframe: {configs['trading']['timeframe']}")
    print(f"🪟  Window: {configs['trading']['window_size']} candles")
    print(f"🌐 Gateway: {configs['gateway']['base_url']}")
    print(f"\n🤖 Agents:")
    for name, agent in configs["agents"].items():
        print(f"   {name.capitalize()}: {agent['model_id']} ({agent['role']})")
    
    api_key = configs["gateway"]["api_key"]
    if api_key == "<YOUR_API_KEY>" or not api_key:
        print("\n❌ ERROR: API key not set!")
        print("   Set OPENCODE_ZEN_API_KEY environment variable")
        print("   Or update config/gateway.json")
        sys.exit(1)
    
    print(f"\n🔑 API Key: {api_key[:12]}...{api_key[-6:]}")

    # Load dataset
    dataset_path = DATA_DIR / "eurusd_5m_sample.csv"
    if not dataset_path.exists():
        print(f"\n❌ ERROR: Dataset not found at {dataset_path}")
        sys.exit(1)

    candles = load_csv(str(dataset_path))
    print(f"\n📊 Loaded {len(candles)} candles from {dataset_path.name}")

    # Generate text-based chart analysis (no image/vision needed)
    window_size = configs["trading"]["window_size"]
    window = candles[:window_size]
    print(f"🪟  Analyzing window: candles 1–{window_size}")

    # Show the analysis package
    analysis = generate_analysis_text(window)
    print("\n" + analysis)

    # Show what gets sent to each LLM agent
    print("\n" + "=" * 60)
    print("📝 LLM PROMPT PREVIEW")
    print("=" * 60)
    prompt = generate_llm_prompt(
        window,
        pair=configs["trading"]["pair"],
        timeframe=configs["trading"]["timeframe"],
    )
    print(f"\nPrompt length: {len(prompt)} chars (~{len(prompt)//4} tokens)")

    print("\n" + "=" * 60)
    print("⚠️  Text chart system loaded. Next steps:")
    print("=" * 60)
    print("""
    1. ✅ text_chart.py — Text-based chart generator (DONE)
    2. Implement gateway_client.py — OpenCode Zen API client
    3. Implement agent_runner.py — Run 3 agents in parallel
    4. Implement consensus_engine.py — Check votes, trigger debate
    5. Implement debate_manager.py — Manage debate rounds
    6. Implement trade_executor.py — Place trades, monitor TP/SL
    7. Implement loop_controller.py — Manage the infinite loop
    """)


if __name__ == "__main__":
    main()
