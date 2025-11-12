# Dynamic Data Ingestion Model for Financial Securities

## Objective

This model is designed to provide a dynamic data ingestion pipeline capable of automatically fetching financial security data, computing technical indicators, and intelligently adapting its calculations and code based on contextual input. It leverages AI for dynamic code adjustments and machine learning for optimal indicator selection, aiming for a scalable and efficient solution without extensive manual code changes.

## Architecture Overview

The model follows a modular architecture, ensuring clear separation of concerns and facilitating maintainability and extensibility. The core components interact as follows:

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {
  'background': 'transparent',
  'primaryColor': 'transparent',
  'primaryBorderColor': '#ffffff',
  'primaryTextColor': '#ffffff',
  'lineColor': '#ffffff',
  'fontSize': '14px',
  'tertiaryColor': 'transparent'
}}}%%

graph TD
    A[User/Context Input] --> B{Contextual Awareness Layer}
    B --> C[Data Fetcher Module]
    B --> D[Technical Indicator Calculation Module]
    B --> E[Machine Learning Module]
    B --> F[Gemini Integration Module]

    C --> G[Raw Financial Data]
    D --> H[Computed Technical Indicators]
    E --> I[Optimal Indicators & Parameters]
    F --> J[TA-Lib Documentation & AI-Assisted Code Suggestions]

    G & H & I --> K[Dynamic Code Adjustment Module]
    K --> L[Updated Indicator Calculation Logic]
    L --> D

    style A fill:transparent,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style B fill:transparent,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style C fill:transparent,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style D fill:transparent,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style E fill:transparent,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style F fill:transparent,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style G fill:transparent,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style H fill:transparent,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style I fill:transparent,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style J fill:transparent,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style K fill:transparent,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style L fill:transparent,stroke:#ffffff,stroke-width:2px,color:#ffffff

