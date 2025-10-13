# Dynamic Data Ingestion Model for Financial Securities

## Overview

This project implements a dynamic data ingestion model for financial securities, featuring a hybrid indicator service that leverages TA-Lib for performance and a pure-Python fallback for portability. It also includes modules for data fetching, dynamic code adjustment, Gemini integration, and machine learning model selection.

## Installation

### Quick Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/Chiqo-ke/AlgoAgent.git
cd AlgoAgent

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Run automated setup
python setup.py
```

The setup script will:
- ✅ Validate file structure
- ✅ Install required dependencies  
- ✅ Create `.env` file from template
- ✅ Run basic functionality tests

### Manual Installation

1. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # macOS/Linux: source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r Data/requirements.txt
   ```

3. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

## Optional: TA-Lib Installation

TA-Lib is a high-performance technical analysis library written in C. Its Python wrapper provides significant speed advantages for indicator calculations. Installation requires the C library to be present on your system.

**Reference:** [https://github.com/TA-Lib/ta-lib-python](https://github.com/TA-Lib/ta-lib-python)

### Platform-specific instructions:

*   **Windows:**
    1.  Download the TA-Lib C library from [http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-msvc.zip](http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-msvc.zip).
    2.  Unzip the file to `C:\ta-lib`.
    3.  Add `C:\ta-lib\bin` to your system's PATH environment variable.
    4.  Install the Python wrapper: `pip install TA-Lib`

*   **Conda (Windows, macOS, Linux):**
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

## API Contracts

### `compute_indicator(name, df, params=None)`

*   **Input:**
    *   `name` (str): The name of the indicator (e.g., "RSI", "MACD").
    *   `df` (pandas.DataFrame): A DataFrame with a DatetimeIndex and columns: `Open`, `High`, `Low`, `Close`, `Volume`.
    *   `params` (dict, optional): A dictionary of parameters specific to the indicator (e.g., `{'timeperiod': 14}`).
*   **Output:**
    *   `(result_df, metadata)`:
        *   `result_df` (pandas.DataFrame): A DataFrame with the same index as the input `df` and new columns containing the computed indicator values.
        *   `metadata` (dict): A dictionary containing:
            *   `'source_hint'` (str): Indicates the implementation used (`'talib'`, `'ta'`, or `'custom'`).
            *   `'params'` (dict): The actual parameters used for the computation (including defaults).
            *   `'version'` (str): The version of the library used (if applicable).

### `describe_indicator(name)`

*   **Input:**
    *   `name` (str): The name of the indicator.
*   **Output:**
    *   `dict`: A dictionary containing metadata about the indicator, such as:
        *   `'inputs'` (list): Required input columns (e.g., `['close']`).
        *   `'outputs'` (list): Names of the output columns generated by the indicator.
        *   `'defaults'` (dict): Default parameters for the indicator.
        *   `'notes'` (str): Any additional notes or descriptions.
