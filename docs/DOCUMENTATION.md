# 🏛️ LLM Round Table Trading System

## Complete Technical Documentation

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Core Concept](#2-core-concept)
3. [Architecture](#3-architecture)
4. [Dataset & Chart Generation](#4-dataset--chart-generation)
5. [OpenCode Zen Gateway Integration](#5-opencode-zen-gateway-integration)
6. [LLM Agent Configuration](#6-llm-agent-configuration)
7. [Decision Protocol](#7-decision-protocol)
8. [Debate Protocol](#8-debate-protocol)
9. [Trade Execution & Monitoring](#9-trade-execution--monitoring)
10. [Loop & Rebuild Cycle](#10-loop--rebuild-cycle)
11. [Prompt Design](#11-prompt-design)
12. [File Structure](#12-file-structure)
13. [Configuration](#13-configuration)
14. [API Reference](#14-api-reference)

---

## 1. System Overview

An automated trading system where **3 different LLM models** analyze the same trading chart, present their reasoning, debate until unanimous consensus, and execute trades only when all 3 agree.

**Key Principles:**
- No single model bias — 3 diverse AI perspectives
- No blind voting — every agent sees others' reasoning
- No lazy consensus — real debate with chart evidence
- No trade without unanimous agreement
- Continuous loop — analyze, trade, monitor, rebuild, repeat

**Gateway:** OpenCode Zen (`https://opencode.ai/zen/v1`)

---

## 2. Core Concept

```
Traditional trading:    1 human → 1 decision → trade
This system:            3 AI models → debate → unanimous → trade
```

**Why 3 models?**
- Each model has different training data, different reasoning style
- GPT might see momentum, Claude might see risk, Gemini might see patterns
- The debate forces every decision to be stress-tested
- If even 1 model disagrees, it must present evidence — and the others must counter it

**The Round Table Metaphor:**
- Like King Arthur's round table — no hierarchy, all voices equal
- Each agent presents their analysis with chart evidence
- They use retail concepts (support/resistance, patterns) AND smart money concepts (liquidity traps, stop hunts, accumulation)
- They argue until genuinely convinced — not forced

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRADING SYSTEM ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────────────────────────────┐  │
│  │   DATASET    │     │         CHART GENERATOR              │  │
│  │              │     │                                      │  │
│  │ EUR/USD 5min │────▶│  OHLC data → Candlestick chart      │  │
│  │ 1000 candles │     │  Support/Resistance lines            │  │
│  │              │     │  MA(7), MA(20) overlays              │  │
│  └──────────────┘     │  Volume bars                         │  │
│                       │  → Output: PNG image (base64)        │  │
│                       └──────────────┬───────────────────────┘  │
│                                      │                          │
│                                      ▼                          │
│                       ┌──────────────────────────────────────┐  │
│                       │      OPENCODE ZEN GATEWAY            │  │
│                       │      https://opencode.ai/zen/v1      │  │
│                       │                                      │  │
│                       │  Same chart + same prompt → 3 calls  │  │
│                       └──────┬──────────┬──────────┬─────────┘  │
│                              │          │          │            │
│                              ▼          ▼          ▼            │
│                       ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│                       │ Agent A │ │ Agent B │ │ Agent C │      │
│                       │ Alpha   │ │ Beta    │ │ Gamma   │      │
│                       │         │ │         │ │         │      │
│                       │ Model 1 │ │ Model 2 │ │ Model 3 │      │
│                       └────┬────┘ └────┬────┘ └────┬────┘      │
│                            │           │           │            │
│                            ▼           ▼           ▼            │
│                       ┌──────────────────────────────────────┐  │
│                       │         CONSENSUS ENGINE             │  │
│                       │                                      │  │
│                       │  Collect 3 decisions + reasoning     │  │
│                       │  Check: Unanimous? Majority? Split?  │  │
│                       │                                      │  │
│                       │  If split → DEBATE PROTOCOL          │  │
│                       │  If unanimous → EXECUTE              │  │
│                       └──────────────┬───────────────────────┘  │
│                                      │                          │
│                              ┌───────┴───────┐                  │
│                              ▼               ▼                  │
│                    ┌──────────────┐  ┌──────────────────┐       │
│                    │   DEBATE     │  │  TRADE EXECUTOR  │       │
│                    │              │  │                  │       │
│                    │ Round table  │  │ Entry + TP + SL  │       │
│                    │ Both sides   │  │ Monitor candles  │       │
│                    │ argue with   │  │ TP/SL hit?       │       │
│                    │ evidence     │  │ → Rebuild chart  │       │
│                    │ Until 3/3    │  │ → Loop back      │       │
│                    └──────────────┘  └──────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Dataset & Chart Generation

### 4.1 Dataset

```
Asset:       EUR/USD
Timeframe:   5 minutes
Total:       1000 candles per dataset
Format:      CSV with columns: timestamp, open, high, low, close, volume
```

### 4.2 Sliding Window

```
Initial:     Candle 1–50     → build chart → send to LLMs
Next trade:  Candle 55–105   → rebuild after TP/SL hit
Next trade:  Candle 108–158  → rebuild again
...continues until dataset exhausted
```

**Window size:** 50 candles (configurable)

### 4.3 Chart Generation

The chart must look like TradingView — clean, professional, information-rich.

**Chart Elements:**
- Candlestick bodies (green for bullish, red for bearish)
- Wicks/shadows
- MA(7) line — fast moving average (yellow)
- MA(20) line — slow moving average (purple)
- Support/Resistance zones (auto-detected)
- Volume bars at bottom
- Price scale on Y-axis
- Time labels on X-axis

**Output:** PNG image, base64 encoded for API transmission

**Library Options:**
- `mplfinance` (matplotlib-based, Python)
- `lightweight-charts` (JavaScript, TradingView style)
- `plotly` (interactive, can export static PNG)
- Custom SVG/Canvas rendering

### 4.4 OHLC Data Format

```csv
timestamp,open,high,low,close,volume
2024-01-15 08:00,1.0850,1.0865,1.0840,1.0860,1250
2024-01-15 08:05,1.0860,1.0870,1.0855,1.0868,980
...
```

---

## 5. OpenCode Zen Gateway Integration

### 5.1 What is OpenCode Zen?

OpenCode Zen is an AI gateway that provides access to multiple LLM models through a unified API. It's maintained by the OpenCode team with tested and verified model configurations.

**Base URL:** `https://opencode.ai/zen/v1`

### 5.2 Authentication

```
Header:  Authorization: Bearer <API_KEY>
```

API keys are obtained from: https://opencode.ai/auth

### 5.3 Available Models

#### Free Models (7)

| Model ID | Name | Best For |
|----------|------|----------|
| `big-pickle` | Big Pickle | General analysis |
| `deepseek-v4-flash-free` | DeepSeek V4 Flash Free | Fast reasoning |
| `qwen3.6-plus-free` | Qwen 3.6 Plus Free | Strong analysis |
| `minimax-m2.5-free` | MiniMax M2.5 Free | General purpose |
| `ring-2.6-1t-free` | Ring 2.6 1T Free | 1T params, diverse perspective |
| `trinity-large-preview-free` | Trinity Large Preview Free | Large context |
| `nemotron-3-super-free` | Nemotron 3 Super Free | NVIDIA model |

#### Paid Models (35)

| Category | Models | Price (per 1M tokens, input/output) |
|----------|--------|-------------------------------------|
| **Claude** | opus-4-7, opus-4-6, opus-4-5, opus-4-1, sonnet-4-6, sonnet-4-5, sonnet-4, haiku-4-5 | $1–$15 / $5–$75 |
| **GPT** | 5.5, 5.5-pro, 5.4, 5.4-pro, 5.4-mini, 5.4-nano, 5.3-codex-spark, 5.3-codex, 5.2, 5.2-codex, 5.1, 5.1-codex-max, 5.1-codex, 5.1-codex-mini, 5, 5-codex, 5-nano | $0.05–$30 / $0.40–$180 |
| **Gemini** | 3.1-pro, 3-flash | $0.50–$2.00 / $3.00–$12.00 |
| **GLM** | 5.1, 5 | $1.00–$1.40 / $3.20–$4.40 |
| **MiniMax** | M2.7, M2.5 | $0.30 / $1.20 |
| **Kimi** | K2.6, K2.5 | $0.60–$0.95 / $3.00–$4.00 |
| **Qwen** | 3.6-plus, 3.5-plus | $0.20–$0.50 / $1.20–$3.00 |

### 5.4 API Endpoints

Different model families use different endpoints:

| Provider | Endpoint | Models |
|----------|----------|--------|
| OpenAI | `/zen/v1/responses` | GPT series |
| Anthropic | `/zen/v1/messages` | Claude series |
| Google | `/zen/v1/models/{model_id}` | Gemini series |
| Others | `/zen/v1/chat/completions` | Qwen, MiniMax, DeepSeek, GLM, Kimi, Ring, Nemotron, Big Pickle |

### 5.5 API Call Format

**For most models (OpenAI-compatible):**

```json
POST https://opencode.ai/zen/v1/chat/completions
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "model": "deepseek-v4-flash-free",
  "messages": [
    {
      "role": "system",
      "content": "You are a professional trading analyst..."
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Analyze this trading chart and give your decision..."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/png;base64,<BASE64_CHART_IMAGE>"
          }
        }
      ]
    }
  ],
  "max_tokens": 1000,
  "temperature": 0.3
}
```

### 5.6 Vision Support

For chart image analysis, the model must support image input. Check model capabilities:

| Model | Vision (Image Input) | Notes |
|-------|---------------------|-------|
| GPT-5.x series | ✅ Yes | All GPT models support vision |
| Claude series | ✅ Yes | All Claude models support vision |
| Gemini series | ✅ Yes | All Gemini models support vision |
| DeepSeek V4 Flash | ⚠️ Check | May or may not support vision |
| Qwen 3.6 Plus | ⚠️ Check | Likely supports vision |
| MiniMax M2.5 | ⚠️ Check | Verify documentation |
| Ring 2.6 1T | ⚠️ Check | Verify documentation |
| Big Pickle | ⚠️ Check | Verify documentation |
| Nemotron 3 | ⚠️ Check | Verify documentation |

**If free models don't support vision:**
- Use paid models with vision (GPT-5.4-nano is cheapest at $0.20/$1.25 per 1M tokens)
- Or convert chart to text description (OHLC data as structured text)

---

## 6. LLM Agent Configuration

### 6.1 Three-Agent Setup

```
Agent Alpha:   First model  (e.g., deepseek-v4-flash-free)
Agent Beta:    Second model (e.g., qwen3.6-plus-free)
Agent Gamma:   Third model  (e.g., ring-2.6-1t-free)
```

### 6.2 Agent Roles (Soft — Not Hardcoded)

Each agent naturally develops a tendency based on its model:
- **Alpha** — May lean toward momentum/trend analysis
- **Beta** — May focus on patterns and risk
- **Gamma** — May be more conservative/contrarian

These are not enforced — the models' inherent reasoning styles create diversity.

### 6.3 Agent Configuration File

```json
{
  "agents": {
    "alpha": {
      "model_id": "deepseek-v4-flash-free",
      "name": "Agent Alpha",
      "role": "Momentum & Trend Analysis",
      "endpoint": "/chat/completions"
    },
    "beta": {
      "model_id": "qwen3.6-plus-free",
      "name": "Agent Beta",
      "role": "Pattern & Risk Assessment",
      "endpoint": "/chat/completions"
    },
    "gamma": {
      "model_id": "ring-2.6-1t-free",
      "name": "Agent Gamma",
      "role": "Conservative Risk Guard",
      "endpoint": "/chat/completions"
    }
  },
  "gateway": {
    "base_url": "https://opencode.ai/zen/v1",
    "api_key": "<YOUR_API_KEY>"
  }
}
```

---

## 7. Decision Protocol

### 7.1 Voting

Each agent returns:
1. **Decision:** `TRADE` or `SKIP`
2. **Reasoning:** Detailed analysis with chart evidence
3. **Confidence:** 0–100%
4. **Entry/TP/SL:** If TRADE, suggested levels

### 7.2 Consensus Rules

```
┌─────────────────────────────────────────────────────────┐
│                  CONSENSUS MATRIX                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Alpha    Beta    Gamma    →  Action                    │
│  ─────    ─────   ─────       ──────                    │
│  SKIP     SKIP    SKIP     →  SKIP ❌ (no debate)      │
│  SKIP     SKIP    TRADE    →  SKIP ❌ (no debate)      │
│  SKIP     TRADE   SKIP     →  SKIP ❌ (no debate)      │
│  TRADE    SKIP    SKIP     →  SKIP ❌ (no debate)      │
│  ─────    ─────   ─────       ──────                    │
│  TRADE    TRADE   SKIP     →  DEBATE 🗣️                │
│  TRADE    SKIP    TRADE    →  DEBATE 🗣️                │
│  SKIP     TRADE   TRADE    →  DEBATE 🗣️                │
│  ─────    ─────   ─────       ──────                    │
│  TRADE    TRADE   TRADE    →  EXECUTE ⚡ (no debate)    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Key Rules:**
- **Skip-majority (2+ skip):** Skip immediately. No debate needed.
- **Trade-majority but not unanimous (2 trade, 1 skip):** Debate required.
- **Unanimous trade (3/3):** Execute immediately.
- **Debate result:** If after debate all 3 agree → execute. If still split → skip (safety default).

---

## 8. Debate Protocol

### 8.1 When Debate Triggers

Debate only happens when: **2 agents say TRADE, 1 says SKIP**

The 2 must convince the 1, OR the 1 must convince the 2.

### 8.2 Debate Structure

```
Round 1:
  MAJORITY (2 agents) present their case:
    - Why they chose TRADE
    - Chart evidence (specific candles, patterns)
    - Concepts used (retail + smart money)
  
  MINORITY (1 agent) presents counter-case:
    - Why they chose SKIP
    - Chart evidence contradicting the majority
    - Risk factors they see

Round 2:
  MAJORITY responds to minority's points:
    - Address specific concerns
    - Provide additional evidence
  
  MINORITY responds to majority's points:
    - Challenge their evidence
    - Present new concerns

Round 3:
  All agents re-evaluate:
    - Have I been convinced by the other side?
    - Do I change my vote?
    - Final decision: TRADE or SKIP
```

### 8.3 Debate Rules

1. **Evidence required:** No "I just feel it" — must cite specific candles, patterns, levels
2. **Both sides argue:** Majority doesn't just say "yes yes" — they must defend. Minority doesn't just fold — they must present real counter-evidence.
3. **Max 3 rounds:** After 3 rounds, forced re-vote. If still split → skip (safety default).
4. **Concepts allowed:**
   - Retail: Support/Resistance, MA crossovers, flags, head & shoulders, double tops, Fibonacci
   - Smart Money: Liquidity traps, stop hunts, order blocks, fair value gaps, accumulation/distribution
   - Indicators: RSI divergence, MACD, volume profile, ATR

### 8.4 Debate Output Format

```json
{
  "round": 1,
  "majority_arguments": [
    {
      "agent": "alpha",
      "argument": "Candle 45-48 show strong bullish momentum. Price broke above resistance at 1.0850...",
      "evidence": ["candle_45_bullish_engulfing", "breakout_above_resistance", "volume_surge"],
      "concepts": ["higher_highs_higher_lows", "golden_cross", "volume_confirmation"]
    },
    {
      "agent": "beta",
      "argument": "Bull flag pattern from candle 30-45. Breakout at candle 48 confirms...",
      "evidence": ["bull_flag_pattern", "fibonacci_38_hold"],
      "concepts": ["bull_flag", "fibonacci_retracement"]
    }
  ],
  "minority_arguments": [
    {
      "agent": "gamma",
      "argument": "Candle 42 and 44 show rejection wicks at same level. This is a liquidity trap...",
      "evidence": ["rejection_wicks", "double_top_formation"],
      "concepts": ["liquidity_trap", "stop_hunt", "fake_breakout"]
    }
  ],
  "vote_changes": [],
  "consensus": false
}
```

---

## 9. Trade Execution & Monitoring

### 9.1 Trade Parameters

When consensus is reached, the system determines:

```json
{
  "action": "BUY" | "SELL",
  "entry_price": 1.0865,
  "stop_loss": 1.0840,
  "take_profit": 1.0895,
  "risk_reward_ratio": 2.3,
  "lot_size": 0.01,
  "confidence": 85,
  "consensus_agents": ["alpha", "beta", "gamma"],
  "debate_rounds": 2
}
```

### 9.2 TP/SL Calculation

- **TP (Take Profit):** Based on agent consensus — typically nearest resistance (BUY) or support (SELL)
- **SL (Stop Loss):** Based on recent swing low (BUY) or swing high (SELL)
- **R:R Ratio:** Minimum 1.5:1 (configurable)

### 9.3 Monitoring

After trade execution, the system monitors each new candle:

```
Trade placed at candle 51
  → Monitor candle 52: No hit
  → Monitor candle 53: No hit
  → Monitor candle 54: No hit
  → Monitor candle 55: TP HIT ✅ → Trade closed in profit
```

**Monitoring Logic:**
```
For each new candle:
  if high >= take_profit:
    result = "TP_HIT"
    profit = take_profit - entry_price
  elif low <= stop_loss:
    result = "SL_HIT"
    loss = entry_price - stop_loss
  else:
    continue monitoring next candle
```

---

## 10. Loop & Rebuild Cycle

### 10.1 The Infinite Loop

```
START
  │
  ▼
Load dataset (1000 candles)
  │
  ▼
Take window (candles 1–50) → Build chart
  │
  ▼
Send to 3 LLMs → Get decisions + reasoning
  │
  ▼
Check consensus ──────────────────────────┐
  │                                        │
  ├─ All skip → SKIP → Move window forward │
  ├─ All trade → EXECUTE                   │
  ├─ Split → DEBATE → Re-check             │
  │                                        │
  ▼                                        │
Execute trade (Entry + TP + SL)            │
  │                                        │
  ▼                                        │
Monitor candles for TP/SL hit              │
  │                                        │
  ▼                                        │
TP or SL hit                                │
  │                                        │
  ▼                                        │
Rebuild chart from hit candle              │
  │                                        │
  └────────────────────────────────────────┘
  (Loop continues until dataset exhausted)
```

### 10.2 Window Advancement

```
Trade 1: Candles 1–50      → TP hit at candle 55
Trade 2: Candles 55–105    → SL hit at candle 89
Trade 3: Candles 89–139    → TP hit at candle 120
Trade 4: Candles 120–170   → Skip (majority said skip)
Trade 5: Candles 170–220   → TP hit at candle 198
...continues...
```

### 10.3 Skip Handling

When the decision is SKIP:
- No trade is placed
- The window moves forward by the window size (50 candles)
- A new chart is built from the new position
- The cycle continues

---

## 11. Prompt Design

### 11.1 Initial Analysis Prompt (Sent to All 3 Agents)

```
You are a professional forex trading analyst. Analyze this EUR/USD 5-minute chart.

CHART: [attached image]

TASK:
1. Analyze the price action, patterns, and trends you see
2. Identify key support and resistance levels
3. Note any significant candlestick patterns
4. Consider both retail and smart money concepts
5. Make a decision: TRADE or SKIP

RESPOND IN THIS EXACT JSON FORMAT:
{
  "decision": "TRADE" or "SKIP",
  "confidence": 0-100,
  "reasoning": "Your detailed analysis with specific candle references...",
  "key_levels": {
    "support": [price levels],
    "resistance": [price levels]
  },
  "patterns_seen": ["pattern1", "pattern2"],
  "concepts_used": ["concept1", "concept2"],
  "if_trade": {
    "direction": "BUY" or "SELL",
    "entry": price,
    "stop_loss": price,
    "take_profit": price,
    "risk_reward": ratio
  }
}

Be specific. Reference exact candles. Use both retail and smart money analysis.
```

### 11.2 Debate Prompt (Sent to Each Agent During Debate)

```
You are in a ROUND TABLE DEBATE with 2 other trading analysts.

YOUR CURRENT VOTE: [TRADE/SKIP]

HERE IS WHAT THE OTHER AGENTS SAID:

--- AGENT [A/B/C] (VOTED: [TRADE/SKIP]) ---
[Their reasoning]

--- AGENT [A/B/C] (VOTED: [TRADE/SKIP]) ---
[Their reasoning]

YOUR TASK:
1. Present your counter-arguments with specific chart evidence
2. Address their points directly — don't ignore them
3. Use chart patterns, candlestick analysis, and smart money concepts
4. After presenting your argument, re-evaluate: Do you CHANGE your vote?

RESPOND IN THIS EXACT JSON FORMAT:
{
  "counter_arguments": "Your detailed counter-argument...",
  "evidence": ["specific candle references", "patterns", "levels"],
  "concepts_used": ["concept1", "concept2"],
  "addressed_opponent_points": {
    "agent_X": "How you counter their specific point...",
    "agent_Y": "How you counter their specific point..."
  },
  "vote_change": true/false,
  "new_vote": "TRADE" or "SKIP" (only if vote_change is true),
  "reason_for_change": "Why you changed your mind (if applicable)"
}
```

### 11.3 System Prompt (Agent Personality)

```
You are {agent_name}, a {agent_role} specialist in forex trading.

Your analysis style:
- Focus on {role_specific_focus}
- You are {personality_trait}
- You always back your decisions with specific chart evidence
- You reference exact candle numbers and price levels
- You use both retail concepts (S/R, patterns, indicators) AND smart money concepts (liquidity, order blocks, FVG)

When debating:
- You don't just agree to be agreeable — you argue your position with evidence
- You acknowledge good points from others but challenge weak ones
- You change your vote ONLY when genuinely convinced by evidence
- You present counter-arguments clearly and respectfully
```

---

## 12. File Structure

```
trading-system/
├── docs/
│   └── DOCUMENTATION.md          # This file
├── config/
│   ├── agents.json               # Agent model assignments
│   ├── gateway.json              # OpenCode Zen API config
│   └── trading.json              # TP/SL/risk parameters
├── src/
│   ├── main.py                   # Entry point — runs the loop
│   ├── chart_generator.py        # OHLC → TradingView-style chart
│   ├── gateway_client.py         # OpenCode Zen API client
│   ├── agent_runner.py           # Runs 3 agents in parallel
│   ├── consensus_engine.py       # Checks votes, triggers debate
│   ├── debate_manager.py         # Manages debate rounds
│   ├── trade_executor.py         # Places trades, monitors TP/SL
│   └── loop_controller.py        # Manages the infinite loop
├── data/
│   ├── eurusd_5m_1000.csv        # Sample dataset
│   └── charts/                   # Generated chart images
├── prompts/
│   ├── analysis_prompt.txt       # Initial analysis prompt
│   ├── debate_prompt.txt         # Debate round prompt
│   └── system_prompts/
│       ├── alpha.txt             # Alpha agent personality
│       ├── beta.txt              # Beta agent personality
│       └── gamma.txt             # Gamma agent personality
├── logs/
│   ├── trades.log                # Trade history
│   ├── debates.log               # Debate transcripts
│   └── decisions.log             # All decisions
└── README.md
```

---

## 13. Configuration

### 13.1 Gateway Config (`config/gateway.json`)

```json
{
  "provider": "opencode_zen",
  "base_url": "https://opencode.ai/zen/v1",
  "api_key": "<YOUR_API_KEY>",
  "timeout_seconds": 30,
  "max_retries": 3,
  "retry_delay_seconds": 2
}
```

### 13.2 Trading Config (`config/trading.json`)

```json
{
  "pair": "EUR/USD",
  "timeframe": "5min",
  "window_size": 50,
  "min_risk_reward": 1.5,
  "max_debate_rounds": 3,
  "default_lot_size": 0.01,
  "max_sl_pips": 50,
  "min_tp_pips": 30,
  "consensus_threshold": {
    "skip": 2,
    "trade_unanimous": 3,
    "debate_required": "2_trade_1_skip"
  }
}
```

### 13.3 Agent Config (`config/agents.json`)

```json
{
  "alpha": {
    "model_id": "deepseek-v4-flash-free",
    "endpoint": "/chat/completions",
    "name": "Agent Alpha",
    "role": "Momentum & Trend Analysis",
    "temperature": 0.3,
    "max_tokens": 1000
  },
  "beta": {
    "model_id": "qwen3.6-plus-free",
    "endpoint": "/chat/completions",
    "name": "Agent Beta",
    "role": "Pattern & Risk Assessment",
    "temperature": 0.3,
    "max_tokens": 1000
  },
  "gamma": {
    "model_id": "ring-2.6-1t-free",
    "endpoint": "/chat/completions",
    "name": "Agent Gamma",
    "role": "Conservative Risk Guard",
    "temperature": 0.3,
    "max_tokens": 1000
  }
}
```

---

## 14. API Reference

### 14.1 OpenCode Zen Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/zen/v1/models` | List all available models |
| POST | `/zen/v1/chat/completions` | Chat completion (most models) |
| POST | `/zen/v1/responses` | OpenAI GPT models |
| POST | `/zen/v1/messages` | Anthropic Claude models |
| POST | `/zen/v1/models/{id}` | Google Gemini models |

### 14.2 Request Headers

```
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

### 14.3 Chat Completion Request

```json
{
  "model": "model-id",
  "messages": [
    {"role": "system", "content": "system prompt"},
    {"role": "user", "content": [
      {"type": "text", "text": "prompt text"},
      {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
    ]}
  ],
  "max_tokens": 1000,
  "temperature": 0.3
}
```

### 14.4 Response Format

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "model-id",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "response text"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 200,
    "total_tokens": 300
  }
}
```

---

## Quick Start Checklist

- [ ] Get OpenCode Zen API key from https://opencode.ai/auth
- [ ] Test API key with: `curl -X POST https://opencode.ai/zen/v1/chat/completions -H "Authorization: Bearer <KEY>" -H "Content-Type: application/json" -d '{"model":"big-pickle","messages":[{"role":"user","content":"Say OK"}],"max_tokens":10}'`
- [ ] Prepare EUR/USD 5min dataset (CSV format)
- [ ] Install chart generation library (`mplfinance` or similar)
- [ ] Configure agents in `config/agents.json`
- [ ] Run the system: `python src/main.py`
- [ ] Monitor logs in `logs/` directory

---

*Documentation version: 1.0*
*Last updated: 2026-05-16*
*System: LLM Round Table Trading System*
*Gateway: OpenCode Zen*
