# Build Plan — LLM Round Table Trading System

## Architecture

```
main.py
  └─ LoopController (the brain)
       ├─ DataLoader        — load CSV, sliding window
       ├─ PromptBuilder     — raw OHLCV → prompt text
       ├─ AgentRunner       — fire 3 LLM calls in parallel
       ├─ ConsensusEngine   — count votes, decide action
       ├─ DebateManager     — multi-round debate if split
       └─ TradeExecutor     — simulate trade, monitor TP/SL
```

## Files to Build

| # | File | Purpose | Lines |
|---|------|---------|-------|
| 1 | `src/data_loader.py` | Load CSV, sliding window extraction | ~40 |
| 2 | `src/raw_prompt.py` | Raw OHLCV → LLM prompt (DONE) | ~50 |
| 3 | `src/gateway_client.py` | HTTP client for OpenCode Zen API | ~80 |
| 4 | `src/agent_runner.py` | Run 3 agents in parallel (asyncio) | ~100 |
| 5 | `src/consensus_engine.py` | Parse votes, determine action | ~80 |
| 6 | `src/debate_manager.py` | Multi-round debate protocol | ~120 |
| 7 | `src/trade_executor.py` | Simulate trades, TP/SL monitoring | ~100 |
| 8 | `src/loop_controller.py` | Main infinite trading loop | ~120 |
| 9 | `src/main.py` | Entry point, CLI args | ~60 |
| 10 | `prompts/debate_prompt.txt` | Debate round template | ~30 |

## Data Flow

```
1. Load CSV → 1000 candles
2. Take window [0:50] → build raw prompt
3. Send prompt to 3 agents (parallel)
4. Each returns: {decision, confidence, reasoning, direction, entry, sl, tp, rr}
5. Consensus check:
   - 3 TRADE → execute
   - 2 TRADE + 1 SKIP → debate
   - 2+ SKIP → skip, advance window
6. Debate: up to 3 rounds, agents argue, re-vote
7. If consensus reached → execute trade
8. Monitor candles for TP/SL hit
9. Record result, advance window
10. Loop back to step 2
```

## Key Decisions

- **No images, no indicators** — raw CSV only
- **Parallel API calls** — asyncio + aiohttp
- **Simulated trading** — no real broker, just TP/SL checks against candle data
- **JSON output** — structured responses, easy to parse
- **Debate format** — each agent sees others' reasoning, presents counter-arguments
