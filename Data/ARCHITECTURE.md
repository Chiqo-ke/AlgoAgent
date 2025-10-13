# AlgoAgent System Architecture and Data Flow

This document provides a detailed overview of the internal architecture of the AlgoAgent data ingestion model, explaining the role of each module and how data flows through the system during a typical run.

## Core Principles

The system is built on three core principles:

1.  **Modularity**: Each component has a single, well-defined responsibility (e.g., fetching data, calculating indicators, generating code).
2.  **Extensibility**: The system is designed to be easily extended with new indicators without modifying the core logic, primarily through the registry and dynamic code generation.
3.  **Safety**: Dynamic code generation, a powerful but risky feature, is gated by automated testing to prevent system instability.

## Module Breakdown

The system is composed of several key Python modules that work in concert.

### 1. Orchestrator (`main.py`)

*   **Purpose**: This is the central nervous system of the application.
*   **Key Component**: `DataIngestionModel` class.
*   **Responsibilities**:
    *   Provides the main public method `ingest_and_process()`.
    *   Coordinates the entire workflow: fetching data, checking for indicators, triggering dynamic code generation, and calculating results.
    *   Manages the critical safety-checked workflow for adding new indicators: it calls the code adjuster, runs `pytest`, and reverts changes if tests fail.

### 2. Data Source (`data_fetcher.py`)

*   **Purpose**: Acts as the sole entry point for external market data.
*   **Key Component**: `DataFetcher` class.
*   **Responsibilities**:
    *   Abstracts the `yfinance` library.
    *   Provides simple methods (`fetch_historical_data`, `fetch_data_by_date_range`) to retrieve OHLCV (Open, High, Low, Close, Volume) data.

### 3. The Hybrid Indicator Subsystem

This is the heart of the system, designed for both performance and portability. It consists of several collaborating modules.

*   **`indicator_calculator.py` (The Public API)**
    *   **Purpose**: Provides a stable, high-level interface for the rest of the application to interact with indicators.
    *   **Key Methods**:
        *   `compute_indicator()`: Calculates a named indicator.
        *   `describe_indicator()`: Retrieves metadata about an indicator.
    *   **How it works**: It does not contain any calculation logic itself. Instead, it consults the `registry` to find and execute the correct implementation.

*   **`registry.py` (The Switchboard)**
    *   **Purpose**: To map indicator names (like "SMA") to the actual Python functions that implement them.
    *   **How it works**:
        1.  On startup, it inspects the `talib_adapters` and `ta_fallback_adapters` modules.
        2.  It checks if `TA-Lib` is installed (`talib_adapters.HAS_TALIB`).
        3.  If `TA-Lib` is available, it registers the high-performance functions from `talib_adapters`. If not, it registers the pure-Python functions from `ta_fallback_adapters` as a fallback.
        4.  It automatically discovers indicator metadata (inputs, outputs, defaults) by parsing the docstrings of the adapter functions. This makes the system "pluggable."

*   **`talib_adapters.py` & `ta_fallback_adapters.py` (The Implementations)**
    *   **Purpose**: These files contain the actual indicator calculation logic.
    *   `talib_adapters.py`: Contains thin wrappers around `TA-Lib` functions. These are used when performance is paramount and the library is installed.
    *   `ta_fallback_adapters.py`: Contains wrappers around the `ta` library or custom `pandas`/`numpy` implementations (like for VWAP). These ensure the application works anywhere, even without the `TA-Lib` C-library.

### 4. The Dynamic Code Generation Subsystem

This subsystem gives the agent the ability to "learn" new indicators on the fly.

*   **`gemini_integrator.py` (The Brain)**
    *   **Purpose**: To generate Python code for a new, unknown indicator.
    *   **How it works**: It formulates a precise prompt and sends it to the Gemini LLM. The current version uses a mock to return a pre-written snippet for "VIX" for testing purposes.

*   **`dynamic_code_adjuster.py` (The Surgeon)**
    *   **Purpose**: To safely insert the new code snippet into the correct file (`ta_fallback_adapters.py`).
    *   **How it works**: It uses Python's `ast` (Abstract Syntax Tree) module to parse the file. This is safer than simple text manipulation because it understands the code's structure. It checks if a function already exists before appending the new snippet to avoid duplication.

