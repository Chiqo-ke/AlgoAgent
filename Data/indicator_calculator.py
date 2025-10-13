# AlgoAgent/Data/indicator_calculator.py

import talib
import pandas as pd
import numpy as np

class IndicatorCalculator:
    def __init__(self):
        pass

    def calculate_indicators(self, data: pd.DataFrame, indicators: list) -> pd.DataFrame:
        """
        Calculates a list of technical indicators for the given financial data.

        Args:
            data (pd.DataFrame): DataFrame containing financial data (must have 'Open', 'High', 'Low', 'Close', 'Volume' columns).
            indicators (list): A list of dictionaries, where each dictionary specifies an indicator
                                and its parameters.
                                Example: [{'name': 'SMA', 'timeperiod': 20},
                                          {'name': 'RSI', 'timeperiod': 14}]

        Returns:
            pd.DataFrame: The original DataFrame with calculated indicators added as new columns.
        """
        if data.empty:
            return data

        df = data.copy()

        for indicator_spec in indicators:
            indicator_name = indicator_spec['name'].upper()
            params = {k: v for k, v in indicator_spec.items() if k != 'name'}

            try:
                # TA-Lib functions typically expect numpy arrays
                if indicator_name == 'SMA':
                    df[f'SMA_{params["timeperiod"]}'] = talib.SMA(df['Close'].values, **params)
                elif indicator_name == 'EMA':
                    df[f'EMA_{params["timeperiod"]}'] = talib.EMA(df['Close'].values, **params)
                elif indicator_name == 'RSI':
                    df[f'RSI_{params["timeperiod"]}'] = talib.RSI(df['Close'].values, **params)
                elif indicator_name == 'MACD':
                    macd, macdsignal, macdhist = talib.MACD(df['Close'].values,
                                                            fastperiod=params.get('fastperiod', 12),
                                                            slowperiod=params.get('slowperiod', 26),
                                                            signalperiod=params.get('signalperiod', 9))
                    df['MACD'] = macd
                    df['MACD_Signal'] = macdsignal
                    df['MACD_Hist'] = macdhist
                elif indicator_name == 'BBANDS':
                    upper, middle, lower = talib.BBANDS(df['Close'].values,
                                                        timeperiod=params.get('timeperiod', 20),
                                                        nbdevup=params.get('nbdevup', 2),
                                                        nbdevdn=params.get('nbdevdn', 2),
                                                        matype=params.get('matype', 0))
                    df['BBANDS_Upper'] = upper
                    df['BBANDS_Middle'] = middle
                    df['BBANDS_Lower'] = lower
                elif indicator_name == 'ADX':
                    df[f'ADX_{params["timeperiod"]}'] = talib.ADX(df['High'].values, df['Low'].values, df['Close'].values, **params)
                elif indicator_name == 'STOCH':
                    slowk, slowd = talib.STOCH(df['High'].values, df['Low'].values, df['Close'].values,
                                               fastk_period=params.get('fastk_period', 5),
                                               slowk_period=params.get('slowk_period', 3),
                                               slowk_matype=params.get('slowk_matype', 0),
                                               slowd_period=params.get('slowd_period', 3),
                                               slowd_matype=params.get('slowd_matype', 0))
                    df['STOCH_SlowK'] = slowk
                    df['STOCH_SlowD'] = slowd
                # Add more indicators as needed
                else:
                    print(f"Warning: Indicator {indicator_name} not implemented or recognized.")

            except Exception as e:
                print(f"Error calculating {indicator_name}: {e}")
        return df

if __name__ == "__main__":
    # Create dummy data for demonstration
    data = {
        'Open': np.random.rand(100) * 100,
        'High': np.random.rand(100) * 100 + 1,
        'Low': np.random.rand(100) * 100 - 1,
        'Close': np.random.rand(100) * 100,
        'Volume': np.random.randint(100000, 1000000, 100)
    }
    df = pd.DataFrame(data)
    df.index = pd.to_datetime(pd.date_range(start='2023-01-01', periods=100, freq='D'))

    calculator = IndicatorCalculator()

    # Define indicators to calculate
    required_indicators = [
        {'name': 'SMA', 'timeperiod': 20},
        {'name': 'EMA', 'timeperiod': 10},
        {'name': 'RSI', 'timeperiod': 14},
        {'name': 'MACD'},
        {'name': 'BBANDS', 'timeperiod': 20, 'nbdevup': 2, 'nbdevdn': 2},
        {'name': 'ADX', 'timeperiod': 14},
        {'name': 'STOCH', 'fastk_period': 5, 'slowk_period': 3, 'slowd_period': 3}
    ]

    df_with_indicators = calculator.calculate_indicators(df, required_indicators)
    print("DataFrame with indicators:")
    print(df_with_indicators.head())
    print(df_with_indicators.tail())