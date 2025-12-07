"""
This module provides the core functions for the hybrid indicator service.
"""
import pandas as pd
from typing import Dict, Any
from . import registry

def validate_inputs(df: pd.DataFrame, required_columns: list[str]):
    """
    Validates that the input DataFrame has the required columns.

    Args:
        df (pd.DataFrame): The DataFrame to validate.
        required_columns (list[str]): A list of required column names.

    Raises:
        ValueError: If any of the required columns are missing.
    """
    df_columns_lower = [c.lower() for c in df.columns]
    
    missing_columns = []
    for col in required_columns:
        col_lower = col.lower()
        
        # For dynamic TALib indicators, map abstract names to actual columns
        if col_lower in ['price', 'real', 'real0', 'real1']:
            # Single price series - check for 'close'
            if 'close' not in df_columns_lower:
                missing_columns.append(col_lower)
        elif col_lower in ['prices', 'ohlc']:
            # OHLC data - check for open, high, low, close
            required_ohlc = ['open', 'high', 'low', 'close']
            if not all(c in df_columns_lower for c in required_ohlc):
                missing_columns.append(col_lower)
        elif col_lower not in df_columns_lower:
            # Standard column name check
            missing_columns.append(col_lower)
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

def compute_indicator(name: str, df: pd.DataFrame, params: Dict[str, Any] = None) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Computes a technical indicator using the registered implementation.

    Args:
        name (str): The name of the indicator (case-insensitive).
        df (pd.DataFrame): A DataFrame with a DatetimeIndex and columns: Open, High, Low, Close, Volume.
        params (Dict[str, Any], optional): A dictionary of parameters for the indicator.

    Returns:
        A tuple containing:
        - pd.DataFrame: A DataFrame with the computed indicator values.
        - Dict[str, Any]: Metadata about the computation (source, params, etc.).
    """
    entry = registry.get_entry(name)
    if not entry:
        raise ValueError(f"Indicator '{name}' not registered.")

    # Combine user-provided params with defaults
    combined_params = {**entry['defaults'], **(params or {})}

    # Validate that the input DataFrame has the required columns
    validate_inputs(df, entry['inputs'])

    # Call the indicator function
    result_df = entry['callable'](df, combined_params)

    metadata = {
        "source_hint": entry['source_hint'],
        "params": combined_params,
        "outputs": list(result_df.columns),
    }
    return result_df, metadata

def describe_indicator(name: str) -> Dict[str, Any]:
    """
    Describes a registered technical indicator.

    Args:
        name (str): The name of the indicator (case-insensitive).

    Returns:
        A dictionary containing metadata about the indicator.
    """
    entry = registry.get_entry(name)
    if not entry:
        raise ValueError(f"Indicator '{name}' not registered.")

    return {
        "inputs": entry["inputs"],
        "outputs": entry["outputs"],
        "defaults": entry["defaults"],
        "source_hint": entry["source_hint"],
    }
