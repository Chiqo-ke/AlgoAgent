import pandas as pd
import numpy as np

try:
    import talib
    HAS_TALIB = True
except ImportError:
    talib = None
    HAS_TALIB = False

def _ensure_dataframe_output(func):
    """Decorator to ensure indicator functions return a DataFrame."""
    def wrapper(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        if not HAS_TALIB:
            return pd.DataFrame(index=df.index) # Return empty DataFrame if TA-Lib not available

        # Ensure column names are lowercase for TA-Lib compatibility
        df_lower = df.rename(columns=str.lower)

        result = func(df_lower, params)

        # Ensure result is a DataFrame and has the same index as input
        if isinstance(result, pd.Series):
            result = result.to_frame()
        elif isinstance(result, tuple):
            # For indicators returning multiple series (e.g., MACD, STOCH, BOLLINGER)
            result = pd.concat(result, axis=1)
        
        if not isinstance(result, pd.DataFrame):
            # If it's still not a DataFrame, try to convert it
            result = pd.DataFrame(result)

        result.index = df.index
        return result
    return wrapper

@_ensure_dataframe_output
def SMA(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Simple Moving Average (SMA)"""
    timeperiod = params.get("timeperiod", 30)
    return pd.DataFrame({f"SMA_{timeperiod}": talib.SMA(df["close"], timeperiod=timeperiod)}, index=df.index)

@_ensure_dataframe_output
def EMA(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Exponential Moving Average (EMA)"""
    timeperiod = params.get("timeperiod", 30)
    return pd.DataFrame({f"EMA_{timeperiod}": talib.EMA(df["close"], timeperiod=timeperiod)}, index=df.index)

@_ensure_dataframe_output
def MACD(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Moving Average Convergence/Divergence (MACD)"""
    fastperiod = params.get("fastperiod", 12)
    slowperiod = params.get("slowperiod", 26)
    signalperiod = params.get("signalperiod", 9)
    macd, macdsignal, macdhist = talib.MACD(
        df["close"],
        fastperiod=fastperiod,
        slowperiod=slowperiod,
        signalperiod=signalperiod,
    )
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
    """Relative Strength Index (RSI)"""
    timeperiod = params.get("timeperiod", 14)
    return pd.DataFrame({f"RSI_{timeperiod}": talib.RSI(df["close"], timeperiod=timeperiod)}, index=df.index)

@_ensure_dataframe_output
def ADX(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Average Directional Movement Index (ADX)"""
    timeperiod = params.get("timeperiod", 14)
    return pd.DataFrame({f"ADX_{timeperiod}": talib.ADX(df["high"], df["low"], df["close"], timeperiod=timeperiod)}, index=df.index)

@_ensure_dataframe_output
def ATR(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Average True Range (ATR)"""
    timeperiod = params.get("timeperiod", 14)
    return pd.DataFrame({f"ATR_{timeperiod}": talib.ATR(df["high"], df["low"], df["close"], timeperiod=timeperiod)}, index=df.index)

@_ensure_dataframe_output
def BOLLINGER(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Bollinger Bands (BBANDS)"""
    timeperiod = params.get("timeperiod", 5)
    nbdevup = params.get("nbdevup", 2)
    nbdevdn = params.get("nbdevdn", 2)
    matype = params.get("matype", 0) # 0 = SMA
    upper, middle, lower = talib.BBANDS(
        df["close"],
        timeperiod=timeperiod,
        nbdevup=nbdevup,
        nbdevdn=nbdevdn,
        matype=matype,
    )
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
    """Stochastic Oscillator (STOCH)"""
    fastk_period = params.get("fastk_period", 5)
    slowk_period = params.get("slowk_period", 3)
    slowk_matype = params.get("slowk_matype", 0)
    slowd_period = params.get("slowd_period", 3)
    slowd_matype = params.get("slowd_matype", 0)
    slowk, slowd = talib.STOCH(
        df["high"],
        df["low"],
        df["close"],
        fastk_period=fastk_period,
        slowk_period=slowk_period,
        slowk_matype=slowk_matype,
        slowd_period=slowd_period,
        slowd_matype=slowd_matype,
    )
    return pd.DataFrame(
        {
            "STOCH_SLOWK": slowk,
            "STOCH_SLOWD": slowd,
        },
        index=df.index,
    )

@_ensure_dataframe_output
def OBV(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """On Balance Volume (OBV)"""
    return pd.DataFrame({"OBV": talib.OBV(df["close"], df["volume"])}, index=df.index)

@_ensure_dataframe_output
def SAR(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Parabolic SAR (SAR)"""
    acceleration = params.get("acceleration", 0.02)
    maximum = params.get("maximum", 0.2)
    return pd.DataFrame({"SAR": talib.SAR(df["high"], df["low"], acceleration=acceleration, maximum=maximum)}, index=df.index)

@_ensure_dataframe_output
def CCI(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Commodity Channel Index (CCI)"""
    timeperiod = params.get("timeperiod", 14)
    return pd.DataFrame({"CCI": talib.CCI(df["high"], df["low"], df["close"], timeperiod=timeperiod)}, index=df.index)

# VWAP is not directly available in TA-Lib. It will be implemented as a custom fallback.
# For now, we'll create a placeholder that returns an empty DataFrame if called.
@_ensure_dataframe_output
def VWAP(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Volume Weighted Average Price (VWAP) - Placeholder for TA-Lib"""
    # TA-Lib does not have a direct VWAP function. This will be handled by fallback.
    return pd.DataFrame(index=df.index)