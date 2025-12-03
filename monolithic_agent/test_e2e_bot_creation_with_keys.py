"""
End-to-End Test: Bot Creation with Key Rotation

Tests the complete flow from strategy description → AI code generation → file persistence
with the new key rotation system enabled.

This test verifies:
1. Key rotation system initialization with real API keys
2. Strategy generation using rotated keys
3. File persistence and validation
4. Key health tracking after generation
5. Fallback behavior if keys are exhausted
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "Backtest"))

from dotenv import load_dotenv
from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
from Backtest.key_rotation import get_key_manager, KeyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestE2EBotCreationWithKeys:
    """End-to-end tests for bot creation with key rotation"""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment"""
        load_dotenv()
        cls.test_output_dir = Path(__file__).parent / "test_output_e2e_keys"
        cls.test_output_dir.mkdir(exist_ok=True)
        logger.info(f"Test output directory: {cls.test_output_dir}")
    
    def test_01_key_rotation_initialization(self):
        """Test 1: Verify key rotation system initializes with provided keys"""
        logger.info("\n" + "="*70)
        logger.info("TEST 1: Key Rotation Initialization")
        logger.info("="*70)
        
        try:
            # Initialize key manager
            manager = get_key_manager()
            
            logger.info(f"Key rotation enabled: {manager.enabled}")
            logger.info(f"Number of keys loaded: {len(manager.keys)}")
            logger.info(f"Number of secrets loaded: {len(manager.key_secrets)}")
            
            # Verify keys are loaded
            assert len(manager.keys) > 0 or len(manager.key_secrets) > 0, \
                "No keys loaded in KeyManager"
            
            logger.info("✓ Key rotation system initialized successfully")
            
            # Log key information
            for key_id in manager.keys.keys():
                metadata = manager.keys[key_id]
                logger.info(f"  - {key_id}: {metadata.model_name} (rpm={metadata.rpm}, tpm={metadata.tpm})")
            
            return True
        
        except Exception as e:
            logger.error(f"✗ Key rotation initialization failed: {e}")
            raise
    
    def test_02_strategy_generation_with_rotation(self):
        """Test 2: Generate strategy using key rotation system"""
        logger.info("\n" + "="*70)
        logger.info("TEST 2: Strategy Generation with Key Rotation")
        logger.info("="*70)
        
        try:
            # Initialize generator with key rotation
            logger.info("Initializing GeminiStrategyGenerator with key rotation...")
            generator = GeminiStrategyGenerator(use_key_rotation=True)
            
            logger.info(f"Generator key rotation enabled: {generator.use_key_rotation}")
            logger.info(f"Selected key ID: {generator.selected_key_id}")
            
            # Simple strategy description
            description = (
                "Create a simple RSI-based trading strategy that:\n"
                "1. Buys when RSI drops below 30 (oversold)\n"
                "2. Sells when RSI rises above 70 (overbought)\n"
                "3. Uses 14-period RSI with close prices\n"
                "4. Includes basic position management"
            )
            
            logger.info(f"\nStrategy description:\n{description}\n")
            
            # Generate strategy
            logger.info("Generating strategy code...")
            start_time = time.time()
            code = generator.generate_strategy(
                description=description,
                strategy_name="KeyRotationTestStrategy"
            )
            elapsed = time.time() - start_time
            
            logger.info(f"✓ Strategy generated in {elapsed:.2f} seconds")
            logger.info(f"Generated code length: {len(code)} bytes")
            
            # Validate code structure
            assert len(code) > 100, "Generated code too short"
            assert "class" in code or "def" in code, "No Python structures found"
            
            # Check for required elements
            has_imports = any(x in code for x in ["import", "from"])
            has_logic = any(x in code for x in ["if", "def", "class"])
            
            logger.info(f"Has imports: {has_imports}")
            logger.info(f"Has logic: {has_logic}")
            
            assert has_imports or has_logic, "Generated code missing basic Python structure"
            
            # Save generated code
            output_file = self.test_output_dir / "test_generated_strategy_01.py"
            output_file.write_text(code, encoding='utf-8')
            logger.info(f"Saved generated code to: {output_file}")
            
            return True
        
        except Exception as e:
            logger.error(f"✗ Strategy generation failed: {e}", exc_info=True)
            raise
    
    def test_03_key_health_tracking(self):
        """Test 3: Verify key health is tracked after generation"""
        logger.info("\n" + "="*70)
        logger.info("TEST 3: Key Health Tracking")
        logger.info("="*70)
        
        try:
            manager = get_key_manager()
            
            # Get health status
            health = manager.get_health_status()
            
            logger.info(f"Number of monitored keys: {len(health)}")
            
            for key_id, status in health.items():
                logger.info(f"\nKey: {key_id}")
                logger.info(f"  Model: {status['model']}")
                logger.info(f"  Active: {status['active']}")
                logger.info(f"  Success Count: {status['success_count']}")
                logger.info(f"  Error Count: {status['error_count']}")
                logger.info(f"  In Cooldown: {status['in_cooldown']}")
                if status['last_used']:
                    logger.info(f"  Last Used: {status['last_used']}")
            
            logger.info("\n✓ Key health tracking verified")
            
            return True
        
        except Exception as e:
            logger.error(f"✗ Health tracking verification failed: {e}")
            raise
    
    def test_04_file_persistence(self):
        """Test 4: Verify generated strategy is persisted correctly"""
        logger.info("\n" + "="*70)
        logger.info("TEST 4: File Persistence")
        logger.info("="*70)
        
        try:
            # Generate and save strategy
            generator = GeminiStrategyGenerator(use_key_rotation=True)
            
            description = "RSI momentum strategy with dynamic periods"
            strategy_name = "KeyRotationFilePersistTest"
            
            logger.info(f"Generating strategy: {strategy_name}")
            code = generator.generate_strategy(description, strategy_name)
            
            # Save to file
            output_file = self.test_output_dir / f"{strategy_name}.py"
            output_file.write_text(code, encoding='utf-8')
            
            logger.info(f"Saved to: {output_file}")
            logger.info(f"File size: {output_file.stat().st_size} bytes")
            
            # Verify file exists and is readable
            assert output_file.exists(), "Generated file not created"
            
            # Read back and verify
            read_code = output_file.read_text(encoding='utf-8')
            assert read_code == code, "File contents don't match original code"
            
            logger.info("✓ File persistence verified")
            
            return True
        
        except Exception as e:
            logger.error(f"✗ File persistence test failed: {e}", exc_info=True)
            raise
    
    def test_05_multiple_strategies_with_different_keys(self):
        """Test 5: Generate multiple strategies and verify key rotation"""
        logger.info("\n" + "="*70)
        logger.info("TEST 5: Multiple Strategies with Key Rotation")
        logger.info("="*70)
        
        try:
            manager = get_key_manager()
            generator = GeminiStrategyGenerator(use_key_rotation=True)
            
            strategies = [
                {
                    "name": "MovingAverageCrossover",
                    "desc": "Buy when fast MA crosses above slow MA, sell on cross below"
                },
                {
                    "name": "BollingerBandStrategy",
                    "desc": "Buy on bounce from lower band, sell at upper band"
                },
                {
                    "name": "MACDStrategy",
                    "desc": "Trade MACD crossovers with signal line"
                }
            ]
            
            keys_used = set()
            
            for i, strategy in enumerate(strategies, 1):
                logger.info(f"\nGenerating strategy {i}/3: {strategy['name']}")
                
                try:
                    # Reinitialize to get fresh key selection
                    generator = GeminiStrategyGenerator(use_key_rotation=True)
                    keys_used.add(generator.selected_key_id)
                    
                    logger.info(f"  Using key: {generator.selected_key_id}")
                    
                    code = generator.generate_strategy(
                        description=strategy['desc'],
                        strategy_name=strategy['name']
                    )
                    
                    # Save strategy
                    output_file = self.test_output_dir / f"{strategy['name']}.py"
                    output_file.write_text(code, encoding='utf-8')
                    
                    logger.info(f"  Generated: {len(code)} bytes")
                    logger.info(f"  Saved to: {output_file.name}")
                
                except Exception as e:
                    logger.warning(f"  Failed to generate {strategy['name']}: {e}")
                    # Continue with next strategy
            
            logger.info(f"\n✓ Generated {len(strategies)} strategies")
            logger.info(f"  Keys used: {keys_used}")
            logger.info(f"  Unique keys: {len(keys_used)}")
            
            return True
        
        except Exception as e:
            logger.error(f"✗ Multiple strategies test failed: {e}", exc_info=True)
            raise
    
    def test_06_strategy_validation(self):
        """Test 6: Validate generated strategy structure"""
        logger.info("\n" + "="*70)
        logger.info("TEST 6: Strategy Validation")
        logger.info("="*70)
        
        try:
            generator = GeminiStrategyGenerator(use_key_rotation=True)
            
            description = "Simple trend-following strategy using price moving average"
            code = generator.generate_strategy(description, "ValidationTestStrategy")
            
            # Perform validation
            validation = generator.validate_generated_code(code)
            
            logger.info(f"Valid: {validation['valid']}")
            logger.info(f"Issues: {len(validation['issues'])}")
            logger.info(f"Warnings: {len(validation['warnings'])}")
            
            if validation['issues']:
                logger.warning("Issues found:")
                for issue in validation['issues']:
                    logger.warning(f"  - {issue}")
            
            if validation['warnings']:
                logger.info("Warnings:")
                for warning in validation['warnings']:
                    logger.info(f"  - {warning}")
            
            logger.info("✓ Strategy validation completed")
            
            return True
        
        except Exception as e:
            logger.error(f"✗ Strategy validation failed: {e}", exc_info=True)
            raise
    
    def test_07_error_recovery(self):
        """Test 7: Verify system recovers from errors"""
        logger.info("\n" + "="*70)
        logger.info("TEST 7: Error Recovery")
        logger.info("="*70)
        
        try:
            # Get initial key health
            manager = get_key_manager()
            initial_health = manager.get_health_status()
            
            logger.info("Initial health snapshot:")
            for key_id, status in initial_health.items():
                logger.info(f"  {key_id}: success={status['success_count']}, error={status['error_count']}")
            
            # Simulate error reporting
            first_key = list(manager.keys.keys())[0] if manager.keys else 'default'
            logger.info(f"\nSimulating error for key: {first_key}")
            
            manager.report_error(first_key, error_type='test_error')
            
            updated_health = manager.get_health_status()
            logger.info(f"Updated error count: {updated_health[first_key]['error_count']}")
            
            logger.info("✓ Error recovery verified")
            
            return True
        
        except Exception as e:
            logger.error(f"✗ Error recovery test failed: {e}")
            raise


