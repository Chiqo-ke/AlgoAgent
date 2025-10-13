import pandas as pd
import numpy as np

try:
    import ta
    HAS_TA = True
except ImportError:
    ta = None
    HAS_TA = False

def _ensure_dataframe_output(func):
    """Decorator to ensure indicator functions return a DataFrame."""
    def wrapper(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        if not HAS_TA:
            return pd.DataFrame(index=df.index) # Return empty DataFrame if `ta` not available

        # Ensure column names are lowercase for `ta` compatibility if needed, or adjust as per `ta` library's expectation
        # The `ta` library typically expects 'high', 'low', 'close', 'volume'
        df_processed = df.copy()
        df_processed.columns = [col.lower() for col in df_processed.columns]

        result = func(df_processed, params)

        if isinstance(result, pd.Series):
            result = result.to_frame()
        elif isinstance(result, tuple):
            result = pd.concat(result, axis=1)
        
        if not isinstance(result, pd.DataFrame):
            result = pd.DataFrame(result)

        result.index = df.index
        return result
    return wrapper

@_ensure_dataframe_output
def SMA(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Simple Moving Average (SMA) using `ta` library."""
    timeperiod = params.get("timeperiod", 30)
    return pd.DataFrame({f"SMA_{timeperiod}": ta.trend.sma_indicator(df["close"], window=timeperiod)}, index=df.index)

@_ensure_dataframe_output
def EMA(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Exponential Moving Average (EMA) using `ta` library."""
    timeperiod = params.get("timeperiod", 30)
    return pd.DataFrame({f"EMA_{timeperiod}": ta.trend.ema_indicator(df["close"], window=timeperiod)}, index=df.index)

@_ensure_dataframe_output
def MACD(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Moving Average Convergence/Divergence (MACD) using `ta` library."""
    fastperiod = params.get("fastperiod", 12)
    slowperiod = params.get("slowperiod", 26)
    signalperiod = params.get("signalperiod", 9)
    macd = ta.trend.macd(df["close"], window_fast=fastperiod, window_slow=slowperiod)
    macdsignal = ta.trend.macd_signal(df["close"], window_fast=fastperiod, window_slow=slowperiod, window_sign=signalperiod)
    macdhist = ta.trend.macd_diff(df["close"], window_fast=fastperiod, window_slow=slowperiod, window_sign=signalperiod)
    return pd.DataFrame(
        {
            "MACD": macd,
            "MACD_SIGNAL": macdsignal,
            "MACD_HIST": macdhist,
        },
        index=df.index,
    )

@_ensure_dataframe_output
def RSI(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Relative Strength Index (RSI) using `ta` library."""
    timeperiod = params.get("timeperiod", 14)
    return pd.DataFrame({f"RSI_{timeperiod}": ta.momentum.rsi(df["close"], window=timeperiod)}, index=df.index)

@_ensure_dataframe_output
def ADX(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Average Directional Movement Index (ADX) using `ta` library."""
    timeperiod = params.get("timeperiod", 14)
    return pd.DataFrame({f"ADX_{timeperiod}": ta.trend.adx(df["high"], df["low"], df["close"], window=timeperiod)}, index=df.index)

@_ensure_dataframe_output
def ATR(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Average True Range (ATR) using `ta` library."""
    timeperiod = params.get("timeperiod", 14)
    return pd.DataFrame({f"ATR_{timeperiod}": ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=timeperiod)}, index=df.index)

@_ensure_dataframe_output
def BOLLINGER(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Bollinger Bands (BBANDS) using `ta` library."""
    timeperiod = params.get("timeperiod", 20) # `ta` default is 20, TA-Lib is 5
    window_dev = params.get("nbdevup", 2) # `ta` uses window_dev for both up/dn
    
    # `ta` library provides separate functions for high, mid, low bands
    upper = ta.volatility.bollinger_hband(df["close"], window=timeperiod, window_dev=window_dev)
    middle = ta.volatility.bollinger_mavg(df["close"], window=timeperiod, window_dev=window_dev)
    lower = ta.volatility.bollinger_lband(df["close"], window=timeperiod, window_dev=window_dev)

    return pd.DataFrame(
        {
            f"BB_UPPER_{timeperiod}": upper,
            f"BB_MIDDLE_{timeperiod}": middle,
            f"BB_LOWER_{timeperiod}": lower,
        },
        index=df.index,
    )

@_ensure_dataframe_output
def STOCH(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Stochastic Oscillator (STOCH) using `ta` library."""
    # `ta` library's stochastic functions are slightly different in parameter names
    window = params.get("fastk_period", 14) # `ta` uses 'window' for %K period
    smooth_window = params.get("slowk_period", 3) # `ta` uses 'smooth_window' for %D period
    
    stoch_k = ta.momentum.stoch(df["high"], df["low"], df["close"], window=window, smooth_window=smooth_window)
    stoch_d = ta.momentum.stoch_signal(df["high"], df["low"], df["close"], window=window, smooth_window=smooth_window, fillna=False) # `ta` has fillna param

    return pd.DataFrame(
        {
            "STOCH_SLOWK": stoch_k,
            "STOCH_SLOWD": stoch_d,
        },
        index=df.index,
    )

@_ensure_dataframe_output
def OBV(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """On Balance Volume (OBV) using `ta` library."""
    return pd.DataFrame({"OBV": ta.volume.on_balance_volume(df["close"], df["volume"])}, index=df.index)

@_ensure_dataframe_output
def SAR(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Parabolic SAR (SAR) using `ta` library."""
    # `ta` library's SAR function parameters
    initial_af = params.get("acceleration", 0.02)
    max_af = params.get("maximum", 0.2)
    return pd.DataFrame({"SAR": ta.trend.psar(df["high"], df["low"], df["close"], step=initial_af, max_step=max_af)}, index=df.index)

@_ensure_dataframe_output
def CCI(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Commodity Channel Index (CCI) using `ta` library."""
    timeperiod = params.get("timeperiod", 14)
    return pd.DataFrame({"CCI": ta.trend.cci(df["high"], df["low"], df["close"], window=timeperiod)}, index=df.index)

@_ensure_dataframe_output
def VWAP(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Volume Weighted Average Price (VWAP) - Custom implementation."""
    # `ta` library does not have a direct VWAP function that matches the signature easily.
    # Implementing a simple custom VWAP here.
    # VWAP = Cumulative(Price * Volume) / Cumulative(Volume)
    if "close" not in df.columns or "volume" not in df.columns:
        return pd.DataFrame(index=df.index)
    
    pv = df["close"] * df["volume"]
    return pd.DataFrame({"VWAP": pv.cumsum() / df["volume"].cumsum()}, index=df.index)