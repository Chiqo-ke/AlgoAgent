# Strategy Integration Flow Diagram

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ALGOAGENT SYSTEM                             │
│                     (Complete Integration)                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐    ┌──────────────────────┐    ┌──────────────┐
│   Strategy Module   │───►│  Backtest Module     │───►│ Data Module  │
│                     │    │                      │    │              │
│ - Validator         │    │ - Interactive Runner │    │ - Fetcher    │
│ - Canonicalizer     │    │ - SimBroker          │    │ - Indicators │
│ - AI Integration    │    │ - Code Generator     │    │              │
└─────────────────────┘    └──────────────────────┘    └──────────────┘
         │                            │                        │
         │                            │                        │
         └────────────────┬───────────┴────────────────────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │  USER INTERACTION   │
                │   (Command Line)    │
                └─────────────────────┘
```

## Interactive Runner v2.0 - Internal Flow

```
                    ┌────────────────────────┐
                    │    USER STARTS         │
                    │ interactive_backtest_  │
                    │      runner.py         │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  1. SYMBOL & DATES     │
                    │                        │
                    │  get_user_symbol()     │
                    │  get_user_date_range() │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  2. DATA INTERVAL      │
                    │                        │
                    │  get_user_interval()   │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  3. FETCH DATA         │
                    │                        │
                    │  Data Module:          │
                    │  fetch_data_by_date_   │
                    │       range()          │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  4. CONFIGURATION      │
                    │                        │
                    │  get_backtest_config() │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  5. BROKER INIT        │
                    │                        │
                    │  SimBroker(config)     │
                    └───────────┬────────────┘
                                │
        ┌───────────────────────▼───────────────────────┐
        │         6. STRATEGY SELECTION (NEW!)          │
        │                                               │
        │  get_user_strategy_choice()                   │
        └───┬────────────────────┬─────────────┬───────┘
            │                    │             │
    ┌───────▼──────┐    ┌───────▼───────┐    ┌▼───────────┐
    │ Option 1:    │    │ Option 2:     │    │ Option 3:  │
    │ NEW STRATEGY │    │ EXISTING      │    │ EXAMPLE    │
    └───────┬──────┘    └───────┬───────┘    └┬───────────┘
            │                   │              │
            │                   │              │
    ┌───────▼──────────────────────────────┐  │
    │  New Strategy Workflow               │  │
    │  ═══════════════════════             │  │
    │                                      │  │
    │  ┌──────────────────────────────┐   │  │
    │  │ enter_new_strategy()         │   │  │
    │  │ • Multi-line text input      │   │  │
    │  │ • Plain English description  │   │  │
    │  └──────────┬───────────────────┘   │  │
    │             │                        │  │
    │  ┌──────────▼───────────────────┐   │  │
    │  │ validate_and_canonicalize_   │   │  │
    │  │        strategy()            │   │  │
    │  │                              │   │  │
    │  │ ┌────────────────────────┐   │   │  │
    │  │ │ Strategy Module        │   │   │  │
    │  │ │ ──────────────────     │   │   │  │
    │  │ │ StrategyValidatorBot   │   │   │  │
    │  │ │ • Parse natural lang   │   │   │  │
    │  │ │ • Security checks      │   │   │  │
    │  │ │ • AI analysis (Gemini) │   │   │  │
    │  │ │ • Canonicalize to JSON │   │   │  │
    │  │ │ • Classification       │   │   │  │
    │  │ └────────────────────────┘   │   │  │
    │  └──────────┬───────────────────┘   │  │
    │             │                        │  │
    │  ┌──────────▼───────────────────┐   │  │
    │  │ generate_strategy_code()     │   │  │
    │  │                              │   │  │
    │  │ ┌────────────────────────┐   │   │  │
    │  │ │ GeminiStrategyGenerator│   │   │  │
    │  │ │ ──────────────────────  │   │   │  │
    │  │ │ • Read canonical JSON  │   │   │  │
    │  │ │ • Generate Python code │   │   │  │
    │  │ │ • SimBroker compatible │   │   │  │
    │  │ │ • Save .py and .json   │   │   │  │
    │  │ └────────────────────────┘   │   │  │
    │  └──────────┬───────────────────┘   │  │
    │             │                        │  │
    │  ┌──────────▼───────────────────┐   │  │
    │  │ load_strategy_class_from_    │   │  │
    │  │         file()               │   │  │
    │  │ • Dynamic import             │   │  │
    │  │ • Find strategy class        │   │  │
    │  └──────────┬───────────────────┘   │  │
    │             │                        │  │
    └─────────────┼────────────────────────┘  │
                  │                           │
                  │    ┌──────────────────────┘
                  │    │
            ┌─────▼────▼──────────────────┐
            │ list_existing_strategies()  │
            │ select_existing_strategy()  │
            │ • Scan codes/ directory     │
            │ • User selects .py file     │
            │ • Load strategy class       │
            └─────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────────────────┐
    │             │                         │
    │  ┌──────────▼───────────────────┐    │
    │  │ SimpleMAStrategy             │    │
    │  │ • Built-in example           │    │
    │  │ • Customizable parameters    │    │
    │  └──────────┬───────────────────┘    │
    │             │                         │
    └─────────────┼─────────────────────────┘
                  │
        ┌─────────▼──────────┐
        │ get_strategy_      │
        │   parameters()     │
        │ • Inspect class    │
        │ • User input       │
        │ • Type conversion  │
        └─────────┬──────────┘
                  │
        ┌─────────▼──────────┐
        │ 7. RUN BACKTEST    │
        │                    │
        │ run_backtest_      │
        │   simulation()     │
        │ • Initialize       │
        │ • Loop bars        │
        │ • strategy.on_bar()│
        │ • broker.step_to() │
        └─────────┬──────────┘
                  │
        ┌─────────▼──────────┐
        │ 8. RESULTS         │
        │                    │
        │ display_results()  │
        │ save_results()     │
        │ • Metrics          │
        │ • Trades CSV       │
        │ • Metrics JSON     │
        └────────────────────┘
