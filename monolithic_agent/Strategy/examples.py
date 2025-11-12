"""
Example Strategies - Test cases and example strategies for validation
Contains various strategy formats for unit testing and demonstrations.
"""

from typing import Dict, Any, List

# Example 1: Simple EMA Crossover (from spec)
EXAMPLE_1_EMA_CROSSOVER = """
Buy 100 shares when 50 EMA crosses above 200 EMA. 
Place stop at 1% below entry. Take profit at 2%. 
No position sizing rule.
"""

EXAMPLE_1_EXPECTED_OUTPUT = {
    "strategy_id": "strat-20251014-001",
    "version": "0.1.0",
    "title": "EMA Crossover Simple",
    "description": "Buy on 50 EMA crossing above 200 EMA. Fixed position. SL 1%, TP 2%.",
    "classification": {
        "type": "trend-following",
        "risk_tier": "medium",
        "primary_instruments": ["AAPL", "SPY"]
    },
    "steps": [
        {
            "step_id": "s1",
            "order": 1,
            "title": "Entry rule",
            "trigger": "50 EMA crosses above 200 EMA on 5m bar",
            "condition": "no open position on instrument",
            "action": {
                "type": "enter",
                "order_type": "market",
                "instrument": "ticker",
                "size": {"mode": "fixed", "value": 100}
            },
            "exit": {
                "stop_loss": "1% below entry",
                "take_profit": "2% above entry"
            },
            "params": [
                {"name": "ema_fast", "value": 50},
                {"name": "ema_slow", "value": 200}
            ],
            "rationale": "Simple trend-follow test"
        }
    ]
}

# Example 2: RSI Mean Reversion
EXAMPLE_2_RSI_MEAN_REVERSION = """
1. When RSI(14) drops below 30, buy 5% of equity
2. When RSI rises above 70, sell position
3. Set stop loss at 2% below entry
4. Maximum 3 concurrent positions
"""

# Example 3: Numbered Scalping Strategy
EXAMPLE_3_SCALPING_NUMBERED = """
1. Entry: Buy when price breaks above 5-minute high with volume > 2x average
2. Size: Risk 1% of account per trade
3. Exit: Take profit at +0.5% or stop loss at -0.3%
4. Re-entry: Wait 10 minutes after stop out
5. Time filter: Only trade 9:30 AM - 3:30 PM EST
"""

# Example 4: Swing Trading Strategy
EXAMPLE_4_SWING_TRADING = """
This is a swing trading strategy for SPY and QQQ.

Entry conditions:
- Wait for 20-day EMA to cross above 50-day EMA
- Confirm with MACD crossover (signal line)
- Volume should be above 20-day average

Position sizing:
- Risk 2% of portfolio per trade
- Maximum position size: 10% of portfolio

Exit rules:
- Stop loss: 3% below entry
- Profit target: 6% above entry (2:1 risk/reward)
- Trailing stop: After 4% profit, trail at 2%

Time horizon: Hold for 3-10 days typically
"""

# Example 5: Dangerous Strategy (for guardrails testing)
EXAMPLE_5_DANGEROUS = """
This is a guaranteed profit pump and dump strategy!
Use 10x leverage with no stop loss.
Risk 100% of your account on each trade.
You can't lose with this insider information!
"""

# Example 6: URL Reference
EXAMPLE_6_URL_REFERENCE = """
https://youtube.com/watch?v=abc123 — Here's an interesting scalping strategy 
from a popular trader. Please analyze and convert to steps.
"""

# Example 7: Options Strategy
EXAMPLE_7_OPTIONS = """
Sell cash-secured puts on AAPL:
1. When IV rank > 50%, sell 30-45 DTE put at 0.30 delta
2. Size: Use 10% of account per position
3. Close at 50% profit or 21 DTE, whichever comes first
4. Roll down and out if tested and fundamentals still good
"""

# Example 8: Multi-step Intraday
EXAMPLE_8_INTRADAY_MULTI = """
Step 1: Pre-market scan
- Identify stocks with gap up > 3% on news
- Volume > 500K shares in pre-market
- Price > $10

Step 2: Entry setup
- Wait for first 15-minute consolidation
- Enter on break of consolidation high
- Use limit order at breakout + $0.05

Step 3: Position management
- Size: 500 shares per signal
- Stop: Below consolidation low
- Target: 2x risk or previous day high

Step 4: Exit rules
- Close 50% at 1:1 risk/reward
- Trail remaining 50% with 15-min low
- Exit all by 3:45 PM
"""

# Example 9: Incomplete Strategy (for recommendations)
EXAMPLE_9_INCOMPLETE = """
Buy when price goes up. Sell when it goes down.
Use AAPL stock.
"""

