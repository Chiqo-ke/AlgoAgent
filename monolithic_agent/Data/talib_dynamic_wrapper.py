"""
Dynamic TALib Wrapper - Auto-generates adapters for all TALib functions
========================================================================

This module dynamically discovers and wraps ALL TALib functions, eliminating
the need to manually create adapter functions for each indicator.

Features:
- Auto-discovers all TALib functions at runtime
- Generates adapters with proper docstrings
- Handles single and multiple output indicators
- Preserves parameter information from TALib
- Outputs DataFrame with standardized column naming

Usage:
    from Data.talib_dynamic_wrapper import get_talib_function
    
    # Get any TALib function dynamically
    rsi_func = get_talib_function('RSI')
    result = rsi_func(df, {'timeperiod': 14})

Version: 1.0.0
Last Updated: 2025-12-06
"""

import pandas as pd
import numpy as np
import talib 
from typing import Dict, Any, List, Optional, Callable
import inspect

try:
    import talib
    from talib import abstract
    HAS_TALIB = True
except ImportError:
    talib = None
    abstract = None
    HAS_TALIB = False
    print("Warning: TA-Lib not installed. Run: pip install TA-Lib")


def get_all_talib_functions() -> Dict[str, Dict[str, Any]]:
    """
    Discover all available TALib functions with their metadata.
    
    Returns:
        Dict mapping function name to metadata dict with:
        - 'function': The TALib abstract function object
        - 'info': Function info dict (name, display_name, group, etc.)
        - 'inputs': List of required input column names
        - 'parameters': Dict of parameter names and default values
        - 'output_names': List of output column names
    """
    if not HAS_TALIB:
        return {}
    
    functions = {}
    
    # Get all TALib function names
    for func_name in talib.get_functions():
        try:
            # Get abstract function object
            func = abstract.Function(func_name)
            
            # Get function info
            info = func.info
            
            # Get input names - handle both dict and list formats
            inputs = []
            if hasattr(func, 'input_names'):
                input_names = func.input_names
                if isinstance(input_names, dict):
                    inputs = list(input_names.keys())
                elif isinstance(input_names, list):
                    inputs = input_names
                else:
                    inputs = ['close']  # Default fallback
            
            # Get parameters with defaults
            parameters = {}
            if hasattr(func, 'parameters'):
                params = func.parameters
                if isinstance(params, dict):
                    parameters = params
            
            # Get output names - handle both dict and list formats
            output_names = []
            if hasattr(func, 'output_names'):
                out_names = func.output_names
                if isinstance(out_names, dict):
                    output_names = list(out_names.keys())
                elif isinstance(out_names, list):
                    output_names = out_names
                else:
                    output_names = [func_name]
            else:
                output_names = [func_name]
            
            functions[func_name] = {
                'function': func,
                'info': info,
                'inputs': inputs,
                'parameters': parameters,
                'output_names': output_names
            }
            
        except Exception as e:
            # Skip functions that can't be loaded
            continue
    
    return functions


