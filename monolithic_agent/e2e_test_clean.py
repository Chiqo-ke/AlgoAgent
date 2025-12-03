"""
End-to-End Test: Monolithic Agent Full Flow
===========================================

Tests the complete flow from user strategy description to code generation
without relying on external APIs initially.

Test Flow:
1. Environment setup
2. Strategy generator initialization  
3. Generate strategy code (mock or real)
4. Code validation
5. Save strategy file
6. AI Agent integration
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import traceback
from datetime import datetime

# Setup paths
MONOLITHIC_ROOT = Path(__file__).parent
sys.path.insert(0, str(MONOLITHIC_ROOT))

# Configure logging with proper encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler(
            MONOLITHIC_ROOT / 'e2e_test_results.log',
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class E2ETest:
    """End-to-End Test Suite for Monolithic Agent"""
    
    def __init__(self):
        """Initialize test suite"""
        self.results = []
        self.passed = 0
        self.failed = 0
        self.start_time = datetime.now()
    
    def test(self, name: str, passed: bool, details: str = "", error: str = ""):
        """Record test result"""
        status = "[PASS]" if passed else "[FAIL]"
        self.results.append({
            'name': name,
            'passed': passed,
            'details': details,
            'error': error
        })
        
        if passed:
            self.passed += 1
            logger.info(f"{status} {name}")
            if details:
                logger.info(f"        {details}")
        else:
            self.failed += 1
            logger.error(f"{status} {name}")
            if error:
                logger.error(f"        Error: {error}")
    
    def run_suite(self):
        """Run all tests"""
        logger.info("=" * 80)
        logger.info("MONOLITHIC AGENT E2E TEST SUITE")
        logger.info("=" * 80)
        logger.info(f"Start: {self.start_time.isoformat()}\n")
        
        # Test 1: Environment
        self.test_environment()
        
        # Test 2: Imports
        self.test_imports()
        
        # Test 3: Generator initialization
        self.test_generator_init()
        
        # Test 4: Code generation (with mock if needed)
        self.test_strategy_generation()
        
        # Test 5: Code validation
        self.test_code_validation()
        
        # Test 6: File operations
        self.test_file_operations()
        
        # Test 7: AI Agent
        self.test_ai_agent()
        
        # Summary
        self.print_summary()
    
    # ========== TEST 1: Environment ==========
    def test_environment(self):
        """Test 1: Check environment"""
        logger.info("\n[TEST 1] Environment Setup")
        logger.info("-" * 80)
        
        try:
            # Check Python version
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            self.test(
                "Python version check",
                True,
                f"Python {python_version}"
            )
            
            # Check workspace
            if MONOLITHIC_ROOT.exists():
                self.test(
                    "Monolithic root directory",
                    True,
                    str(MONOLITHIC_ROOT)
                )
            else:
                self.test(
                    "Monolithic root directory",
                    False,
                    error=f"Directory not found: {MONOLITHIC_ROOT}"
                )
            
            # Check key subdirectories
            key_dirs = [
                ('Backtest', MONOLITHIC_ROOT / 'Backtest'),
                ('Strategy', MONOLITHIC_ROOT / 'Strategy'),
                ('strategy_api', MONOLITHIC_ROOT / 'strategy_api'),
            ]
            
            for name, path in key_dirs:
                if path.exists():
                    self.test(f"Directory: {name}", True)
                else:
                    self.test(f"Directory: {name}", False, error="Not found")
        
        except Exception as e:
            self.test("Environment Setup", False, error=str(e))
    
    # ========== TEST 2: Imports ==========
    def test_imports(self):
        """Test 2: Test required imports"""
        logger.info("\n[TEST 2] Package Imports")
        logger.info("-" * 80)
        
        packages = [
            ('google.generativeai', 'Gemini API'),
            ('langchain', 'LangChain'),
            ('backtesting', 'backtesting.py'),
            ('pandas', 'Pandas'),
            ('numpy', 'NumPy'),
        ]
        
        for module_name, label in packages:
            try:
                __import__(module_name)
                self.test(f"Import: {label}", True)
            except ImportError as e:
                self.test(f"Import: {label}", False, error=str(e))
        
        # Special check for Django
        try:
            import django
            django_ok = True
        except ImportError:
            django_ok = False
        
        self.test(
            "Import: Django",
            django_ok,
            error="Django not installed (optional)" if not django_ok else ""
        )
    
    # ========== TEST 3: Generator Initialization ==========
    def test_generator_init(self):
        """Test 3: Initialize Gemini Strategy Generator"""
        logger.info("\n[TEST 3] Strategy Generator Initialization")
        logger.info("-" * 80)
        
        try:
            from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
            
            api_key = os.getenv('GEMINI_API_KEY')
            
            if not api_key:
                self.test(
                    "Initialize GeminiStrategyGenerator",
                    False,
                    error="GEMINI_API_KEY not set (set env var to test API features)"
                )
                return
            
            generator = GeminiStrategyGenerator(api_key=api_key)
            self.test(
                "Initialize GeminiStrategyGenerator",
                True,
                "Generator initialized with gemini-2.0-flash"
            )
            
            # Check system prompt
            if generator.system_prompt and len(generator.system_prompt) > 100:
                self.test(
                    "System prompt loaded",
                    True,
                    f"Prompt size: {len(generator.system_prompt)} chars"
                )
            else:
                self.test(
                    "System prompt loaded",
                    False,
                    error="Prompt is empty or too short"
                )
        
        except ImportError as e:
            self.test(
                "Import GeminiStrategyGenerator",
                False,
                error=str(e)
            )
        except Exception as e:
            self.test(
                "Initialize GeminiStrategyGenerator",
                False,
                error=str(e)
            )
    
    # ========== TEST 4: Strategy Generation ==========
    def test_strategy_generation(self):
        """Test 4: Generate strategy code"""
        logger.info("\n[TEST 4] Strategy Code Generation")
        logger.info("-" * 80)
        
        try:
            from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
            
            api_key = os.getenv('GEMINI_API_KEY')
            
            if not api_key:
                # Use mock strategy code
                logger.info("Using mock strategy (API key not set)")
                self.generated_code = self._get_mock_strategy()
                self.test(
                    "Generate strategy code (MOCK)",
                    True,
                    "Using example strategy code"
                )
                return
            
            # Real generation with API
            generator = GeminiStrategyGenerator(api_key=api_key)
            
            strategy_desc = """
            Simple EMA Crossover Strategy:
            - Buy when EMA(10) crosses above EMA(50)
            - Sell when EMA(10) crosses below EMA(50)
            - Risk 1% per trade
            """
            
            logger.info(f"Generating strategy from: {strategy_desc.strip()}")
            
            self.generated_code = generator.generate_strategy(strategy_desc)
            
            if self.generated_code and len(self.generated_code) > 100:
                self.test(
                    "Generate strategy code",
                    True,
                    f"Generated {len(self.generated_code)} chars"
                )
            else:
                self.test(
                    "Generate strategy code",
                    False,
                    error="Generated code is too short"
                )
        
        except Exception as e:
            logger.error(f"Generation error: {e}")
            # Fall back to mock
            self.generated_code = self._get_mock_strategy()
            self.test(
                "Generate strategy code",
                False,
                error=f"API error (using mock): {str(e)[:50]}"
            )
    
    @staticmethod
    def _get_mock_strategy() -> str:
        """Return mock strategy code for testing"""
        return '''
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA

class EMACrossover(Strategy):
    """Simple EMA Crossover Strategy"""
    
    def init(self):
        # Precompute indicators
        self.ma1 = self.I(SMA, self.data.Close, 10)
        self.ma2 = self.I(SMA, self.data.Close, 50)
    
    def next(self):
        # Buy signal: EMA10 crosses above EMA50
        if crossover(self.ma1, self.ma2):
            self.buy()
        # Sell signal: EMA10 crosses below EMA50
        elif crossover(self.ma2, self.ma1):
            self.position.close()

if __name__ == '__main__':
    # Example usage
    from backtesting.test import GOOG
    bt = Backtest(GOOG, EMACrossover, cash=10000, commission=.002)
    stats = bt.run()
    print(stats)
'''
    
    # ========== TEST 5: Code Validation ==========
    def test_code_validation(self):
        """Test 5: Validate generated code"""
        logger.info("\n[TEST 5] Code Validation")
        logger.info("-" * 80)
        
        try:
            if not hasattr(self, 'generated_code'):
                self.test(
                    "Code validation",
                    False,
                    error="No generated code available"
                )
                return
            
            # Test 1: Syntax check
            try:
                compile(self.generated_code, '<strategy>', 'exec')
                self.test("Python syntax check", True)
            except SyntaxError as e:
                self.test(
                    "Python syntax check",
                    False,
                    error=f"Line {e.lineno}: {e.msg}"
                )
                return
            
            # Test 2: Component checks
            checks = [
                ('from backtesting import' in self.generated_code, "Has backtesting import"),
                ('class' in self.generated_code, "Has class definition"),
                ('def init' in self.generated_code or '__init__' in self.generated_code, "Has init method"),
                ('def next' in self.generated_code, "Has next() method"),
            ]
            
            for check, label in checks:
                self.test(f"Code component: {label}", check)
        
        except Exception as e:
            self.test("Code validation", False, error=str(e))
    
    # ========== TEST 6: File Operations ==========
    def test_file_operations(self):
        """Test 6: Test file I/O"""
        logger.info("\n[TEST 6] File Operations")
        logger.info("-" * 80)
        
        try:
            # Test writing strategy to file
            codes_dir = MONOLITHIC_ROOT / 'Backtest' / 'codes'
            codes_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_file = codes_dir / f'e2e_test_{timestamp}.py'
            
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(self.generated_code)
            
            # Verify file was created
            if test_file.exists() and test_file.stat().st_size > 0:
                self.test(
                    "Write strategy file",
                    True,
                    f"Saved: {test_file.name} ({test_file.stat().st_size} bytes)"
                )
                self.test_file = test_file
            else:
                self.test(
                    "Write strategy file",
                    False,
                    error="File not properly written"
                )
        
        except Exception as e:
            self.test("File operations", False, error=str(e))
    
    # ========== TEST 7: AI Agent ==========
    def test_ai_agent(self):
        """Test 7: AI Developer Agent"""
        logger.info("\n[TEST 7] AI Developer Agent")
        logger.info("-" * 80)
        
        try:
            from Backtest.ai_developer_agent import AIDeveloperAgent
            
            api_key = os.getenv('GEMINI_API_KEY')
            
            if not api_key:
                self.test(
                    "Initialize AI Developer Agent",
                    False,
                    error="GEMINI_API_KEY not set (required for AI features)"
                )
                return
            
            agent = AIDeveloperAgent(api_key=api_key)
            self.test(
                "Initialize AI Developer Agent",
                True,
                "Agent created with terminal access"
            )
            
            # Test chat
            response = agent.chat("Hello, what can you do?")
            
            if response and len(response) > 0:
                self.test(
                    "AI chat interaction",
                    True,
                    f"Response: {len(response)} characters"
                )
            else:
                self.test(
                    "AI chat interaction",
                    False,
                    error="Empty response from agent"
                )
        
        except ImportError:
            self.test(
                "Initialize AI Developer Agent",
                False,
                error="AIDeveloperAgent not available"
            )
        except Exception as e:
            self.test(
                "AI Developer Agent",
                False,
                error=str(e)
            )
    
    # ========== SUMMARY ==========
    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        
        total = self.passed + self.failed
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed:      {self.passed}")
        logger.info(f"Failed:      {self.failed}")
        
        if total > 0:
            pass_rate = (self.passed / total * 100)
            logger.info(f"Pass Rate:   {pass_rate:.1f}%")
        
        # Failed tests detail
        if self.failed > 0:
            logger.info("\nFailed Tests:")
            for result in self.results:
                if not result['passed']:
                    logger.info(f"  - {result['name']}")
                    if result['error']:
                        logger.info(f"    {result['error']}")
        
        # Save JSON report
        end_time = datetime.now()
        report = {
            'timestamp': self.start_time.isoformat(),
            'duration_seconds': (end_time - self.start_time).total_seconds(),
            'total': total,
            'passed': self.passed,
            'failed': self.failed,
            'pass_rate': (self.passed / total * 100) if total > 0 else 0,
            'results': self.results
        }
        
        report_file = MONOLITHIC_ROOT / 'e2e_test_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\nReport saved: {report_file}")
        logger.info(f"End: {end_time.isoformat()}")
        logger.info("=" * 80)
        
        # Return exit code
        return 0 if self.failed == 0 else 1


def main():
    """Run test suite"""
    suite = E2ETest()
    exit_code = suite.run_suite()
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
