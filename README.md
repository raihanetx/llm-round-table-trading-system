# 🏛️ LLM Round Table Trading System

An automated trading system where **3 different LLM models** analyze the same chart, debate until unanimous consensus, and execute trades only when all 3 agree.

## Quick Start

```bash
# 1. Clone and setup
cd trading-system

# 2. Set your API key
export OPENCODE_ZEN_API_KEY="your-api-key-here"

# 3. Run
python src/main.py
```

## How It Works

```
Dataset (1000 candles) → Build chart (50 candles) → Send to 3 LLMs
    ↓
Each agent votes: TRADE or SKIP (with reasoning)
    ↓
If unanimous → Execute
If split → Round Table Debate (argue with chart evidence)
    ↓
Execute trade (Entry + TP + SL)
    ↓
Monitor candles → TP or SL hit
    ↓
Rebuild chart from that point → Loop back
```

## Free Models (via OpenCode Zen)

| Agent | Model | Cost |
|-------|-------|------|
| Alpha | `deepseek-v4-flash-free` | Free |
| Beta | `qwen3.6-plus-free` | Free |
| Gamma | `ring-2.6-1t-free` | Free |

## Documentation

See [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) for complete documentation.

## File Structure

```
trading-system/
├── docs/DOCUMENTATION.md    # Complete documentation
├── config/                  # Configuration files
├── src/                     # Source code
├── data/                    # Datasets
├── prompts/                 # LLM prompts
└── logs/                    # Trade and debate logs
```