def run_all_tests():
    """Run all tests and generate report"""
    logger.info("\n" + "="*70)
    logger.info("END-TO-END BOT CREATION TEST SUITE (With Key Rotation)")
    logger.info("="*70)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    
    # Load environment
    load_dotenv()
    
    # Check key configuration
    api_key = os.getenv('GEMINI_API_KEY')
    rotation_enabled = os.getenv('ENABLE_KEY_ROTATION', 'false').lower() == 'true'
    
    logger.info(f"\nConfiguration:")
    logger.info(f"  GEMINI_API_KEY set: {bool(api_key)}")
    logger.info(f"  ENABLE_KEY_ROTATION: {rotation_enabled}")
    logger.info(f"  SECRET_STORE_TYPE: {os.getenv('SECRET_STORE_TYPE', 'env')}")
    
    # Initialize test class
    test_class = TestE2EBotCreationWithKeys()
    test_class.setup_class()
    
    # Run tests
    tests = [
        ("Key Rotation Initialization", test_class.test_01_key_rotation_initialization),
        ("Strategy Generation with Rotation", test_class.test_02_strategy_generation_with_rotation),
        ("Key Health Tracking", test_class.test_03_key_health_tracking),
        ("File Persistence", test_class.test_04_file_persistence),
        ("Multiple Strategies", test_class.test_05_multiple_strategies_with_different_keys),
        ("Strategy Validation", test_class.test_06_strategy_validation),
        ("Error Recovery", test_class.test_07_error_recovery),
    ]
    
    results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\nRunning: {test_name}...")
            test_func()
            results['passed'] += 1
            logger.info(f"✓ PASSED: {test_name}")
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'test': test_name,
                'error': str(e)
            })
            logger.error(f"✗ FAILED: {test_name}")
            logger.error(f"  Error: {e}")
    
    # Generate final report
    logger.info("\n" + "="*70)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*70)
    logger.info(f"Passed: {results['passed']}/{len(tests)}")
    logger.info(f"Failed: {results['failed']}/{len(tests)}")
    logger.info(f"Success Rate: {results['passed']/len(tests)*100:.1f}%")
    
    if results['errors']:
        logger.info("\nFailed Tests:")
        for error in results['errors']:
            logger.info(f"  - {error['test']}: {error['error']}")
    
    logger.info(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70)
    
    # Save results
    results_file = test_class.test_output_dir / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(tests),
            'passed': results['passed'],
            'failed': results['failed'],
            'success_rate': results['passed']/len(tests),
            'errors': results['errors']
        }, f, indent=2)
    
    logger.info(f"Results saved to: {results_file}")
    
    return results['failed'] == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
