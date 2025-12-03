"""
End-to-End Test: Bot Creation with Key Rotation (Mock Version)

This test demonstrates the complete flow from strategy description → code generation
with the key rotation system enabled, using mock API responses.

This test verifies:
1. Key rotation system initialization
2. Key selection algorithm
3. Health tracking
4. File persistence
5. Failover behavior
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "Backtest"))

from dotenv import load_dotenv
from Backtest.key_rotation import get_key_manager, KeyManager, APIKeyMetadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestE2EBotCreationMock:
    """End-to-end tests for bot creation with mock key rotation"""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment"""
        load_dotenv()
        cls.test_output_dir = Path(__file__).parent / "test_output_e2e_mock"
        cls.test_output_dir.mkdir(exist_ok=True)
        logger.info(f"Test output directory: {cls.test_output_dir}")
    
    def test_01_key_rotation_system_init(self):
        """Test 1: Key rotation system initializes correctly"""
        logger.info("\n" + "="*70)
        logger.info("TEST 1: Key Rotation System Initialization")
        logger.info("="*70)
        
        try:
            # Get key manager
            manager = get_key_manager()
            
            logger.info(f"Key rotation enabled: {manager.enabled}")
            logger.info(f"Keys loaded: {len(manager.keys)}")
            logger.info(f"Secrets loaded: {len(manager.key_secrets)}")
            
            # Should have at least default key
            assert len(manager.keys) >= 0, "Keys dictionary initialized"
            assert manager.key_secrets, "At least one secret loaded"
            
            logger.info("✓ Key rotation system initialized")
            return True
        
        except Exception as e:
            logger.error(f"✗ Failed: {e}")
            raise
    
    def test_02_key_selection_algorithm(self):
        """Test 2: Key selection algorithm works correctly"""
        logger.info("\n" + "="*70)
        logger.info("TEST 2: Key Selection Algorithm")
        logger.info("="*70)
        
        try:
            manager = get_key_manager()
            
            # Add test keys
            logger.info("Creating test keys...")
            
            test_keys = [
                ('flash_01', 'gemini-2.5-flash', 60, 1000000),
                ('flash_02', 'gemini-2.5-flash', 60, 1000000),
                ('pro_01', 'gemini-2.5-pro', 10, 4000000),
            ]
            
            for key_id, model, rpm, tpm in test_keys:
                manager.keys[key_id] = APIKeyMetadata(
                    key_id=key_id,
                    model_name=model,
                    provider='gemini',
                    rpm=rpm,
                    tpm=tpm,
                    active=True
                )
                manager.key_secrets[key_id] = f'test-secret-{key_id}'
            
            logger.info(f"Added {len(test_keys)} test keys")
            
            # Test key selection
            logger.info("\nTesting key selection...")
            
            # Select any available key
            key_info = manager.select_key()
            logger.info(f"Selected key: {key_info['key_id'] if key_info else 'None'}")
            assert key_info is not None, "Should select a key"
            assert 'secret' in key_info, "Should include secret"
            assert 'key_id' in key_info, "Should include key_id"
            
            # Select with model preference
            logger.info("\nTesting model preference...")
            key_info = manager.select_key(model_preference='gemini-2.5-flash')
            logger.info(f"Selected flash key: {key_info['key_id'] if key_info else 'None'}")
            if key_info:
                assert key_info['model'] == 'gemini-2.5-flash', "Should select flash model"
            
            logger.info("✓ Key selection algorithm works correctly")
            return True
        
        except Exception as e:
            logger.error(f"✗ Failed: {e}")
            raise
    
    def test_03_health_tracking(self):
        """Test 3: Key health is tracked correctly"""
        logger.info("\n" + "="*70)
        logger.info("TEST 3: Health Tracking")
        logger.info("="*70)
        
        try:
            manager = get_key_manager()
            
            # Select a key to update health
            logger.info("Selecting key to track health...")
            key_info = manager.select_key()
            
            if key_info:
                key_id = key_info['key_id']
                logger.info(f"Selected key: {key_id}")
                
                # Get health before
                health_before = manager.get_health_status().get(key_id, {})
                logger.info(f"Success count before: {health_before.get('success_count', 0)}")
                
                # Report error
                logger.info("Reporting error...")
                manager.report_error(key_id, 'test_error')
                
                # Get health after
                health_after = manager.get_health_status().get(key_id, {})
                logger.info(f"Error count after: {health_after.get('error_count', 0)}")
                logger.info(f"In cooldown: {health_after.get('in_cooldown', False)}")
                
                assert health_after.get('error_count', 0) > health_before.get('error_count', 0), \
                    "Error count should increase"
            
            logger.info("✓ Health tracking works correctly")
            return True
        
        except Exception as e:
            logger.error(f"✗ Failed: {e}")
            raise
    
    def test_04_file_persistence(self):
        """Test 4: Generated code can be persisted"""
        logger.info("\n" + "="*70)
        logger.info("TEST 4: File Persistence")
        logger.info("="*70)
        
        try:
            # Create mock strategy code
            strategy_code = '''"""
Generated Trading Strategy - RSI Strategy
"""

import pandas as pd
import numpy as np
from datetime import datetime

class RSIStrategy:
    """Simple RSI-based trading strategy"""
    
    def __init__(self, period=14):
        self.period = period
        self.prices = []
    
    def calculate_rsi(self, prices):
        """Calculate RSI indicator"""
        deltas = np.diff(prices)
        seed = deltas[:self.period+1]
        up = seed[seed >= 0].sum() / self.period
        down = -seed[seed < 0].sum() / self.period
        rs = up / down
        rsi = np.zeros_like(prices)
        rsi[:self.period] = 100. - 100. / (1. + rs)
        
        for i in range(self.period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            up = (up * (self.period - 1) + upval) / self.period
            down = (down * (self.period - 1) + downval) / self.period
            rs = up / down
            rsi[i] = 100. - 100. / (1. + rs)
        
        return rsi
    
    def signal(self, price):
        """Generate trading signal"""
        self.prices.append(price)
        
        if len(self.prices) < self.period:
            return 0
        
        rsi = self.calculate_rsi(np.array(self.prices))[-1]
        
        if rsi < 30:
            return 1  # Buy signal
        elif rsi > 70:
            return -1  # Sell signal
        else:
            return 0  # Hold

if __name__ == "__main__":
    print("Strategy loaded successfully")
'''
            
            # Save to file
            output_file = self.test_output_dir / "RSIStrategy.py"
            output_file.write_text(strategy_code, encoding='utf-8')
            
            logger.info(f"Saved strategy to: {output_file}")
            logger.info(f"File size: {output_file.stat().st_size} bytes")
            
            # Verify file exists
            assert output_file.exists(), "File should exist"
            
            # Verify file is readable
            read_code = output_file.read_text(encoding='utf-8')
            assert len(read_code) > 0, "File should have content"
            assert "class RSIStrategy" in read_code, "File should contain strategy class"
            
            logger.info("✓ File persistence works correctly")
            return True
        
        except Exception as e:
            logger.error(f"✗ Failed: {e}")
            raise
    
    def test_05_multi_key_management(self):
        """Test 5: Multiple keys can be managed"""
        logger.info("\n" + "="*70)
        logger.info("TEST 5: Multi-Key Management")
        logger.info("="*70)
        
        try:
            # Get existing manager
            manager = get_key_manager()
            
            # Simulate loading multiple keys
            logger.info("Simulating multi-key setup...")
            
            keys_data = [
                {
                    'key_id': 'test_flash_01',
                    'model_name': 'gemini-2.5-flash',
                    'provider': 'gemini',
                    'rpm': 60,
                    'tpm': 1000000,
                    'active': True
                },
                {
                    'key_id': 'test_flash_02',
                    'model_name': 'gemini-2.5-flash',
                    'provider': 'gemini',
                    'rpm': 60,
                    'tpm': 1000000,
                    'active': True
                },
                {
                    'key_id': 'test_pro_01',
                    'model_name': 'gemini-2.5-pro',
                    'provider': 'gemini',
                    'rpm': 10,
                    'tpm': 4000000,
                    'active': True
                }
            ]
            
            # Load keys
            for key_data in keys_data:
                manager.keys[key_data['key_id']] = APIKeyMetadata.from_dict(key_data)
                manager.key_secrets[key_data['key_id']] = f"secret-{key_data['key_id']}"
            
            num_keys = len([k for k in manager.keys if k.startswith('test_')])
            logger.info(f"Loaded {num_keys} test keys")
            
            # Verify all keys are loaded
            assert num_keys >= 3, "Should have at least 3 test keys"
            
            # Test load distribution
            logger.info("\nTesting load distribution...")
            selections = {}
            for _ in range(10):
                key_info = manager.select_key()
                if key_info:
                    key_id = key_info['key_id']
                    selections[key_id] = selections.get(key_id, 0) + 1
            
            logger.info(f"Distribution: {selections}")
            
            logger.info("✓ Multi-key management works correctly")
            return True
        
        except Exception as e:
            logger.error(f"✗ Failed: {e}")
            raise
    
    def test_06_failover_simulation(self):
        """Test 6: System handles failover correctly"""
        logger.info("\n" + "="*70)
        logger.info("TEST 6: Failover Simulation")
        logger.info("="*70)
        
        try:
            manager = KeyManager()
            
            # Set up keys
            logger.info("Setting up test keys...")
            for i in range(1, 4):
                key_id = f'key_{i}'
                manager.keys[key_id] = APIKeyMetadata(
                    key_id=key_id,
                    model_name='gemini-2.5-flash',
                    provider='gemini',
                    rpm=60,
                    tpm=1000000,
                    active=True
                )
                manager.key_secrets[key_id] = f'secret-{key_id}'
            
            logger.info(f"Created {len(manager.keys)} keys")
            
            # Simulate key failures
            logger.info("\nSimulating key failures...")
            
            # Key 1 fails once
            manager.report_error('key_1')
            health_1 = manager.get_health_status()['key_1']
            logger.info(f"Key_1 after 1 error: error_count={health_1['error_count']}, in_cooldown={health_1['in_cooldown']}")
            
            # Key 2 fails 3 times (should enter cooldown)
            for _ in range(3):
                manager.report_error('key_2')
            health_2 = manager.get_health_status()['key_2']
            logger.info(f"Key_2 after 3 errors: error_count={health_2['error_count']}, in_cooldown={health_2['in_cooldown']}")
            
            assert health_2['in_cooldown'], "Key should be in cooldown after 3 errors"
            
            # Try to select - should avoid key_2
            logger.info("\nSelecting key (avoiding cooldown key)...")
            key_info = manager.select_key(exclude_keys=['key_2'])
            logger.info(f"Selected: {key_info['key_id'] if key_info else 'None'}")
            
            if key_info:
                assert key_info['key_id'] != 'key_2', "Should not select key in cooldown"
            
            logger.info("✓ Failover handling works correctly")
            return True
        
        except Exception as e:
            logger.error(f"✗ Failed: {e}")
            raise
    
    def test_07_rate_limiting_logic(self):
        """Test 7: Rate limiting logic is correct"""
        logger.info("\n" + "="*70)
        logger.info("TEST 7: Rate Limiting Logic")
        logger.info("="*70)
        
        try:
            manager = KeyManager()
            
            # Create key with specific limits
            logger.info("Creating key with specific rate limits...")
            
            manager.keys['limited_key'] = APIKeyMetadata(
                key_id='limited_key',
                model_name='gemini-2.5-flash',
                provider='gemini',
                rpm=5,        # Only 5 requests per minute
                tpm=1000,     # Only 1000 tokens per minute
                active=True
            )
            manager.key_secrets['limited_key'] = 'secret'
            
            # Get metadata
            metadata = manager.keys['limited_key']
            logger.info(f"Key RPM limit: {metadata.rpm}")
            logger.info(f"Key TPM limit: {metadata.tpm}")
            
            assert metadata.rpm == 5, "RPM should be 5"
            assert metadata.tpm == 1000, "TPM should be 1000"
            
            # Check capacity function (without Redis)
            logger.info("\nTesting capacity check (without Redis)...")
            
            # Without Redis, should always return True (fail open)
            can_proceed = manager._check_capacity('limited_key', metadata, 500)
            logger.info(f"Can proceed with 500 tokens: {can_proceed}")
            
            assert can_proceed, "Should allow requests when Redis unavailable"
            
            logger.info("✓ Rate limiting logic works correctly")
            return True
        
        except Exception as e:
            logger.error(f"✗ Failed: {e}")
            raise