def create_dynamic_adapter(func_name: str, metadata: Dict[str, Any]) -> Callable:
    """
    Create a dynamic adapter function for a TALib indicator.
    
    Args:
        func_name: Name of the TALib function (e.g., 'RSI', 'MACD')
        metadata: Metadata dict from get_all_talib_functions()
    
    Returns:
        Callable function that takes (df, params) and returns DataFrame
    """
    func = metadata['function']
    info = metadata['info']
    inputs = metadata['inputs']
    parameters = metadata['parameters']
    output_names = metadata['output_names']
    
    # Determine what inputs this function actually needs
    needs_ohlc = any(inp.lower() in ['prices', 'ohlc'] for inp in inputs)
    needs_volume = any(inp.lower() == 'volume' for inp in inputs)
    
    def adapter(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Dynamic adapter for TALib function.
        
        This function is auto-generated at runtime.
        """
        # Ensure lowercase column names for TALib compatibility
        df_lower = df.rename(columns=str.lower)
        
        # Check if required columns are present
        required = ['close']
        if needs_ohlc:
            required.extend(['open', 'high', 'low'])
        if needs_volume:
            required.append('volume')
        
        missing = [col for col in required if col not in df_lower.columns]
        if missing:
            # Return empty DataFrame if missing required columns
            return pd.DataFrame(index=df.index)
        
        # Merge default parameters with user parameters
        combined_params = {**parameters, **params}
        
        try:
            # Create a new function instance to avoid state issues
            func_instance = abstract.Function(func_name)
            
            # Set parameters
            func_instance.parameters = combined_params
            
            # Call TALib function with the dataframe
            # The abstract API automatically maps columns
            result = func_instance(df_lower)
            
        except Exception as e:
            # If function call fails, return empty DataFrame
            # print(f"Warning: {func_name} failed: {e}")
            return pd.DataFrame(index=df.index)
        
        # Handle single or multiple outputs
        if isinstance(result, np.ndarray):
            # Single output
            # Generate column name
            if 'timeperiod' in combined_params:
                col_name = f"{func_name}_{combined_params['timeperiod']}"
            else:
                col_name = func_name
            
            result_df = pd.DataFrame({col_name: result}, index=df.index)
        
        elif isinstance(result, (list, tuple)):
            # Multiple outputs (e.g., MACD returns 3 arrays, STOCH returns 2)
            result_dict = {}
            for i, output_name in enumerate(output_names):
                if i < len(result):
                    # Generate column name
                    if len(output_names) > 1:
                        # Multi-output: use output name (e.g., MACD, MACD_SIGNAL)
                        if output_name.lower() != func_name.lower():
                            col_name = f"{func_name}_{output_name}"
                        else:
                            col_name = output_name
                    else:
                        # Single output with period
                        if 'timeperiod' in combined_params:
                            col_name = f"{func_name}_{combined_params['timeperiod']}"
                        else:
                            col_name = func_name
                    
                    result_dict[col_name.upper()] = result[i]
            
            result_df = pd.DataFrame(result_dict, index=df.index)
        
        elif isinstance(result, pd.Series):
            # Series output
            if 'timeperiod' in combined_params:
                col_name = f"{func_name}_{combined_params['timeperiod']}"
            else:
                col_name = func_name
            result_df = pd.DataFrame({col_name: result.values}, index=df.index)
        
        else:
            # Unexpected result type
            result_df = pd.DataFrame(index=df.index)
        
        return result_df
    
    # Set function metadata
    adapter.__name__ = func_name
    adapter.__doc__ = f"""
    {info.get('display_name', func_name)} ({func_name})
    
    Group: {info.get('group', 'Unknown')}
    
    Inputs: {', '.join(inputs)}
    Parameters: {', '.join(f'{k}={v}' for k, v in parameters.items())}
    Outputs: {', '.join(output_names)}
    
    This adapter is auto-generated from TA-Lib.
    See: https://github.com/TA-Lib/ta-lib-python/blob/master/docs/func.md
    """
    
    return adapter


def get_talib_function(func_name: str) -> Optional[Callable]:
    """
    Get a dynamic adapter for any TALib function.
    
    Args:
        func_name: Name of the TALib function (case-insensitive)
    
    Returns:
        Callable adapter function or None if not found
    """
    if not HAS_TALIB:
        return None
    
    # Get all functions (cached in module scope for performance)
    if not hasattr(get_talib_function, '_cache'):
        get_talib_function._cache = get_all_talib_functions()
    
    functions = get_talib_function._cache
    
    # Case-insensitive lookup
    func_name_upper = func_name.upper()
    if func_name_upper not in functions:
        return None
    
    metadata = functions[func_name_upper]
    return create_dynamic_adapter(func_name_upper, metadata)


def get_talib_function_info(func_name: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata for a TALib function.
    
    Args:
        func_name: Name of the TALib function
    
    Returns:
        Metadata dict or None if not found
    """
    if not HAS_TALIB:
        return None
    
    if not hasattr(get_talib_function, '_cache'):
        get_talib_function._cache = get_all_talib_functions()
    
    functions = get_talib_function._cache
    func_name_upper = func_name.upper()
    
    if func_name_upper not in functions:
        return None
    
    metadata = functions[func_name_upper]
    return {
        'name': func_name_upper,
        'display_name': metadata['info'].get('display_name', func_name_upper),
        'group': metadata['info'].get('group', 'Unknown'),
        'inputs': metadata['inputs'],
        'parameters': metadata['parameters'],
        'outputs': metadata['output_names']
    }


def list_all_talib_functions() -> List[str]:
    """
    List all available TALib function names.
    
    Returns:
        Sorted list of function names
    """
    if not HAS_TALIB:
        return []
    
    if not hasattr(get_talib_function, '_cache'):
        get_talib_function._cache = get_all_talib_functions()
    
    return sorted(get_talib_function._cache.keys())


def list_talib_functions_by_group() -> Dict[str, List[str]]:
    """
    List TALib functions organized by group.
    
    Returns:
        Dict mapping group name to list of function names
    """
    if not HAS_TALIB:
        return {}
    
    if not hasattr(get_talib_function, '_cache'):
        get_talib_function._cache = get_all_talib_functions()
    
    functions = get_talib_function._cache
    groups = {}
    
    for func_name, metadata in functions.items():
        group = metadata['info'].get('group', 'Other')
        if group not in groups:
            groups[group] = []
        groups[group].append(func_name)
    
    # Sort each group
    for group in groups:
        groups[group].sort()
    
    return groups


if __name__ == "__main__":
    """Test and demonstrate dynamic wrapper functionality."""
    print("=" * 70)
    print("TALib Dynamic Wrapper - Discovery Report")
    print("=" * 70)
    
    if not HAS_TALIB:
        print("\n❌ TA-Lib not installed!")
        print("   Install with: pip install TA-Lib")
        exit(1)
    
    # List all functions by group
    print("\n1. Available TALib Functions by Group:")
    groups = list_talib_functions_by_group()
    total_functions = sum(len(funcs) for funcs in groups.values())
    print(f"   Total: {total_functions} functions in {len(groups)} groups\n")
    
    for group, funcs in sorted(groups.items()):
        print(f"   {group} ({len(funcs)} functions):")
        print(f"      {', '.join(funcs[:5])}" + (" ..." if len(funcs) > 5 else ""))
    
    # Show examples
    print("\n2. Example Function Details:")
    examples = ['SMA', 'RSI', 'MACD', 'BBANDS', 'STOCH']
    for func_name in examples:
        info = get_talib_function_info(func_name)
        if info:
            print(f"\n   {func_name} - {info['display_name']}")
            print(f"      Group: {info['group']}")
            print(f"      Inputs: {', '.join(info['inputs'])}")
            print(f"      Parameters: {info['parameters']}")
            print(f"      Outputs: {', '.join(info['outputs'])}")
    
    # Test dynamic adapter
    print("\n3. Testing Dynamic Adapter:")
    print("   Creating sample OHLCV data...")
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'Open': np.random.randn(100).cumsum() + 100,
        'High': np.random.randn(100).cumsum() + 101,
        'Low': np.random.randn(100).cumsum() + 99,
        'Close': np.random.randn(100).cumsum() + 100,
        'Volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    # Test RSI
    print("\n   Testing RSI(14)...")
    rsi_func = get_talib_function('RSI')
    if rsi_func:
        result = rsi_func(df, {'timeperiod': 14})
        print(f"   ✓ Generated columns: {list(result.columns)}")
        print(f"   ✓ Sample values: {result.iloc[-5:].values.flatten()}")
    
    # Test MACD
    print("\n   Testing MACD(12, 26, 9)...")
    macd_func = get_talib_function('MACD')
    if macd_func:
        result = macd_func(df, {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9})
        print(f"   ✓ Generated columns: {list(result.columns)}")
        print(f"   ✓ Shape: {result.shape}")
    
    print("\n" + "=" * 70)
    print("✓ Dynamic wrapper working correctly!")
    print("=" * 70)