```
## Module-wise Breakdown

### 1. Context Manager
- **File:** [`AlgoAgent/Data/context_manager.py`](AlgoAgent/Data/context_manager.py)
- **Class:** `ContextManager`
- **Purpose:** Manages the operational context of the model, including the financial security ticker, required technical indicators, data fetching periods, and intervals. It acts as a central repository for dynamic configuration.
- **Key Functions:**
    - `set_context(key, value)`: Stores a key-value pair in the context.
    - `get_context(key, default)`: Retrieves a value from the context.
    - `update_context(new_context)`: Updates the entire context with a dictionary.
    - `get_required_indicators()`: Retrieves the list of indicators to be calculated.
    - `set_required_indicators(indicators)`: Sets the list of required indicators.
    - `get_security_ticker()`: Retrieves the current security ticker.
    - `set_security_ticker(ticker)`: Sets the current security ticker.

### 2. Data Fetcher Module
- **File:** [`AlgoAgent/Data/data_fetcher.py`](AlgoAgent/Data/data_fetcher.py)
- **Class:** `DataFetcher`
- **Purpose:** Responsible for fetching historical financial data for specified securities from external sources (e.g., Yahoo Finance via `yfinance`).
- **Key Functions:**
    - `fetch_historical_data(ticker, period, interval)`: Fetches data for a given period and interval.
    - `fetch_data_by_date_range(ticker, start_date, end_date, interval)`: Fetches data within a specific date range.

### 3. Technical Indicator Calculation Module
- **File:** [`AlgoAgent/Data/indicator_calculator.py`](AlgoAgent/Data/indicator_calculator.py)
- **Class:** `IndicatorCalculator`
- **Purpose:** Computes a wide array of technical indicators using the `TA-Lib` library based on the fetched financial data and a list of specified indicators. This module is designed to be dynamically updated.
- **Key Function:**
    - `calculate_indicators(data, indicators)`: Takes a DataFrame and a list of indicator specifications, returning the DataFrame augmented with calculated indicator columns.

### 4. Machine Learning Model Selector
- **File:** [`AlgoAgent/Data/ml_model_selector.py`](AlgoAgent/Data/ml_model_selector.py)
- **Class:** `MLModelSelector`
- **Purpose:** Utilizes machine learning models (e.g., `RandomForestClassifier` from `scikit-learn`) to dynamically determine the most effective technical indicators and their optimal parameters for a given financial security.
- **Key Functions:**
    - `train_model(data, target_column, feature_columns)`: Trains an ML model using historical data and indicators.
    - `predict_optimal_indicators(current_data, feature_columns)`: Predicts and suggests optimal indicators or parameters based on the trained model.

### 5. Gemini Integration Module
- **File:** [`AlgoAgent/Data/gemini_integrator.py`](AlgoAgent/Data/gemini_integrator.py)
- **Class:** `GeminiIntegrator`
- **Purpose:** Interacts with Google's Gemini API to assist in understanding TA-Lib documentation and generating AI-assisted code snippets for new or updated indicators.
- **Key Functions:**
    - `get_talib_indicator_info(indicator_name)`: Fetches detailed information about a specific TA-Lib indicator.
    - `suggest_code_update(current_code, required_indicator_spec)`: Generates a Python code snippet for a new/updated indicator to be inserted into `indicator_calculator.py`.

### 6. Dynamic Code Adjustment Module
- **File:** [`AlgoAgent/Data/dynamic_code_adjuster.py`](AlgoAgent/Data/dynamic_code_adjuster.py)
- **Class:** `DynamicCodeAdjuster`
- **Purpose:** Intelligently modifies the `indicator_calculator.py` file by inserting or updating code snippets for technical indicator calculations. It uses Python's `ast` module for parsing and unparsing code to ensure structural integrity.
- **Key Function:**
    - `update_indicator_calculation_logic(current_indicator_calculator_code, new_indicator_snippet)`: Inserts a new code snippet into the `calculate_indicators` method of the `indicator_calculator.py` file.

### 7. Main Data Ingestion Model
- **File:** [`AlgoAgent/Data/main.py`](AlgoAgent/Data/main.py)
- **Class:** `DataIngestionModel`
- **Purpose:** The orchestrator of the entire data ingestion pipeline. It initializes all modules, manages the flow of data, triggers dynamic code adjustments, and integrates ML-driven insights.
- **Key Functions:**
    - `_check_and_update_indicator_logic(required_indicators)`: Internal method to check for missing indicators and trigger Gemini for code suggestions and dynamic code adjustment.
    - `_read_indicator_calculator_code()`: Reads the content of `indicator_calculator.py`.
    - `_write_indicator_calculator_code(content)`: Writes updated content to `indicator_calculator.py`.
    - `ingest_and_process(ticker, required_indicators, period, interval, ml_feature_columns, ml_target_column)`: The main public method that executes the entire data ingestion and processing workflow.

## Data Flow

1.  **User/Context Input:** The process begins with user-defined context, typically a financial `ticker` and a list of `required_indicators` (e.g., `[{'name': 'SMA', 'timeperiod': 20}]`). This input is managed by the `ContextManager` (`AlgoAgent/Data/context_manager.py`).
2.  **Raw Financial Data Fetching:** The `DataFetcher` (`AlgoAgent/Data/data_fetcher.py`) retrieves historical OHLCV (Open, High, Low, Close, Volume) data for the specified `ticker` and `period`/`interval`. This raw data is a `pandas.DataFrame`.
3.  **Indicator Logic Check & Update:** Before calculation, the `DataIngestionModel` (`AlgoAgent/Data/main.py`) checks if all `required_indicators` are implemented in the `IndicatorCalculator` (`AlgoAgent/Data/indicator_calculator.py`).
    *   If an indicator is missing, the `GeminiIntegrator` (`AlgoAgent/Data/gemini_integrator.py`) is prompted to `suggest_code_update()` for that indicator.
    *   The generated code snippet is then used by the `DynamicCodeAdjuster` (`AlgoAgent/Data/dynamic_code_adjuster.py`) to `update_indicator_calculation_logic()` within `indicator_calculator.py`, effectively modifying the code on the fly.
4.  **Technical Indicator Calculation:** The `IndicatorCalculator` (`AlgoAgent/Data/indicator_calculator.py`) takes the raw financial data and the (potentially updated) list of `required_indicators` to compute and append new columns for each indicator to the `pandas.DataFrame`.
5.  **Machine Learning for Optimal Indicators:** The `MLModelSelector` (`AlgoAgent/Data/ml_model_selector.py`) can optionally `train_model()` and `predict_optimal_indicators()` based on the data with computed indicators. This generates `Optimal Indicators & Parameters` which can inform future `required_indicators`.
6.  **Processed Data Output:** The final output is a `pandas.DataFrame` containing the raw financial data augmented with all calculated technical indicators.

## Logic Flow

1.  **Initialization:** An instance of `DataIngestionModel` is created, which in turn initializes instances of `ContextManager`, `DataFetcher`, `IndicatorCalculator`, `MLModelSelector`, `GeminiIntegrator`, and `DynamicCodeAdjuster`.
2.  **Ingestion Request:** The `ingest_and_process()` method of `DataIngestionModel` is called with the `ticker`, `required_indicators`, and other parameters.
3.  **Context Setting:** The `ContextManager.set_security_ticker()` and `ContextManager.set_required_indicators()` methods are used to store the current operational context.
4.  **Data Retrieval:** `DataFetcher.fetch_historical_data()` is invoked to get the raw financial data.
5.  **Dynamic Code Check:** `DataIngestionModel._check_and_update_indicator_logic()` is called.
    *   It reads the current `indicator_calculator.py` code.
    *   For each `required_indicator`, it checks if the indicator's logic is present.
    *   If not, `GeminiIntegrator.suggest_code_update()` is called to get a new code snippet.
    *   `DynamicCodeAdjuster.update_indicator_calculation_logic()` then modifies the `indicator_calculator.py` file with the new snippet.
    *   If changes were made, `indicator_calculator.py` is rewritten.
6.  **Indicator Calculation:** `IndicatorCalculator.calculate_indicators()` is called with the fetched data and the (potentially updated) list of `required_indicators`.
7.  **ML Integration (Optional):** If `ml_feature_columns` and `ml_target_column` are provided, `MLModelSelector.train_model()` and `MLModelSelector.predict_optimal_indicators()` are executed. The suggestions from the ML model can be used to refine future `required_indicators`.
8.  **Return Processed Data:** The `ingest_and_process()` method returns the `pandas.DataFrame` with all raw data and calculated indicators.

## Setup and Usage

### Prerequisites

*   Python 3.8+
*   A Google Gemini API Key

### Installation

1.  **Navigate to the project directory:**
    ```bash
    conda install -c conda-forge ta-lib
    ```

*   **Debian/Ubuntu:**
    ```bash
    sudo apt-get install build-essential python3-dev
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib/
    ./configure --prefix=/usr
    make
    sudo make install
    pip install TA-Lib
    ```

*   **macOS (using Homebrew):**
    ```bash
    brew install ta-lib
    pip install TA-Lib
    ```

## Environment Configuration

### Setting up API Keys

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file and add your API keys:**
   ```bash
   # Required for LLM integration
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   
   # Optional: Additional data sources
   # ALPHA_VANTAGE_API_KEY=your_key_here
   # QUANDL_API_KEY=your_key_here
   ```

3. **Get your Gemini API key:**
   - Visit: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
   - Create a new API key
   - Copy it to your `.env` file

### Environment Variables

The system supports these configuration options:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GEMINI_API_KEY` | Gemini API key for LLM integration | None | Optional* |
| `ML_MODEL_PATH` | Directory for ML models | `./models/` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `ENABLE_CACHE` | Enable result caching | `true` | No |
| `ENABLE_DYNAMIC_CODE` | Enable dynamic code generation | `true` | No |

*Without `GEMINI_API_KEY`, the system runs in mock mode for LLM features.

## Usage Example

```python
from AlgoAgent.Data.main import DataIngestionModel

model = DataIngestionModel()

# Example request
df = model.ingest_and_process(
    ticker="AAPL",
    required_indicators=[{"name":"RSI","timeperiod":14},{"name":"MACD","fastperiod":12,"slowperiod":26,"signalperiod":9}],
    period="60d",
    interval="1h",
)

# df will contain original OHLCV + new columns: RSI, MACD, MACD_SIGNAL, MACD_HIST
```

Observe the console output for messages regarding data fetching, indicator calculation, and any dynamic code adjustments made by Gemini.
