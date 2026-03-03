"""
Indicator management for TradingView scraper  
"""

from typing import Dict, List, Optional


class IndicatorManager:
    """
    Manages TradingView indicators including names, parameters, and configurations.
    """
    
    # Common TradingView indicators and their typical parameters
    INDICATORS = {
        "EMA": {
            "name": "Moving Average Exponential",
            "default_params": {"length": 9},
            "param_types": {"length": int}
        },
        "SMA": {
            "name": "Moving Average",
            "default_params": {"length": 20},
            "param_types": {"length": int}
        },
        "RSI": {
            "name": "Relative Strength Index",
            "default_params": {"length": 14},
            "param_types": {"length": int}
        },
        "MACD": {
            "name": "MACD",
            "default_params": {
                "fast_length": 12,
                "slow_length": 26,
                "signal_length": 9
            },
            "param_types": {
                "fast_length": int,
                "slow_length": int,
                "signal_length": int
            }
        },
        "BB": {
            "name": "Bollinger Bands",
            "default_params": {
                "length": 20,
                "std_dev": 2
            },
            "param_types": {
                "length": int,
                "std_dev": float
            }
        },
        "ATR": {
            "name": "Average True Range",
            "default_params": {"length": 14},
            "param_types": {"length": int}
        },
        "Stochastic": {
            "name": "Stochastic",
            "default_params": {
                "k_length": 14,
                "k_smoothing": 3,
                "d_smoothing": 3
            },
            "param_types": {
                "k_length": int,
                "k_smoothing": int,
                "d_smoothing": int
            }
        },
        "Volume": {
            "name": "Volume",
            "default_params": {},
            "param_types": {}
        }
    }
    
    @classmethod
    def get_indicator_info(cls, indicator_name: str) -> Optional[Dict]:
        """
        Get information about an indicator.
        
        Args:
            indicator_name: Short name of the indicator
            
        Returns:
            Dict with indicator info or None if not found
        """
        return cls.INDICATORS.get(indicator_name)
    
    @classmethod
    def validate_parameters(cls, indicator_name: str, parameters: Dict) -> bool:
        """
        Validate indicator parameters.
        
        Args:
            indicator_name: Short name of the indicator
            parameters: Dict of parameter values
            
        Returns:
            True if valid, False otherwise
        """
        info = cls.get_indicator_info(indicator_name)
        if not info:
            return False
        
        param_types = info.get("param_types", {})
        
        for key, value in parameters.items():
            if key not in param_types:
                print(f"Unknown parameter: {key}")
                return False
            
            expected_type = param_types[key]
            if not isinstance(value, expected_type):
                print(f"Parameter {key} should be {expected_type.__name__}, got {type(value).__name__}")
                return False
        
        return True
    
    @classmethod
    def get_default_parameters(cls, indicator_name: str) -> Dict:
        """
        Get default parameters for an indicator.
        
        Args:
            indicator_name: Short name of the indicator
            
        Returns:
            Dict of default parameters
        """
        info = cls.get_indicator_info(indicator_name)
        return info.get("default_params", {}) if info else {}
    
    @classmethod
    def merge_parameters(cls, indicator_name: str, custom_params: Optional[Dict] = None) -> Dict:
        """
        Merge custom parameters with defaults.
        
        Args:
            indicator_name: Short name of the indicator
            custom_params: Optional custom parameters
            
        Returns:
            Merged parameter dict
        """
        defaults = cls.get_default_parameters(indicator_name)
        if not custom_params:
            return defaults
        
        merged = defaults.copy()
        merged.update(custom_params)
        
        return merged
    
    @classmethod
    def list_indicators(cls) -> List[str]:
        """
        Get a list of all available indicators.
        
        Returns:
            List of indicator short names
        """
        return list(cls.INDICATORS.keys())
    
    @classmethod
    def format_indicator_name(cls, indicator_name: str) -> str:
        """
        Get the full TradingView name for an indicator.
        
        Args:
            indicator_name: Short name of the indicator
            
        Returns:
            Full indicator name as used in TradingView
        """
        info = cls.get_indicator_info(indicator_name)
        return info.get("name", indicator_name) if info else indicator_name