```

## Module Interaction Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    USER INPUT LAYER                            │
├────────────────────────────────────────────────────────────────┤
│  Interactive CLI                                               │
│  • Symbol: AAPL                                                │
│  • Dates: 2024-01-01 to 2024-10-22                            │
│  • Strategy: "Buy when RSI < 30..."                           │
└────────────┬───────────────────────────────────────────────────┘
             │
┌────────────▼───────────────────────────────────────────────────┐
│                  STRATEGY MODULE                               │
├────────────────────────────────────────────────────────────────┤
│  strategy_validator.py                                         │
│  ├─► StrategyValidatorBot                                      │
│  │   ├─► InputParser (parse text)                             │
│  │   ├─► Guardrails (security)                                │
│  │   ├─► GeminiStrategyIntegrator (AI)                        │
│  │   └─► CanonicalStrategy (JSON)                             │
│  │                                                             │
│  OUTPUT:                                                       │
│  {                                                             │
│    "strategy_id": "strat-001",                                 │
│    "title": "RSI Mean Reversion",                             │
│    "steps": [...],                                             │
│    "classification": {...}                                     │
│  }                                                             │
└────────────┬───────────────────────────────────────────────────┘
             │ Canonical JSON
┌────────────▼───────────────────────────────────────────────────┐
│                GEMINI CODE GENERATOR                           │
├────────────────────────────────────────────────────────────────┤
│  gemini_strategy_generator.py                                  │
│  ├─► GeminiStrategyGenerator                                   │
│  │   ├─► Read canonical JSON                                   │
│  │   ├─► Load SYSTEM_PROMPT.md                                │
│  │   ├─► Call Gemini API                                       │
│  │   └─► Generate Python code                                  │
│  │                                                             │
│  OUTPUT:                                                       │
│  class RsiMeanReversion:                                       │
│      def __init__(self, broker, ...):                          │
│          self.broker = broker                                  │
│      def on_bar(self, timestamp, data):                        │
│          # Strategy logic                                      │
│          if rsi < 30 and price > ma:                           │
│              self.broker.emit_signal(...)                      │
│                                                                │
│  SAVED TO: Backtest/codes/rsi_mean_reversion.py               │
└────────────┬───────────────────────────────────────────────────┘
             │ Python Code
┌────────────▼───────────────────────────────────────────────────┐
│              BACKTEST EXECUTION ENGINE                         │
├────────────────────────────────────────────────────────────────┤
│  SimBroker + Strategy                                          │
│  ├─► Load strategy class dynamically                           │
│  ├─► Initialize with parameters                                │
│  ├─► Loop through market data                                  │
│  │   ├─► strategy.on_bar(timestamp, data)                     │
│  │   └─► broker.step_to(timestamp, data)                      │
│  └─► Compute metrics                                           │
│                                                                │
│  COMPONENTS:                                                   │
│  • account_manager.py (positions, cash)                        │
│  • order_manager.py (orders)                                   │
│  • execution_simulator.py (fills)                              │
│  • metrics_engine.py (performance)                             │
└────────────┬───────────────────────────────────────────────────┘
             │ Metrics & Trades
┌────────────▼───────────────────────────────────────────────────┐
│                  DATA MODULE                                   │
├────────────────────────────────────────────────────────────────┤
│  data_fetcher.py                                               │
│  ├─► DataFetcher                                               │
│  │   └─► fetch_data_by_date_range()                           │
│  │       ├─► Yahoo Finance API                                 │
│  │       └─► Return OHLCV DataFrame                            │
│  │                                                             │
│  indicator_calculator.py                                       │
│  └─► compute_indicator()                                       │
│      └─► TA-Lib / pandas-ta                                    │
└────────────┬───────────────────────────────────────────────────┘
             │ Market Data + Indicators
┌────────────▼───────────────────────────────────────────────────┐
│                  RESULTS & STORAGE                             │
├────────────────────────────────────────────────────────────────┤
│  Backtest/results/                                             │
│  ├─► AAPL_trades_20241022_165432.csv                          │
│  │   • Trade log with P&L                                      │
│  └─► AAPL_metrics_20241022_165432.json                        │
│      • Sharpe, drawdown, win rate, etc.                        │
│                                                                │
│  Backtest/codes/                                               │
│  ├─► rsi_mean_reversion.py                                     │
│  │   • Generated strategy code                                 │
│  └─► rsi_mean_reversion.json                                   │
│      • Canonical strategy definition                           │
└────────────────────────────────────────────────────────────────┘
```