# Example 10: Complex Multi-Condition
EXAMPLE_10_COMPLEX = """
Entry Long:
- 50 EMA > 200 EMA (daily timeframe)
- RSI(14) between 40-60 (4-hour timeframe)  
- Price pulls back to 21 EMA on 1-hour chart
- Volume spike (1.5x average) on reversal candle
- Enter at market on next candle open

Position Sizing:
- Calculate ATR(14) on daily chart
- Risk 1% of account
- Position size = (Account * 0.01) / (2 * ATR)

Exits:
- Stop loss: 2 * ATR below entry
- First target: 3 * ATR above entry (close 50%)
- Second target: 5 * ATR above entry (close 50%)
- Trailing stop: 1.5 * ATR after first target hit

Re-entry Rules:
- Can add to position if profit > 1 * ATR
- Maximum 2 positions per symbol
- No new entries if market down > 2% (SPY)
"""

# Collect all examples
ALL_EXAMPLES = [
    {
        "id": 1,
        "name": "Simple EMA Crossover",
        "input": EXAMPLE_1_EMA_CROSSOVER,
        "expected_type": "trend-following",
        "expected_risk": "medium",
        "should_pass": True
    },
    {
        "id": 2,
        "name": "RSI Mean Reversion",
        "input": EXAMPLE_2_RSI_MEAN_REVERSION,
        "expected_type": "mean-reversion",
        "expected_risk": "medium",
        "should_pass": True
    },
    {
        "id": 3,
        "name": "Scalping Strategy",
        "input": EXAMPLE_3_SCALPING_NUMBERED,
        "expected_type": "scalping",
        "expected_risk": "low",
        "should_pass": True
    },
    {
        "id": 4,
        "name": "Swing Trading",
        "input": EXAMPLE_4_SWING_TRADING,
        "expected_type": "swing",
        "expected_risk": "low",
        "should_pass": True
    },
    {
        "id": 5,
        "name": "Dangerous Strategy",
        "input": EXAMPLE_5_DANGEROUS,
        "expected_type": "other",
        "expected_risk": "high",
        "should_pass": False
    },
    {
        "id": 6,
        "name": "URL Reference",
        "input": EXAMPLE_6_URL_REFERENCE,
        "expected_type": "unknown",
        "expected_risk": "unknown",
        "should_pass": "url"
    },
    {
        "id": 7,
        "name": "Options Strategy",
        "input": EXAMPLE_7_OPTIONS,
        "expected_type": "other",
        "expected_risk": "medium",
        "should_pass": True
    },
    {
        "id": 8,
        "name": "Multi-step Intraday",
        "input": EXAMPLE_8_INTRADAY_MULTI,
        "expected_type": "intraday",
        "expected_risk": "medium",
        "should_pass": True
    },
    {
        "id": 9,
        "name": "Incomplete Strategy",
        "input": EXAMPLE_9_INCOMPLETE,
        "expected_type": "other",
        "expected_risk": "high",
        "should_pass": True  # Should pass but with many recommendations
    },
    {
        "id": 10,
        "name": "Complex Multi-Condition",
        "input": EXAMPLE_10_COMPLEX,
        "expected_type": "trend-following",
        "expected_risk": "low",
        "should_pass": True
    }
]


def get_example(example_id: int) -> Dict[str, Any]:
    """Get a specific example by ID."""
    for example in ALL_EXAMPLES:
        if example["id"] == example_id:
            return example
    return None


def get_all_examples() -> List[Dict[str, Any]]:
    """Get all examples."""
    return ALL_EXAMPLES


def get_safe_examples() -> List[Dict[str, Any]]:
    """Get only safe examples (for normal testing)."""
    return [ex for ex in ALL_EXAMPLES if ex["should_pass"] is True]


def get_dangerous_examples() -> List[Dict[str, Any]]:
    """Get dangerous examples (for guardrails testing)."""
    return [ex for ex in ALL_EXAMPLES if ex["should_pass"] is False]


def get_url_examples() -> List[Dict[str, Any]]:
    """Get URL-based examples."""
    return [ex for ex in ALL_EXAMPLES if ex["should_pass"] == "url"]


if __name__ == "__main__":
    print("Strategy Examples Library")
    print("=" * 70)
    print(f"Total examples: {len(ALL_EXAMPLES)}")
    print(f"Safe examples: {len(get_safe_examples())}")
    print(f"Dangerous examples: {len(get_dangerous_examples())}")
    print(f"URL examples: {len(get_url_examples())}")
    
    print("\n" + "=" * 70)
    print("Example List:")
    print("=" * 70)
    for example in ALL_EXAMPLES:
        status = "✓" if example["should_pass"] is True else "✗" if example["should_pass"] is False else "🔗"
        print(f"{status} Example {example['id']}: {example['name']}")
        print(f"   Type: {example['expected_type']}, Risk: {example['expected_risk']}")
    
    print("\n" + "=" * 70)
    print("Sample Input (Example 1):")
    print("=" * 70)
    print(EXAMPLE_1_EMA_CROSSOVER)
