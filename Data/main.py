import os
import importlib
import pandas as pd
import sys
import subprocess
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import project modules
from .data_fetcher import DataFetcher
from .dynamic_code_adjuster import insert_snippet_if_missing
from .gemini_integrator import GeminiIntegrator
from .ml_model_selector import MLModelSelector

# These modules will be reloaded if code is dynamically changed
from . import ta_fallback_adapters
from . import registry
from . import indicator_calculator

class DataIngestionModel:
    def __init__(self, gemini_api_key: str = None):
        """Initialize the DataIngestionModel.
        
        Args:
            gemini_api_key: Optional API key. If not provided, will use GEMINI_API_KEY from environment.
        """
        self.data_fetcher = DataFetcher()
        # GeminiIntegrator will automatically load from environment if no key provided
        self.gemini_integrator = GeminiIntegrator(api_key=gemini_api_key)
        self.ml_model_selector = MLModelSelector()

    def ingest_and_process(self, ticker: str, required_indicators: List[Dict[str, Any]],
                           period: str = "1y", interval: str = "1d",
                           ml_feature_columns: List[str] = None, ml_target_column: str = None) -> pd.DataFrame:
        """
        Main method to ingest data, calculate indicators, and dynamically adjust code if needed.
        """
        print(f"--- Starting ingestion for {ticker} ---")
        
        # 1. Fetch Data
        print(f"Fetching data for {ticker}...")
        df = self.data_fetcher.fetch_historical_data(ticker, period=period, interval=interval)
        if df.empty:
            print(f"Failed to fetch data for {ticker}. Aborting.")
            return pd.DataFrame()

        # 2. Check for missing indicators and update code dynamically
        code_was_changed = self._check_and_update_indicators(required_indicators)

        if code_was_changed:
            print("Code was changed, reloading modules...")
            try:
                importlib.reload(ta_fallback_adapters)
                importlib.reload(registry)
                importlib.reload(indicator_calculator)
                print("Modules reloaded successfully.")
            except Exception as e:
                print(f"FATAL: Failed to reload modules after code change: {e}")
                print("The application might be in an unstable state.")
                return df # Return original df without indicators

        # 3. Compute Indicators
        print("Calculating technical indicators...")
        final_df = df.copy()
        for indicator_spec in required_indicators:
            name = indicator_spec['name']
            params = {k: v for k, v in indicator_spec.items() if k != 'name'}
            try:
                result_df, metadata = indicator_calculator.compute_indicator(name, final_df, params)
                print(f"  - Computed {name} (source: {metadata['source_hint']}) with params: {metadata['params']}")
                final_df = pd.concat([final_df, result_df], axis=1)
            except Exception as e:
                print(f"  - FAILED to compute {name}: {e}")

        # 4. ML Model Training and Suggestion
        if ml_feature_columns and ml_target_column:
            print("\nRunning ML model selector...")
            self.ml_model_selector.train_model(final_df, ml_target_column, ml_feature_columns)
            suggestions = self.ml_model_selector.suggest_indicators(k=3)
            print(f"\nTop 3 suggested indicators from ML model: {suggestions}")

        print(f"--- Ingestion for {ticker} complete. ---")
        return final_df

    def _check_and_update_indicators(self, required_indicators: List[Dict[str, Any]]) -> bool:
        """Checks for missing indicators, and attempts to dynamically add them."""
        any_code_changed = False
        ADAPTER_FILE_PATH = os.path.abspath(ta_fallback_adapters.__file__)

        for indicator_spec in required_indicators:
            indicator_name = indicator_spec['name']
            try:
                indicator_calculator.describe_indicator(indicator_name)
                print(f"Indicator '{indicator_name}' is already registered.")
            except ValueError:
                print(f"Indicator '{indicator_name}' not found. Attempting to generate it...")
                
                # 1. Get snippet from Gemini
                snippet = self.gemini_integrator.suggest_code_update(indicator_name)
                if not snippet or snippet.startswith("#"):
                    print(f"Could not get a valid snippet for {indicator_name}. Skipping.")
                    continue

                # 2. Save original file content
                with open(ADAPTER_FILE_PATH, 'r') as f:
                    original_content = f.read()

                # 3. Insert the new snippet
                print(f"Inserting snippet for {indicator_name} into {os.path.basename(ADAPTER_FILE_PATH)}...")
                changed = insert_snippet_if_missing(ADAPTER_FILE_PATH, indicator_name, snippet)
                if not changed:
                    print("Insertion failed, snippet might already exist.")
                    continue

                # 4. Run tests to verify the change
                print("Running tests to verify the new code...")
                # Use sys.executable to be platform-agnostic
                pytest_command = [sys.executable, "-m", "pytest", "Data/tests/"]
                print(f"Running command: {' '.join(pytest_command)}")
                test_result = subprocess.run(
                    pytest_command, capture_output=True, text=True, check=False
                )
                
                if test_result.returncode == 0:
                    print("Tests passed! The new indicator is safe to use.")
                    any_code_changed = True
                else:
                    print("ERROR: Tests failed after adding the new indicator snippet!")
                    print(test_result.stdout)
                    print(test_result.stderr)
                    print("Reverting changes to the adapter file.")
                    with open(ADAPTER_FILE_PATH, 'w') as f:
                        f.write(original_content)
                    print("Changes reverted.")
        
        return any_code_changed

if __name__ == "__main__":
    # This example demonstrates the full workflow.
    try:
        model = DataIngestionModel()

        # Define indicators. 'VIX' does not exist and will trigger the dynamic workflow.
        required = [
            {'name': 'SMA', 'timeperiod': 20},
            {'name': 'RSI', 'timeperiod': 14},
            {'name': 'VIX', 'timeperiod': 14} # This will be dynamically added
        ]

        processed_df = model.ingest_and_process(
            ticker="AAPL",
            required_indicators=required,
            period="60d",
            interval="1d",
        )

        if not processed_df.empty:
            print("\n--- Final Processed DataFrame ---" )
            print(processed_df.head())
            print("\n")
            print(processed_df.tail())

    except Exception as e:
        print(f"\nAn unexpected error occurred during the main execution: {e}")