## Comparison: Old vs New Flow

### OLD FLOW (v1.0)
```
User Input
    │
    ▼
[Symbol & Dates]
    │
    ▼
[Fetch Data]
    │
    ▼
[Hardcoded Strategy]  ◄── Fixed to example_strategy.py
    │
    ▼
[Run Backtest]
    │
    ▼
[Results]
```

### NEW FLOW (v2.0)
```
User Input
    │
    ▼
[Symbol & Dates]
    │
    ▼
[Fetch Data]
    │
    ▼
[Strategy Selection]  ◄── Three options!
    │
    ├─► [NEW]
    │   ├─► Text Input
    │   ├─► AI Validation (Strategy Module)
    │   ├─► Code Generation (Gemini)
    │   └─► Dynamic Loading
    │
    ├─► [EXISTING]
    │   ├─► List codes/
    │   └─► Load selected
    │
    └─► [EXAMPLE]
        └─► SimpleMAStrategy
    │
    ▼
[Run Backtest]
    │
    ▼
[Results + Save Code]  ◄── Strategy saved for reuse
```

## File Generation Flow

```
User enters:
"Buy when RSI < 30"
        │
        ▼
┌────────────────────┐
│ Validation         │
│ (Strategy Module)  │
└────────┬───────────┘
         │
         │ Creates
         ▼
┌────────────────────┐
│ Canonical JSON     │
│ ─────────────────  │
│ {                  │
│   "strategy_id":   │
│   "strat-001",     │
│   "steps": [...]   │
│ }                  │
└────────┬───────────┘
         │
         │ Feeds into
         ▼
┌────────────────────┐
│ Code Generator     │
│ (Gemini)           │
└────────┬───────────┘
         │
         │ Produces
         ▼
┌────────────────────────────────────┐
│ TWO FILES IN Backtest/codes/       │
│                                    │
│ 1. rsi_mean_reversion.py           │
│    ┌─────────────────────────┐    │
│    │ class RsiMeanReversion: │    │
│    │   def on_bar(...):      │    │
│    │     # Strategy logic    │    │
│    └─────────────────────────┘    │
│                                    │
│ 2. rsi_mean_reversion.json         │
│    ┌─────────────────────────┐    │
│    │ {                       │    │
│    │   "strategy_id": ...,   │    │
│    │   "steps": [...]        │    │
│    │ }                       │    │
│    └─────────────────────────┘    │
└────────────────────────────────────┘
         │
         │ Both preserved
         ▼
┌────────────────────┐
│ Strategy Library   │
│ • Reusable         │
│ • Documented       │
│ • Versioned        │
└────────────────────┘
```

## Integration Benefits Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                    BEFORE (v1.0)                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Interactive Runner          Strategy Module               │
│  ┌─────────────────┐         ┌──────────────┐             │
│  │ • Symbol input  │         │ • Validation │             │
│  │ • Date input    │    ✗    │ • AI parsing │             │
│  │ • Data fetch    │  NO LINK │ • Canonical  │             │
│  │ • Fixed strategy│         └──────────────┘             │
│  └─────────────────┘                                       │
│         ↓                                                   │
│  [Example strategy only]                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    AFTER (v2.0)                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Interactive Runner          Strategy Module               │
│  ┌─────────────────┐         ┌──────────────┐             │
│  │ • Symbol input  │         │ • Validation │             │
│  │ • Date input    │    ✓    │ • AI parsing │             │
│  │ • Data fetch    │  LINKED │ • Canonical  │             │
│  │ • Strategy pick │◄────────┤ • Code gen   │             │
│  └────────┬────────┘         └──────────────┘             │
│           │                         ↓                       │
│           │                  ┌──────────────┐             │
│           │                  │ Gemini       │             │
│           └─────────────────►│ Generator    │             │
│                              └──────┬───────┘             │
│                                     ↓                       │
│                        ┌────────────────────┐             │
│                        │ codes/             │             │
│                        │ • .py files        │             │
│                        │ • .json files      │             │
│                        └────────────────────┘             │
│                                                             │
│  [Dynamic strategy loading, reusable library]              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
