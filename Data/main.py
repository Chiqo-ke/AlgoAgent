# AlgoAgent/Data/main.py

import pandas as pd
from typing import List, Dict, Any
import os

from .data_fetcher import DataFetcher
from .indicator_calculator import IndicatorCalculator
from .ml_model_selector import MLModelSelector
from .gemini_integrator import GeminiIntegrator
from .dynamic_code_adjuster import DynamicCodeAdjuster
from .context_manager import ContextManager

class DataIngestionModel:
    def __init__(self, gemini_api_key: str = None):
        self.context_manager = ContextManager()
        self.data_fetcher = DataFetcher()
        self.indicator_calculator = IndicatorCalculator()
        self.ml_model_selector = MLModelSelector()
        self.dynamic_code_adjuster = DynamicCodeAdjuster()
        self.gemini_integrator = GeminiIntegrator(api_key=gemini_api_key)

    def _check_and_update_indicator_logic(self, required_indicators: List[Dict[str, Any]]):
        """
        Checks if all required indicators are implemented in indicator_calculator.py
        and uses Gemini to suggest code updates if necessary.
        """
        current_calculator_code = self._read_indicator_calculator_code()
        updated_code = current_calculator_code

        for indicator_spec in required_indicators:
            indicator_name = indicator_spec['name'].upper()
            # Simple check: see if the indicator name is present in the code
            if f"elif indicator_name == '{indicator_name}'" not in updated_code and \
               f"if indicator_name == '{indicator_name}'" not in updated_code:
                print(f"Indicator '{indicator_name}' not found in indicator_calculator.py. Requesting Gemini for code snippet...")
                snippet = self.gemini_integrator.suggest_code_update(current_calculator_code, indicator_spec)
                if snippet and "# Error" not in snippet:
                    print(f"Gemini suggested snippet for {indicator_name}:\n{snippet}")
                    updated_code = self.dynamic_code_adjuster.update_indicator_calculation_logic(updated_code, snippet)
                    print(f"Code for {indicator_name} dynamically adjusted.")
                else:
                    print(f"Could not get a valid code snippet for {indicator_name} from Gemini.")
            else:
                print(f"Indicator '{indicator_name}' already implemented.")
        
        if updated_code != current_calculator_code:
            self._write_indicator_calculator_code(updated_code)
            print("indicator_calculator.py updated with new indicator logic.")

    def _read_indicator_calculator_code(self) -> str:
        """Reads the current content of the indicator_calculator.py file."""
        file_path = os.path.join(os.path.dirname(__file__), 'indicator_calculator.py')
        with open(file_path, 'r') as f:
            return f.read()

    def _write_indicator_calculator_code(self, content: str):
        """Writes the updated content to the indicator_calculator.py file."""
        file_path = os.path.join(os.path.dirname(__file__), 'indicator_calculator.py')
        with open(file_path, 'w') as f:
            f.write(content)

    def ingest_and_process(self, ticker: str, required_indicators: List[Dict[str, Any]],
                           period: str = "1y", interval: str = "1d",
                           ml_feature_columns: List[str] = None, ml_target_column: str = None) -> pd.DataFrame:
        """
        Main method to ingest data, calculate indicators, and dynamically adjust.

        Args:
            ticker (str): The financial security ticker.
            required_indicators (List[Dict[str, Any]]): List of indicators to calculate.
            period (str): Data fetching period.
            interval (str): Data fetching interval.
            ml_feature_columns (List[str]): Columns to use as features for ML model.
            ml_target_column (str): Target column for ML model.

        Returns:
            pd.DataFrame: DataFrame with raw data and calculated indicators.
        """
        self.context_manager.set_security_ticker(ticker)
        self.context_manager.set_required_indicators(required_indicators)
        self.context_manager.set_context('data_period', period)
        self.context_manager.set_context('data_interval', interval)

        print(f"Fetching data for {ticker}...")
        data = self.data_fetcher.fetch_historical_data(ticker, period=period, interval=interval)
        if data.empty:
            print(f"Failed to fetch data for {ticker}. Aborting.")
            return pd.DataFrame()

        print("Checking and updating indicator calculation logic...")
        self._check_and_update_indicator_logic(required_indicators)

        print("Calculating technical indicators...")
        df_with_indicators = self.indicator_calculator.calculate_indicators(data, required_indicators)

        if ml_feature_columns and ml_target_column:
            print("Training/Predicting with ML model for optimal indicators...")
            # For demonstration, we'll train and then predict. In a real scenario,
            # training might happen less frequently.
            self.ml_model_selector.train_model(df_with_indicators.dropna(), ml_target_column, ml_feature_columns)
            optimal_suggestions = self.ml_model_selector.predict_optimal_indicators(df_with_indicators, ml_feature_columns)
            print("ML Model Suggestions:", optimal_suggestions)
            # Here, you would integrate logic to potentially adjust `required_indicators`
            # based on `optimal_suggestions` and re-run indicator calculation if needed.

        print("Data ingestion and processing complete.")
        return df_with_indicators

if __name__ == "__main__":
    # Ensure you have your Gemini API key set as an environment variable: GEMINI_API_KEY
    # or pass it directly: DataIngestionModel(gemini_api_key="YOUR_API_KEY")
    try:
        model = DataIngestionModel()

        # Define initial indicators
        initial_indicators = [
            {'name': 'SMA', 'timeperiod': 20},
            {'name': 'RSI', 'timeperiod': 14},
            {'name': 'MACD'}
        ]

        # Define ML parameters (example)
        ml_features = ['SMA_20', 'RSI_14', 'MACD'] # These should match indicator outputs
        # Create a dummy target for ML training: 1 if next day's close is higher, 0 otherwise
        # This needs to be generated on the fly or pre-calculated in the data.
        # For this example, we'll assume a 'Future_Direction' column exists after data fetching.
        # In a real scenario, you'd add this target creation logic.
        ml_target = 'Future_Direction'

        print("--- First Ingestion Run (AAPL) ---")
        processed_aapl_data = model.ingest_and_process(
            ticker="AAPL",
            required_indicators=initial_indicators,
            period="1y",
            interval="1d",
            ml_feature_columns=ml_features,
            ml_target_column=ml_target
        )
        if not processed_aapl_data.empty:
            print("\nProcessed AAPL Data Head:")
            print(processed_aapl_data.head())
            print("\nProcessed AAPL Data Tail:")
            print(processed_aapl_data.tail())

        # Simulate adding a new indicator dynamically
        print("\n--- Second Ingestion Run (GOOG) with a new indicator (ADX) ---")
        new_indicators_for_goog = [
            {'name': 'SMA', 'timeperiod': 20},
            {'name': 'RSI', 'timeperiod': 14},
            {'name': 'MACD'},
            {'name': 'ADX', 'timeperiod': 14} # New indicator
        ]
        processed_goog_data = model.ingest_and_process(
            ticker="GOOG",
            required_indicators=new_indicators_for_goog,
            period="6mo",
            interval="1d",
            ml_feature_columns=ml_features, # Re-using for simplicity, but should be updated
            ml_target_column=ml_target
        )
        if not processed_goog_data.empty:
            print("\nProcessed GOOG Data Head:")
            print(processed_goog_data.head())
            print("\nProcessed GOOG Data Tail:")
            print(processed_goog_data.tail())

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during main execution: {e}")