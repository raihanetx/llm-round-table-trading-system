# 🏛️ LLM Round Table Trading System

An automated trading system where **3 different LLM models** analyze the same chart, debate until unanimous consensus, and execute trades only when all 3 agree.

## Quick Start

```bash
# 1. Set your API key
export OPENCODE_ZEN_API_KEY="your-api-key-here"

# 2. Run
python src/main.py

# Options
python src/main.py --cycles 5          # Stop after 5 cycles
python src/main.py --dry-run           # Test config without trading
python src/main.py --dataset data/my_data.csv
```

## How It Works

```
Dataset (1000 candles) → Sliding window (50 candles) → Raw OHLCV data
    ↓
Send raw CSV to 3 LLM agents (parallel)
    ↓
Each agent votes: TRADE or SKIP (with entry/SL/TP)
    ↓
Consensus check:
  3 TRADE  → Execute immediately ⚡
  2 TRADE  → Round Table Debate 🗣️ (up to 3 rounds)
  2+ SKIP  → Skip, advance window ❌
    ↓
Execute trade → Monitor candles → TP or SL hit
    ↓
Advance window → Loop back
```

**No charts. No indicators. No images.** Just raw OHLCV data. The LLMs figure out the patterns themselves.

## Free Models (via OpenCode Zen)

| Agent | Model | Role |
|-------|-------|------|
| Alpha | `deepseek-v4-flash-free` | Momentum & Trend Analysis |
| Beta | `qwen3.6-plus-free` | Pattern & Risk Assessment |
| Gamma | `ring-2.6-1t-free` | Conservative Risk Guard |

## File Structure

```
trading-system/
├── src/
│   ├── main.py              # Entry point
│   ├── data_loader.py       # CSV reader + sliding window
│   ├── raw_prompt.py        # Raw OHLCV → LLM prompt
│   ├── gateway_client.py    # OpenCode Zen API client
│   ├── agent_runner.py      # Run 3 agents in parallel
│   ├── consensus_engine.py  # Vote counting + debate trigger
│   ├── debate_manager.py    # Multi-round debate protocol
│   ├── trade_executor.py    # Simulate trades, TP/SL monitoring
│   └── loop_controller.py   # Main trading loop
├── config/
│   ├── agents.json          # Agent model assignments
│   ├── gateway.json         # API endpoint config
│   └── trading.json         # TP/SL/risk parameters
├── prompts/
│   ├── analysis_prompt.txt  # Analysis prompt template
│   ├── debate_prompt.txt    # Debate round template
│   └── system_prompts/      # Agent personality prompts
├── data/
│   └── eurusd_5m_sample.csv # Sample EUR/USD dataset
└── logs/
    ├── trading.log          # Human-readable log
    ├── decisions.jsonl      # All decisions (JSON)
    └── trades.jsonl         # Trade results (JSON)
```

## Configuration

**`config/trading.json`:**
```json
{
  "pair": "EUR/USD",
  "timeframe": "5min",
  "window_size": 50,
  "min_risk_reward": 1.5,
  "max_debate_rounds": 3,
  "default_lot_size": 0.01
}
```

## Documentation

See [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) for complete technical documentation.

