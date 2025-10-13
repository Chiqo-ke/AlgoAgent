# AlgoAgent/Data/gemini_integrator.py

import google.generativeai as genai
import os
import re

class GeminiIntegrator:
    def __init__(self, api_key: str = None):
        if api_key:
            genai.configure(api_key=api_key)
        else:
            # Attempt to get API key from environment variable
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
            else:
                raise ValueError("Gemini API key not provided and not found in environment variables (GEMINI_API_KEY).")

        self.model = genai.GenerativeModel('gemini-pro')

    def get_talib_indicator_info(self, indicator_name: str) -> str:
        """
        Uses Gemini to fetch information about a specific TA-Lib indicator.

        Args:
            indicator_name (str): The name of the TA-Lib indicator (e.g., "SMA", "RSI").

        Returns:
            str: A string containing information about the indicator, its parameters, and usage.
        """
        prompt = f"Provide detailed information about the TA-Lib indicator '{indicator_name}', including its purpose, common parameters, and how it's typically used in financial analysis. Also, mention the expected input series (e.g., 'close', 'high', 'low') and output."
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error fetching TA-Lib info for {indicator_name} from Gemini: {e}")
            return f"Could not retrieve information for {indicator_name}."

    def suggest_code_update(self, current_code: str, required_indicator_spec: dict) -> str:
        """
        Uses Gemini to suggest code updates for the indicator_calculator.py file
        to include a new or updated indicator.

        Args:
            current_code (str): The current content of the indicator_calculator.py file.
            required_indicator_spec (dict): A dictionary specifying the new/updated indicator
                                            and its parameters.
                                            Example: {'name': 'ADX', 'timeperiod': 14}

        Returns:
            str: Suggested code snippet to be inserted or a full updated file content.
        """
        indicator_name = required_indicator_spec['name'].upper()
        params_str = ", ".join([f"{k}={v}" for k, v in required_indicator_spec.items() if k != 'name'])

        prompt = f"""
        Given the following Python code from `indicator_calculator.py`:

        ```python
        {current_code}
        ```

        I need to add or update the calculation for the TA-Lib indicator '{indicator_name}' with parameters '{params_str}'.
        Please provide ONLY the Python code snippet that should be inserted or modified within the `calculate_indicators` method's `if/elif` block to handle this indicator.
        Ensure the snippet correctly uses `talib.{indicator_name}` and adds the result to the DataFrame `df`.
        If the indicator already exists, provide the updated block. If not, provide a new `elif` block.
        Do not include any surrounding text, explanations, or full file content, just the code snippet.
        """
        try:
            response = self.model.generate_content(prompt)
            # Gemini might return markdown code block, extract just the code
            code_snippet = re.search(r"```python\n(.*?)```", response.text, re.DOTALL)
            if code_snippet:
                return code_snippet.group(1).strip()
            return response.text.strip()
        except Exception as e:
            print(f"Error suggesting code update for {indicator_name} from Gemini: {e}")
            return f"# Error: Could not suggest code for {indicator_name}"

if __name__ == "__main__":
    # This part requires a valid GEMINI_API_KEY set in your environment variables
    # or passed directly to the constructor.
    # For demonstration, we'll use a dummy key if not set, but it won't work.
    try:
        gemini_integrator = GeminiIntegrator()

        # Example 1: Get info about an indicator
        rsi_info = gemini_integrator.get_talib_indicator_info("RSI")
        print("\nRSI Indicator Info:")
        print(rsi_info)

        # Example 2: Suggest code update (requires a dummy current_code)
        dummy_current_code = """
import talib
import pandas as pd
import numpy as np

class IndicatorCalculator:
    def __init__(self):
        pass

    def calculate_indicators(self, data: pd.DataFrame, indicators: list) -> pd.DataFrame:
        if data.empty:
            return data
        df = data.copy()
        for indicator_spec in indicators:
            indicator_name = indicator_spec['name'].upper()
            params = {k: v for k, v in indicator_spec.items() if k != 'name'}
            try:
                if indicator_name == 'SMA':
                    df[f'SMA_{params["timeperiod"]}'] = talib.SMA(df['Close'].values, **params)
                # Placeholder for other indicators
            except Exception as e:
                print(f"Error calculating {indicator_name}: {e}")
        return df
"""
        new_indicator_spec = {'name': 'ADX', 'timeperiod': 14}
        suggested_adx_code = gemini_integrator.suggest_code_update(dummy_current_code, new_indicator_spec)
        print("\nSuggested ADX Code Update:")
        print(suggested_adx_code)

    except ValueError as e:
        print(f"Initialization error: {e}")
        print("Please set the GEMINI_API_KEY environment variable or pass it to the constructor.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")