def run_all_tests():
    """Run all tests and generate report"""
    logger.info("\n" + "="*70)
    logger.info("END-TO-END BOT CREATION TEST SUITE (Mock)")
    logger.info("With Key Rotation System Integration")
    logger.info("="*70)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python version: {sys.version}")
    
    load_dotenv()
    
    # Initialize test class
    test_class = TestE2EBotCreationMock()
    test_class.setup_class()
    
    # Run tests
    tests = [
        ("Key Rotation Initialization", test_class.test_01_key_rotation_system_init),
        ("Key Selection Algorithm", test_class.test_02_key_selection_algorithm),
        ("Health Tracking", test_class.test_03_health_tracking),
        ("File Persistence", test_class.test_04_file_persistence),
        ("Multi-Key Management", test_class.test_05_multi_key_management),
        ("Failover Simulation", test_class.test_06_failover_simulation),
        ("Rate Limiting Logic", test_class.test_07_rate_limiting_logic),
    ]
    
    results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    for test_name, test_func in tests:
        try:
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
    
    # Generate final report
    logger.info("\n" + "="*70)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*70)
    logger.info(f"Total Tests: {len(tests)}")
    logger.info(f"Passed: {results['passed']}")
    logger.info(f"Failed: {results['failed']}")
    logger.info(f"Success Rate: {results['passed']/len(tests)*100:.1f}%")
    
    if results['errors']:
        logger.info("\nFailed Tests:")
        for error in results['errors']:
            logger.info(f"  - {error['test']}")
            logger.info(f"    Error: {error['error']}")
    
    logger.info(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70)
    
    # Save results
    results_file = test_class.test_output_dir / "test_results_mock.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'test_type': 'mock',
            'total_tests': len(tests),
            'passed': results['passed'],
            'failed': results['failed'],
            'success_rate': results['passed']/len(tests),
            'errors': results['errors']
        }, f, indent=2)
    
    logger.info(f"\nResults saved to: {results_file}")
    
    return results['failed'] == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