### 5. Other Modules

*   **`ml_model_selector.py`**: An optional module that can be used to train a `RandomForestClassifier` on the generated features to determine which indicators are most predictive.
*   **`context_manager.py`**: A generic state management class. It is not currently used by `main.py`, which favors passing parameters directly for clarity.
*   **`interactive_test.py`**: A command-line interface (CLI) that provides a user-friendly way to run the `DataIngestionModel` with custom inputs.

---

## Data Flow Diagram

Below are two common data flow scenarios that illustrate how the modules interact.

### Scenario 1: Indicator Exists

This is the flow when a user requests an indicator that is already registered (e.g., "RSI").

```
1. User calls `ingest_and_process(ticker="AAPL", required_indicators=[{'name': 'RSI'}])` in `main.py`.
   |
   v
2. `DataFetcher` is called -> Fetches OHLCV data from yfinance.
   |
   v
3. `_check_and_update_indicators` loop begins.
   |
   v
4. `indicator_calculator.describe_indicator('RSI')` is called.
   |
   v
5. `registry.get_entry('rsi')` finds the 'RSI' entry -> No error is raised.
   |
   v
6. Loop finishes. No code was changed.
   |
   v
7. `indicator_calculator.compute_indicator('RSI', df)` is called.
   |
   v
8. `registry` provides the correct function (e.g., `talib_adapters.RSI` if available, otherwise `ta_fallback_adapters.RSI`).
   |
   v
9. The adapter function runs, calculates RSI, and returns a DataFrame.
   |
   v
10. The result is merged into the main DataFrame and returned to the user.
```

### Scenario 2: Indicator is Missing (Dynamic Flow)

This is the flow when a user requests an indicator that is not registered (e.g., "VIX").

```
1. User calls `ingest_and_process(ticker="AAPL", required_indicators=[{'name': 'VIX'}])`.
   |
   v
2. `DataFetcher` gets data.
   |
   v
3. `_check_and_update_indicators` loop begins.
   |
   v
4. `indicator_calculator.describe_indicator('VIX')` is called.
   |
   v
5. `registry.get_entry('vix')` returns `None` -> A `ValueError` is raised.
   |
   v
6. The `except` block in `main.py` is triggered.
   |
   v
7. `gemini_integrator.suggest_code_update('VIX')` -> Returns a Python code snippet for a VIX function.
   |
   v
8. `dynamic_code_adjuster.insert_snippet_if_missing(...)` -> Appends the VIX function to `ta_fallback_adapters.py`.
   |
   v
9. `subprocess.run('pytest ...')` is executed -> The test suite runs to validate the new code.
   |
   v
10. Tests pass!
    |
    v
11. `importlib.reload()` is called on `ta_fallback_adapters`, `registry`, and `indicator_calculator` to load the new VIX function into the live session.
    |
    v
12. The process continues to the calculation step (Step 7 in Scenario 1), where `compute_indicator('VIX', ...)` now succeeds.

---
```

## Testing the System

The system includes several ways to test its functionality, from isolated component checks to full end-to-end validation.

### 1. Unit Testing (`pytest`)

*   **Purpose**: To test individual modules in isolation and ensure they behave as expected. This is the fastest and most reliable way to catch regressions.
*   **Location**: `Data/tests/`
*   **How it works**: The test suite uses `pytest` and `pytest-mock` to test components like the `registry`, `data_fetcher` (by mocking network calls), and `dynamic_code_adjuster` (by using temporary files).
*   **How to run**:
    ```bash
    # Navigate to the root of the project
    # Run the test suite located in the Data directory
    python -m pytest Data/tests/ -v
    ```

### 2. Interactive End-to-End Testing (`interactive_test.py`)

*   **Purpose**: To allow a user to manually test the complete `ingest_and_process` workflow with live data from `yfinance`.
*   **How it works**: This script prompts the user for a stock ticker, time period, interval, and a selection of indicators. It then calls the `DataIngestionModel` and prints the results, saving the final DataFrame to a CSV file.
*   **How to run**:
    ```bash
    # Run from the root directory
    python interactive_test.py
    ```
12. The process continues to the calculation step (Step 7 in Scenario 1), where `compute_indicator('VIX', ...)` now succeeds.
```
