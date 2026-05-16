#!/usr/bin/env python3
"""
Text-Based Chart Generator for LLM Round Table Trading System

Generates ASCII candlestick charts from OHLC data — no image/vision needed.
LLMs read the chart as structured text with visual price action.

Output includes:
- ASCII candlestick chart with wicks and bodies
- MA(7) and MA(20) overlay markers
- Auto-detected support/resistance levels
- Volume bars
- Pre-computed technical indicators
"""

import csv
import statistics
from pathlib import Path
from typing import List, Dict, Tuple, Optional


def load_csv(filepath: str) -> List[Dict]:
    """Load OHLC data from CSV file."""
    candles = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            candles.append({
                "timestamp": row["timestamp"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
            })
    return candles


def compute_ma(candles: List[Dict], period: int, key: str = "close") -> List[Optional[float]]:
    """Compute moving average for each candle."""
    ma = []
    for i in range(len(candles)):
        if i < period - 1:
            ma.append(None)
        else:
            values = [candles[j][key] for j in range(i - period + 1, i + 1)]
            ma.append(sum(values) / len(values))
    return ma


def compute_rsi(candles: List[Dict], period: int = 14) -> List[Optional[float]]:
    """Compute RSI (Relative Strength Index)."""
    if len(candles) < period + 1:
        return [None] * len(candles)

    rsi_values = [None] * period
    gains = []
    losses = []

    for i in range(1, period + 1):
        delta = candles[i]["close"] - candles[i - 1]["close"]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        rsi_values.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi_values.append(100 - (100 / (1 + rs)))

    for i in range(period + 1, len(candles)):
        delta = candles[i]["close"] - candles[i - 1]["close"]
        gain = max(delta, 0)
        loss = max(-delta, 0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - (100 / (1 + rs)))

    return rsi_values


def compute_atr(candles: List[Dict], period: int = 14) -> List[Optional[float]]:
    """Compute ATR (Average True Range)."""
    if len(candles) < 2:
        return [None] * len(candles)

    tr_list = [None]
    for i in range(1, len(candles)):
        tr = max(
            candles[i]["high"] - candles[i]["low"],
            abs(candles[i]["high"] - candles[i - 1]["close"]),
            abs(candles[i]["low"] - candles[i - 1]["close"]),
        )
        tr_list.append(tr)

    atr_values = [None] * period
    first_trs = [t for t in tr_list[1:period + 1] if t is not None]
    if not first_trs:
        return [None] * len(candles)

    atr = sum(first_trs) / len(first_trs)
    atr_values.append(atr)

    for i in range(period + 1, len(candles)):
        if tr_list[i] is not None:
            atr = (atr * (period - 1) + tr_list[i]) / period
        atr_values.append(atr)

    return atr_values


def detect_support_resistance(candles: List[Dict], lookback: int = 5) -> Tuple[List[float], List[float]]:
    """Auto-detect support and resistance levels using swing highs/lows."""
    supports = []
    resistances = []

    for i in range(lookback, len(candles) - lookback):
        # Swing low → support
        is_swing_low = True
        for j in range(i - lookback, i + lookback + 1):
            if j == i:
                continue
            if j < len(candles) and candles[j]["low"] < candles[i]["low"]:
                is_swing_low = False
                break
        if is_swing_low:
            supports.append(candles[i]["low"])

        # Swing high → resistance
        is_swing_high = True
        for j in range(i - lookback, i + lookback + 1):
            if j == i:
                continue
            if j < len(candles) and candles[j]["high"] > candles[i]["high"]:
                is_swing_high = False
                break
        if is_swing_high:
            resistances.append(candles[i]["high"])

    # Cluster nearby levels (within 0.0005)
    supports = _cluster_levels(supports, tolerance=0.0005)
    resistances = _cluster_levels(resistances, tolerance=0.0005)

    return supports, resistances


def _cluster_levels(levels: List[float], tolerance: float = 0.0005) -> List[float]:
    """Cluster nearby price levels into single zones."""
    if not levels:
        return []

    levels = sorted(levels)
    clustered = []
    cluster = [levels[0]]

    for i in range(1, len(levels)):
        if levels[i] - levels[i - 1] <= tolerance:
            cluster.append(levels[i])
        else:
            clustered.append(sum(cluster) / len(cluster))
            cluster = [levels[i]]
    clustered.append(sum(cluster) / len(cluster))

    return clustered


def detect_patterns(candles: List[Dict]) -> List[str]:
    """Detect basic candlestick patterns from OHLC data."""
    patterns = []

    for i in range(len(candles)):
        c = candles[i]
        body = abs(c["close"] - c["open"])
        upper_wick = c["high"] - max(c["close"], c["open"])
        lower_wick = min(c["close"], c["open"]) - c["low"]
        total_range = c["high"] - c["low"]

        if total_range == 0:
            continue

        # Doji — tiny body
        if body / total_range < 0.1:
            patterns.append(f"Candle {i + 1}: Doji (indecision)")

        # Hammer — small body, long lower wick
        if lower_wick > body * 2 and upper_wick < body * 0.5:
            patterns.append(f"Candle {i + 1}: Hammer (bullish reversal)")

        # Shooting star — small body, long upper wick
        if upper_wick > body * 2 and lower_wick < body * 0.5:
            patterns.append(f"Candle {i + 1}: Shooting Star (bearish reversal)")

        # Engulfing (needs previous candle)
        if i > 0:
            prev = candles[i - 1]
            prev_body = abs(prev["close"] - prev["open"])
            # Bullish engulfing
            if prev["close"] < prev["open"] and c["close"] > c["open"]:
                if c["close"] > prev["open"] and c["open"] < prev["close"]:
                    patterns.append(f"Candle {i + 1}: Bullish Engulfing")
            # Bearish engulfing
            if prev["close"] > prev["open"] and c["close"] < c["open"]:
                if c["close"] < prev["open"] and c["open"] > prev["close"]:
                    patterns.append(f"Candle {i + 1}: Bearish Engulfing")

    return patterns


def generate_ascii_chart(
    candles: List[Dict],
    width: int = 60,
    height: int = 20,
    show_ma7: bool = True,
    show_ma20: bool = True,
    show_sr: bool = True,
    show_volume: bool = True,
) -> str:
    """
    Generate an ASCII candlestick chart from OHLC data.

    Returns a multi-line string with:
    - Price scale on Y-axis
    - Candlestick bodies + wicks
    - MA(7) and MA(20) lines marked
    - Support/Resistance zones marked
    - Volume bars at bottom
    """
    if not candles:
        return "No data"

    # Price range
    all_highs = [c["high"] for c in candles]
    all_lows = [c["low"] for c in candles]
    price_max = max(all_highs)
    price_min = min(all_lows)
    price_range = price_max - price_min
    if price_range == 0:
        price_range = 0.001

    # Price step per row
    price_step = price_range / height

    # Compute indicators
    ma7 = compute_ma(candles, 7) if show_ma7 else [None] * len(candles)
    ma20 = compute_ma(candles, 20) if show_ma20 else [None] * len(candles)
    supports, resistances = detect_support_resistance(candles) if show_sr else ([], [])

    # Max volume for scaling
    max_vol = max(c["volume"] for c in candles) if candles else 1

    # Build the chart grid
    # Each candle takes: 1 char for wick + some spacing
    candle_width = max(1, width // len(candles))

    # Grid: height rows × width columns
    grid = [[" " for _ in range(width)] for _ in range(height)]

    # Map price to row (0 = top = highest price)
    def price_to_row(price: float) -> int:
        row = int((price_max - price) / price_step)
        return max(0, min(height - 1, row))

    # Place candles
    for i, c in enumerate(candles):
        col = int(i * width / len(candles))
        if col >= width:
            col = width - 1

        is_bullish = c["close"] >= c["open"]
        body_top = price_to_row(max(c["close"], c["open"]))
        body_bottom = price_to_row(min(c["close"], c["open"]))
        wick_top = price_to_row(c["high"])
        wick_bottom = price_to_row(c["low"])

        # Draw upper wick
        for r in range(wick_top, body_top):
            grid[r][col] = "│"

        # Draw body
        for r in range(body_top, body_bottom + 1):
            if is_bullish:
                grid[r][col] = "█"  # Filled = bullish
            else:
                grid[r][col] = "░"  # Shaded = bearish

        # Draw lower wick
        for r in range(body_bottom + 1, wick_bottom + 1):
            grid[r][col] = "│"

    # Overlay MA(7) markers
    if show_ma7:
        for i, val in enumerate(ma7):
            if val is not None:
                col = int(i * width / len(candles))
                if col >= width:
                    col = width - 1
                row = price_to_row(val)
                if grid[row][col] == " ":
                    grid[row][col] = "·"
                # If already occupied, leave candle visible

    # Overlay MA(20) markers
    if show_ma20:
        for i, val in enumerate(ma20):
            if val is not None:
                col = int(i * width / len(candles))
                if col >= width:
                    col = width - 1
                row = price_to_row(val)
                if grid[row][col] == " ":
                    grid[row][col] = "◦"

    # Mark support levels with S
    for s_level in supports:
        row = price_to_row(s_level)
        for col in range(width):
            if grid[row][col] == " ":
                grid[row][col] = "─"

    # Mark resistance levels with R
    for r_level in resistances:
        row = price_to_row(r_level)
        for col in range(width):
            if grid[row][col] == " ":
                grid[row][col] = "═"

    # Build output
    lines = []
    lines.append("┌" + "─" * (width + 12) + "┐")
    lines.append("│  PRICE CHART (ASCII Candlestick)" + " " * (width + 12 - 34) + "│")
    lines.append("├" + "─" * (width + 12) + "┤")

    # Legend
    lines.append("│  Legend: █=Bullish  ░=Bearish  │=Wick  ·=MA(7)  ◦=MA(20)  ─=Support  ═=Resistance")
    lines.append("├" + "─" * (width + 12) + "┤")

    # Render grid with price labels
    for r in range(height):
        price_label = price_max - r * price_step
        row_str = "".join(grid[r])
        lines.append(f"│ {price_label:8.5f} │{row_str}│")

    # Volume bars below chart
    if show_volume:
        lines.append("├" + "─" * (width + 12) + "┤")
        vol_height = 5
        vol_grid = [[" " for _ in range(width)] for _ in range(vol_height)]

        for i, c in enumerate(candles):
            col = int(i * width / len(candles))
            if col >= width:
                col = width - 1
            vol_rows = int((c["volume"] / max_vol) * vol_height)
            for r in range(vol_height - 1, vol_height - 1 - vol_rows, -1):
                if r >= 0:
                    is_bullish = c["close"] >= c["open"]
                    vol_grid[r][col] = "█" if is_bullish else "░"

        for r in range(vol_height):
            row_str = "".join(vol_grid[r])
            lines.append(f"│   {'VOL':>6s} │{row_str}│")

    lines.append("└" + "─" * (width + 12) + "┘")

    return "\n".join(lines)


def generate_analysis_text(candles: List[Dict]) -> str:
    """
    Generate a complete text-based chart analysis package for LLMs.

    Combines:
    1. ASCII candlestick chart
    2. OHLC data table
    3. Pre-computed indicators
    4. Detected patterns
    5. Support/Resistance levels
    """
    if not candles:
        return "No data available."

    # Indicators
    ma7 = compute_ma(candles, 7)
    ma20 = compute_ma(candles, 20)
    rsi = compute_rsi(candles, 14)
    atr = compute_atr(candles, 14)
    supports, resistances = detect_support_resistance(candles)
    patterns = detect_patterns(candles)

    # ASCII chart
    chart = generate_ascii_chart(candles, width=50, height=18, show_volume=True)

    # OHLC table
    ohlc_lines = ["Candle | Timestamp           | Open     | High     | Low      | Close    | Volume"]
    ohlc_lines.append("─" * 90)
    for i, c in enumerate(candles):
        ohlc_lines.append(
            f"  {i + 1:3d}  | {c['timestamp']:19s} | {c['open']:8.5f} | {c['high']:8.5f} | "
            f"{c['low']:8.5f} | {c['close']:8.5f} | {c['volume']}"
        )

    # Latest indicator values
    latest_ma7 = ma7[-1]
    latest_ma20 = ma20[-1]
    latest_rsi = rsi[-1]
    latest_atr = atr[-1]

    # Trend detection
    trend = "NEUTRAL"
    if latest_ma7 and latest_ma20:
        if latest_ma7 > latest_ma20:
            trend = "BULLISH (MA7 > MA20)"
        elif latest_ma7 < latest_ma20:
            trend = "BEARISH (MA7 < MA20)"

    # Price action summary
    first_close = candles[0]["close"]
    last_close = candles[-1]["close"]
    price_change = last_close - first_close
    price_change_pct = (price_change / first_close) * 100

    highest = max(c["high"] for c in candles)
    lowest = min(c["low"] for c in candles)

    # Build output
    output = []
    output.append("=" * 80)
    output.append("📊 CHART ANALYSIS PACKAGE")
    output.append("=" * 80)

    output.append("")
    output.append(chart)

    output.append("")
    output.append("─" * 80)
    output.append("📈 OHLC DATA")
    output.append("─" * 80)
    output.extend(ohlc_lines)

    output.append("")
    output.append("─" * 80)
    output.append("📐 TECHNICAL INDICATORS")
    output.append("─" * 80)
    output.append(f"  MA(7):          {latest_ma7:.5f}" if latest_ma7 else "  MA(7):          N/A")
    output.append(f"  MA(20):         {latest_ma20:.5f}" if latest_ma20 else "  MA(20):         N/A")
    output.append(f"  RSI(14):        {latest_rsi:.1f}" if latest_rsi else "  RSI(14):        N/A")
    output.append(f"  ATR(14):        {latest_atr:.5f}" if latest_atr else "  ATR(14):        N/A")
    output.append(f"  Trend:          {trend}")
    output.append(f"  Highest High:   {highest:.5f}")
    output.append(f"  Lowest Low:     {lowest:.5f}")
    output.append(f"  Price Change:   {price_change:+.5f} ({price_change_pct:+.2f}%)")

    output.append("")
    output.append("─" * 80)
    output.append("🔑 SUPPORT & RESISTANCE LEVELS")
    output.append("─" * 80)
    if supports:
        output.append(f"  Support:    {', '.join(f'{s:.5f}' for s in supports)}")
    else:
        output.append("  Support:    None detected")
    if resistances:
        output.append(f"  Resistance: {', '.join(f'{r:.5f}' for r in resistances)}")
    else:
        output.append("  Resistance: None detected")

    output.append("")
    output.append("─" * 80)
    output.append("🔍 DETECTED PATTERNS")
    output.append("─" * 80)
    if patterns:
        for p in patterns:
            output.append(f"  • {p}")
    else:
        output.append("  No significant patterns detected.")

    output.append("")
    output.append("=" * 80)

    return "\n".join(output)


def generate_llm_prompt(candles: List[Dict], pair: str = "EUR/USD", timeframe: str = "5min") -> str:
    """
    Generate the complete prompt to send to an LLM agent.

    Combines the chart analysis with the instruction prompt.
    """
    analysis = generate_analysis_text(candles)

    prompt = f"""You are a professional forex trading analyst. Analyze this {pair} {timeframe} chart.

{analysis}

TASK:
1. Analyze the price action, patterns, and trends you see in the data above
2. Identify key support and resistance levels
3. Note any significant candlestick patterns
4. Consider both retail concepts (S/R, patterns, indicators) AND smart money concepts (liquidity traps, stop hunts, order blocks, fair value gaps)
5. Make a decision: TRADE or SKIP

RESPOND IN THIS EXACT JSON FORMAT:
{{
  "decision": "TRADE" or "SKIP",
  "confidence": 0-100,
  "reasoning": "Your detailed analysis with specific candle references...",
  "key_levels": {{
    "support": [price levels],
    "resistance": [price levels]
  }},
  "patterns_seen": ["pattern1", "pattern2"],
  "concepts_used": ["concept1", "concept2"],
  "if_trade": {{
    "direction": "BUY" or "SELL",
    "entry": price,
    "stop_loss": price,
    "take_profit": price,
    "risk_reward": ratio
  }}
}}

Be specific. Reference exact candles (candle 1, candle 2, etc. from left to right).
Use both retail analysis AND smart money analysis."""

    return prompt


# ── CLI Entry Point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    csv_path = sys.argv[1] if len(sys.argv) > 1 else str(
        Path(__file__).parent.parent / "data" / "eurusd_5m_sample.csv"
    )

    print(f"Loading data from: {csv_path}")
    candles = load_csv(csv_path)
    print(f"Loaded {len(candles)} candles\n")

    # Print the full analysis package
    print(generate_analysis_text(candles))

    # Print sample LLM prompt
    print("\n\n")
    print("=" * 80)
    print("📝 SAMPLE LLM PROMPT (what gets sent to agents)")
    print("=" * 80)
    print(generate_llm_prompt(candles))
