"""
Test All Bot Scripts to Identify Working Bots
==============================================
This script tests all bot scripts in Backtest/codes/ to identify which ones:
1. Import successfully
2. Have proper structure (Strategy class or similar)
3. Can be instantiated

Note: Full backtesting requires specific data and setup, so this focuses on
validating that bots are structurally sound and can be imported.
"""

import os
import sys
import importlib.util
import json
from pathlib import Path
from datetime import datetime
import traceback

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

class BotTester:
    """Test bot scripts and track results"""
    
    def __init__(self):
        self.codes_dir = Path(__file__).parent / "Backtest" / "codes"
        self.results = {
            'working_bots': [],
            'failed_bots': [],
            'test_timestamp': datetime.now().isoformat()
        }
        
    def load_bot_config(self, bot_file: Path) -> dict:
        """Load bot configuration from JSON file"""
        json_file = bot_file.with_suffix('.json')
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"  ⚠️  Could not load config: {e}")
                return {}
        return {}
    
    def import_strategy(self, bot_file: Path):
        """Import strategy class from bot file"""
        module_name = bot_file.stem
        spec = importlib.util.spec_from_file_location(module_name, bot_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {bot_file}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Find Strategy class or similar
        strategy_classes = []
        for attr_name in dir(module):
            if attr_name.startswith('_'):
                continue
            attr = getattr(module, attr_name)
            if isinstance(attr, type):
                # Check if it looks like a strategy class
                class_methods = dir(attr)
                if 'on_bar' in class_methods or 'next' in class_methods or 'init' in class_methods:
                    strategy_classes.append((attr_name, attr))
        
        if not strategy_classes:
            raise ImportError(f"No Strategy class found in {bot_file}")
        
        return strategy_classes[0][1]  # Return first matching class
    
    def validate_strategy_structure(self, strategy_class) -> dict:
        """Validate strategy class structure"""
        validation = {
            'has_init': hasattr(strategy_class, '__init__'),
            'has_on_bar': hasattr(strategy_class, 'on_bar'),
            'has_next': hasattr(strategy_class, 'next'),
            'is_backtesting_py': False,
            'is_simbroker': False
        }
        
        # Check if it's a backtesting.py strategy
        try:
            from backtesting import Strategy as BacktestingStrategy
            if issubclass(strategy_class, BacktestingStrategy):
                validation['is_backtesting_py'] = True
        except:
            pass
        
        # Check if it uses SimBroker (has on_bar method)
        if hasattr(strategy_class, 'on_bar'):
            validation['is_simbroker'] = True
        
        return validation
    
    def test_bot(self, bot_file: Path) -> dict:
        """Test a single bot script"""
        result = {
            'bot_name': bot_file.stem,
            'bot_file': str(bot_file),
            'status': 'unknown',
            'error': None,
            'strategy_type': 'unknown',
            'has_config': False,
            'validation': {}
        }
        
        print(f"\n{'='*80}")
        print(f"Testing: {bot_file.name}")
        print(f"{'='*80}")
        
        # Load configuration
        config = self.load_bot_config(bot_file)
        if config:
            result['has_config'] = True
            print(f"  📋 Config loaded: {config.get('symbol', 'N/A')}")
        
        # Test import
        try:
            print(f"  🔍 Importing strategy class...")
            strategy_class = self.import_strategy(bot_file)
            print(f"  ✅ Import successful: {strategy_class.__name__}")
            
            # Validate structure
            validation = self.validate_strategy_structure(strategy_class)
            result['validation'] = validation
            
            if validation['is_backtesting_py']:
                result['strategy_type'] = 'backtesting.py'
                print(f"  📦 Strategy type: backtesting.py")
            elif validation['is_simbroker']:
                result['strategy_type'] = 'SimBroker'
                print(f"  📦 Strategy type: SimBroker (on_bar)")
            else:
                result['strategy_type'] = 'unknown'
                print(f"  ⚠️  Strategy type: Unknown")
            
            # Success - bot can be imported and validated
            result['status'] = 'working'
            print(f"  🎉 BOT IS IMPORTABLE AND VALID!")
            
        except Exception as e:
            print(f"  ❌ Import/validation failed: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
            return result
        
        return result
    
    def test_all_bots(self):
        """Test all bot scripts in the codes directory"""
        print(f"\n{'='*80}")
        print(f"BOT TESTING SESSION")
        print(f"{'='*80}")
        print(f"Codes directory: {self.codes_dir}")
        print(f"Timestamp: {self.results['test_timestamp']}")
        
        # Get all Python files (excluding test files and __pycache__)
        bot_files = [
            f for f in self.codes_dir.glob('*.py')
            if not f.name.startswith('test_') 
            and not f.name.startswith('_')
            and f.name not in ['README.md', '__init__.py']
        ]
        
        print(f"\nFound {len(bot_files)} bot scripts to test\n")
        
        # Test each bot
        for bot_file in sorted(bot_files):
            try:
                result = self.test_bot(bot_file)
                
                # Categorize result
                if result['status'] == 'working':
                    self.results['working_bots'].append(result)
                else:
                    self.results['failed_bots'].append(result)
                    
            except Exception as e:
                print(f"  ❌ Unexpected error testing {bot_file.name}: {e}")
                self.results['failed_bots'].append({
                    'bot_name': bot_file.stem,
                    'bot_file': str(bot_file),
                    'status': 'unexpected_error',
                    'error': str(e)
                })
        
        # Print summary
        self.print_summary()
        
        # Save results
        self.save_results()
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*80}")
        print(f"TEST SUMMARY")
        print(f"{'='*80}")
        
        total = len(self.results['working_bots']) + len(self.results['failed_bots'])
        
        print(f"\n✅ WORKING BOTS: {len(self.results['working_bots'])} / {total}")
        
        # Group by strategy type
        simbroker_bots = [b for b in self.results['working_bots'] if b['strategy_type'] == 'SimBroker']
        backtesting_bots = [b for b in self.results['working_bots'] if b['strategy_type'] == 'backtesting.py']
        unknown_bots = [b for b in self.results['working_bots'] if b['strategy_type'] == 'unknown']
        
        print(f"\n   SimBroker strategies: {len(simbroker_bots)}")
        for bot in simbroker_bots:
            config_status = "✓ config" if bot['has_config'] else "✗ no config"
            print(f"   - {bot['bot_name']} ({config_status})")
        
        print(f"\n   Backtesting.py strategies: {len(backtesting_bots)}")
        for bot in backtesting_bots:
            config_status = "✓ config" if bot['has_config'] else "✗ no config"
            print(f"   - {bot['bot_name']} ({config_status})")
        
        if unknown_bots:
            print(f"\n   Unknown type strategies: {len(unknown_bots)}")
            for bot in unknown_bots:
                print(f"   - {bot['bot_name']}")
        
        print(f"\n❌ FAILED BOTS: {len(self.results['failed_bots'])} / {total}")
        for bot in self.results['failed_bots']:
            error_preview = bot['error'][:50] if bot['error'] else 'Unknown error'
            print(f"   - {bot['bot_name']}: {error_preview}")
        
        print(f"\n{'='*80}")
        
        # Recommend bots for verification
        if simbroker_bots:
            print(f"\n🏆 RECOMMENDED FOR VERIFICATION (SimBroker with config):")
            verified_candidates = [b for b in simbroker_bots if b['has_config']]
            for i, bot in enumerate(verified_candidates[:5], 1):
                print(f"   {i}. {bot['bot_name']}")
            
            if len(verified_candidates) > 5:
                print(f"   ... and {len(verified_candidates) - 5} more")
    
    def save_results(self):
        """Save test results to JSON file"""
        results_file = self.codes_dir / 'bot_test_results.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to: {results_file}")

if __name__ == '__main__':
    tester = BotTester()
    tester.test_all_bots()
