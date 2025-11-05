"""
Fixture Management System

Provides deterministic test data for reproducible strategy testing.
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random


class FixtureManager:
    """
    Manages deterministic test fixtures for strategy backtesting.
    
    Fixture Types:
    1. OHLCV Data: Historical price data
    2. Indicator Expected Values: Known good indicator outputs
    3. Entry Scenarios: Test cases for entry logic
    4. Exit Scenarios: Test cases for exit logic
    """
    
    def __init__(self, fixtures_dir: Path = Path("fixtures")):
        """
        Initialize fixture manager.
        
        Args:
            fixtures_dir: Directory to store fixtures
        """
        self.fixtures_dir = Path(fixtures_dir)
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)
    
    def create_ohlcv_fixture(
        self,
        symbol: str,
        num_bars: int = 30,
        seed: int = 42
    ) -> Path:
        """
        Create deterministic OHLCV data fixture.
        
        Args:
            symbol: Stock symbol
            num_bars: Number of bars to generate
            seed: Random seed for determinism
            
        Returns:
            Path to created CSV file
        """
        random.seed(seed)
        
        # Generate realistic price data
        data = []
        base_price = 100.0
        current_price = base_price
        
        start_date = datetime(2024, 1, 1)
        
        for i in range(num_bars):
            date = start_date + timedelta(days=i)
            
            # Random walk with drift
            change_pct = random.gauss(0.001, 0.02)  # Mean 0.1% drift, 2% volatility
            current_price *= (1 + change_pct)
            
            # Generate OHLCV
            open_price = current_price
            high_price = current_price * (1 + abs(random.gauss(0, 0.01)))
            low_price = current_price * (1 - abs(random.gauss(0, 0.01)))
            close_price = random.uniform(low_price, high_price)
            volume = int(random.gauss(1000000, 200000))
            
            data.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Open': round(open_price, 2),
                'High': round(high_price, 2),
                'Low': round(low_price, 2),
                'Close': round(close_price, 2),
                'Volume': volume
            })
            
            current_price = close_price
        
        # Save to CSV
        filepath = self.fixtures_dir / f"sample_{symbol.lower()}.csv"
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            writer.writeheader()
            writer.writerows(data)
        
        print(f"[Fixtures] Created OHLCV fixture: {filepath}")
        return filepath
    
    def create_indicator_fixture(
        self,
        indicator_name: str,
        test_cases: List[Dict[str, Any]]
    ) -> Path:
        """
        Create fixture for indicator expected values.
        
        Args:
            indicator_name: Name of indicator (e.g., 'rsi', 'macd')
            test_cases: List of test case dicts with input and expected output
            
        Example test_case:
            {
                "name": "test_rsi_oversold",
                "input": {"prices": [44, 44.34, 44.09, 43.61, 44.33], "period": 14},
                "expected": {"rsi": 30.5}
            }
            
        Returns:
            Path to created JSON file
        """
        filepath = self.fixtures_dir / f"{indicator_name}_expected.json"
        
        fixture = {
            "indicator": indicator_name,
            "version": "1.0",
            "test_cases": test_cases
        }
        
        with open(filepath, 'w') as f:
            json.dump(fixture, f, indent=2)
        
        print(f"[Fixtures] Created indicator fixture: {filepath}")
        return filepath
    
    def create_entry_scenarios_fixture(
        self,
        scenarios: List[Dict[str, Any]]
    ) -> Path:
        """
        Create fixture for entry condition testing.
        
        Args:
            scenarios: List of entry test scenarios
            
        Example scenario:
            {
                "name": "rsi_oversold_entry",
                "description": "Should enter when RSI < 30",
                "bar": {"date": "2024-01-15", "close": 95.0},
                "indicators": {"rsi": 28},
                "position": None,
                "expected_entry": True
            }
            
        Returns:
            Path to created JSON file
        """
        filepath = self.fixtures_dir / "entry_scenarios.json"
        
        fixture = {
            "version": "1.0",
            "scenarios": scenarios
        }
        
        with open(filepath, 'w') as f:
            json.dump(fixture, f, indent=2)
        
        print(f"[Fixtures] Created entry scenarios fixture: {filepath}")
        return filepath
    
    def create_exit_scenarios_fixture(
        self,
        scenarios: List[Dict[str, Any]]
    ) -> Path:
        """
        Create fixture for exit condition testing.
        
        Args:
            scenarios: List of exit test scenarios
            
        Example scenario:
            {
                "name": "stop_loss_exit",
                "description": "Should exit when price drops 5%",
                "bar": {"date": "2024-01-15", "close": 95.0},
                "indicators": {"rsi": 45},
                "position": {"entry_price": 100.0, "shares": 10},
                "expected_exit": True,
                "exit_reason": "stop_loss"
            }
            
        Returns:
            Path to created JSON file
        """
        filepath = self.fixtures_dir / "exit_scenarios.json"
        
        fixture = {
            "version": "1.0",
            "scenarios": scenarios
        }
        
        with open(filepath, 'w') as f:
            json.dump(fixture, f, indent=2)
        
        print(f"[Fixtures] Created exit scenarios fixture: {filepath}")
        return filepath
    
    def load_fixture(self, filename: str) -> Any:
        """
        Load a fixture file.
        
        Args:
            filename: Fixture filename
            
        Returns:
            Loaded fixture data (dict for JSON, list for CSV)
        """
        filepath = self.fixtures_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Fixture not found: {filepath}")
        
        if filepath.suffix == '.json':
            with open(filepath, 'r') as f:
                return json.load(f)
        
        elif filepath.suffix == '.csv':
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                return list(reader)
        
        else:
            raise ValueError(f"Unsupported fixture format: {filepath.suffix}")


# Example usage and CLI
def main():
    """Generate sample fixtures for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate test fixtures')
    parser.add_argument('--symbol', default='AAPL', help='Stock symbol')
    parser.add_argument('--bars', type=int, default=30, help='Number of bars')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output', default='fixtures', help='Output directory')
    
    args = parser.parse_args()
    
    manager = FixtureManager(fixtures_dir=Path(args.output))
    
    # Create OHLCV fixture
    ohlcv_path = manager.create_ohlcv_fixture(
        symbol=args.symbol,
        num_bars=args.bars,
        seed=args.seed
    )
    
    # Create sample indicator fixture (RSI)
    rsi_test_cases = [
        {
            "name": "test_rsi_oversold",
            "description": "RSI should calculate correctly for oversold condition",
            "input": {
                "prices": [44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 
                          45.89, 46.03, 45.61, 46.28, 46.28],
                "period": 14
            },
            "expected": {
                "rsi": 70.46
            }
        },
        {
            "name": "test_rsi_overbought",
            "description": "RSI should calculate correctly for overbought condition",
            "input": {
                "prices": [46.28, 46.00, 46.03, 46.41, 46.22, 45.64, 46.21, 46.25, 45.71, 46.45,
                          45.78, 45.35, 44.03, 44.18, 44.22],
                "period": 14
            },
            "expected": {
                "rsi": 37.30
            }
        }
    ]
    
    rsi_path = manager.create_indicator_fixture('rsi', rsi_test_cases)
    
    # Create sample entry scenarios
    entry_scenarios = [
        {
            "name": "rsi_oversold_entry",
            "description": "Should enter when RSI < 30",
            "bar": {"date": "2024-01-15", "close": 95.0, "high": 96.0, "low": 94.0},
            "indicators": {"rsi": 28},
            "position": None,
            "expected_entry": True
        },
        {
            "name": "rsi_normal_no_entry",
            "description": "Should not enter when RSI is normal",
            "bar": {"date": "2024-01-16", "close": 100.0, "high": 101.0, "low": 99.0},
            "indicators": {"rsi": 50},
            "position": None,
            "expected_entry": False
        }
    ]
    
    entry_path = manager.create_entry_scenarios_fixture(entry_scenarios)
    
    # Create sample exit scenarios
    exit_scenarios = [
        {
            "name": "stop_loss_exit",
            "description": "Should exit when price drops 5%",
            "bar": {"date": "2024-01-20", "close": 95.0, "high": 96.0, "low": 94.0},
            "indicators": {"rsi": 45},
            "position": {"entry_price": 100.0, "shares": 10, "entry_date": "2024-01-15"},
            "expected_exit": True,
            "exit_reason": "stop_loss"
        },
        {
            "name": "take_profit_exit",
            "description": "Should exit when price gains 10%",
            "bar": {"date": "2024-01-25", "close": 110.0, "high": 111.0, "low": 109.0},
            "indicators": {"rsi": 75},
            "position": {"entry_price": 100.0, "shares": 10, "entry_date": "2024-01-15"},
            "expected_exit": True,
            "exit_reason": "take_profit"
        },
        {
            "name": "no_exit_holding",
            "description": "Should hold position when conditions not met",
            "bar": {"date": "2024-01-18", "close": 102.0, "high": 103.0, "low": 101.0},
            "indicators": {"rsi": 55},
            "position": {"entry_price": 100.0, "shares": 10, "entry_date": "2024-01-15"},
            "expected_exit": False,
            "exit_reason": None
        }
    ]
    
    exit_path = manager.create_exit_scenarios_fixture(exit_scenarios)
    
    print("\n✅ Generated fixtures:")
    print(f"  - {ohlcv_path}")
    print(f"  - {rsi_path}")
    print(f"  - {entry_path}")
    print(f"  - {exit_path}")
    
    return 0


if __name__ == '__main__':
    exit(main())
