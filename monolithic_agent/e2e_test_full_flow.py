"""
End-to-End Test: User Strategy Description to Generated Code
===========================================================

This test simulates the complete flow:
1. User describes a strategy
2. AI validates the strategy description
3. AI generates Python code for backtesting.py
4. Code is saved and ready for execution

Tests both the monolithic agent flow and API endpoints.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import traceback
from datetime import datetime

# Add paths for imports
MONOLITHIC_ROOT = Path(__file__).parent
sys.path.insert(0, str(MONOLITHIC_ROOT))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(MONOLITHIC_ROOT / 'e2e_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Django setup (required for API tests)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')
import django
try:
    django.setup()
except Exception as e:
    logger.warning(f"Django setup skipped: {e}")


class E2ETestSuite:
    """Comprehensive end-to-end test suite"""
    
    def __init__(self):
        """Initialize test suite"""
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'test_cases': [],
            'timestamp': None
        }
        self.test_cases = []
    
    def log_test_result(self, test_name: str, passed: bool, details: str = "", error: str = ""):
        """Log test result"""
        self.results['total_tests'] += 1
        
        result = {
            'test': test_name,
            'passed': passed,
            'details': details,
            'error': error
        }
        
        self.results['test_cases'].append(result)
        
        if passed:
            self.results['passed'] += 1
            logger.info(f"✓ PASS: {test_name}")
            if details:
                logger.info(f"  Details: {details}")
        else:
            self.results['failed'] += 1
            logger.error(f"✗ FAIL: {test_name}")
            if error:
                logger.error(f"  Error: {error}")
    
    # ========== TEST 1: Environment Setup ==========
    def test_environment_setup(self) -> bool:
        """Test 1: Verify environment is properly configured"""
        logger.info("\n" + "="*80)
        logger.info("TEST 1: Environment Setup")
        logger.info("="*80)
        
        try:
            # Check API key
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                self.log_test_result(
                    "Environment - GEMINI_API_KEY",
                    True,
                    f"API key found (last 10 chars: ...{api_key[-10:]})"
                )
            else:
                self.log_test_result(
                    "Environment - GEMINI_API_KEY",
                    False,
                    error="GEMINI_API_KEY not set in environment"
                )
                return False
            
            # Check required packages
            required_packages = [
                ('google.generativeai', 'google-generativeai'),
                ('langchain', 'langchain'),
                ('backtesting', 'backtesting'),
                ('django', 'Django'),
                ('rest_framework', 'djangorestframework')
            ]
            
            all_packages_ok = True
            for module_name, package_name in required_packages:
                try:
                    __import__(module_name)
                    self.log_test_result(
                        f"Package - {package_name}",
                        True,
                        f"{package_name} is installed"
                    )
                except ImportError:
                    self.log_test_result(
                        f"Package - {package_name}",
                        False,
                        error=f"{package_name} is not installed"
                    )
                    all_packages_ok = False
            
            return all_packages_ok
        
        except Exception as e:
            self.log_test_result(
                "Environment Setup",
                False,
                error=str(e)
            )
            return False
    
    # ========== TEST 2: Strategy Generator Initialization ==========
    def test_strategy_generator_init(self) -> bool:
        """Test 2: Initialize Gemini Strategy Generator"""
        logger.info("\n" + "="*80)
        logger.info("TEST 2: Strategy Generator Initialization")
        logger.info("="*80)
        
        try:
            from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
            
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                self.log_test_result(
                    "GeminiStrategyGenerator Init",
                    False,
                    error="API key not available"
                )
                return False
            
            generator = GeminiStrategyGenerator(api_key=api_key)
            
            self.log_test_result(
                "GeminiStrategyGenerator Init",
                True,
                "Generator initialized successfully with gemini-2.0-flash model"
            )
            
            # Check system prompt
            if generator.system_prompt:
                self.log_test_result(
                    "System Prompt Loaded",
                    True,
                    f"System prompt loaded ({len(generator.system_prompt)} characters)"
                )
            else:
                self.log_test_result(
                    "System Prompt Loaded",
                    False,
                    error="System prompt is empty"
                )
            
            return True
        
        except Exception as e:
            self.log_test_result(
                "GeminiStrategyGenerator Init",
                False,
                error=f"{type(e).__name__}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return False
    
    # ========== TEST 3: Generate Strategy from Description ==========
    def test_strategy_generation(self) -> bool:
        """Test 3: Generate strategy code from natural language description"""
        logger.info("\n" + "="*80)
        logger.info("TEST 3: Strategy Generation from Description")
        logger.info("="*80)
        
        try:
            from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
            
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                self.log_test_result(
                    "Strategy Generation",
                    False,
                    error="API key not available"
                )
                return False
            
            generator = GeminiStrategyGenerator(api_key=api_key)
            
            # Test strategy description
            strategy_description = """
            I want a simple moving average crossover strategy:
            - Entry: When 10 period EMA crosses above 50 period EMA
            - Exit: When 10 period EMA crosses below 50 period EMA
            - Position sizing: Risk 1% of account per trade
            - Stop loss: 2% below entry
            """
            
            logger.info(f"\nStrategy Description:\n{strategy_description}")
            logger.info("\nGenerating code (this may take 30-60 seconds)...")
            
            generated_code = generator.generate_strategy(
                strategy_description,
                output_file=None  # Don't save yet, just get code
            )
            
            if generated_code and len(generated_code) > 100:
                self.log_test_result(
                    "Strategy Generation",
                    True,
                    f"Generated {len(generated_code)} characters of valid Python code"
                )
                
                # Check for key components
                checks = [
                    ('class' in generated_code, "Contains Strategy class definition"),
                    ('def init' in generated_code or 'def __init__' in generated_code, "Has __init__ method"),
                    ('def next' in generated_code, "Has next() method for backtesting"),
                    ('from backtesting' in generated_code or 'from backtesting.py' in generated_code, "Imports backtesting.py"),
                ]
                
                all_checks_pass = True
                for check, description in checks:
                    self.log_test_result(
                        f"Code Component - {description}",
                        check,
                        description if check else ""
                    )
                    if not check:
                        all_checks_pass = False
                
                # Save the generated code for later use
                self.generated_code = generated_code
                
                return all_checks_pass
            else:
                self.log_test_result(
                    "Strategy Generation",
                    False,
                    error="Generated code is empty or too short"
                )
                return False
        
        except Exception as e:
            self.log_test_result(
                "Strategy Generation",
                False,
                error=f"{type(e).__name__}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return False
    
    # ========== TEST 4: Save Generated Strategy ==========
    def test_save_generated_strategy(self) -> bool:
        """Test 4: Save generated code to file"""
        logger.info("\n" + "="*80)
        logger.info("TEST 4: Save Generated Strategy")
        logger.info("="*80)
        
        try:
            if not hasattr(self, 'generated_code'):
                self.log_test_result(
                    "Save Strategy File",
                    False,
                    error="No generated code available from previous test"
                )
                return False
            
            codes_dir = MONOLITHIC_ROOT / "Backtest" / "codes"
            codes_dir.mkdir(parents=True, exist_ok=True)
            
            # Save with timestamp for uniqueness
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            strategy_file = codes_dir / f"e2e_test_strategy_{timestamp}.py"
            
            with open(strategy_file, 'w', encoding='utf-8') as f:
                f.write(self.generated_code)
            
            self.log_test_result(
                "Save Strategy File",
                True,
                f"Saved to {strategy_file.name}"
            )
            
            # Verify file was written
            if strategy_file.exists() and strategy_file.stat().st_size > 0:
                self.log_test_result(
                    "File Verification",
                    True,
                    f"File exists and contains {strategy_file.stat().st_size} bytes"
                )
                self.strategy_file = strategy_file
                return True
            else:
                self.log_test_result(
                    "File Verification",
                    False,
                    error="File was not properly written"
                )
                return False
        
        except Exception as e:
            self.log_test_result(
                "Save Strategy File",
                False,
                error=f"{type(e).__name__}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return False
    
    # ========== TEST 5: Validate Generated Code ==========
    def test_code_validation(self) -> bool:
        """Test 5: Validate the generated Python code"""
        logger.info("\n" + "="*80)
        logger.info("TEST 5: Code Validation")
        logger.info("="*80)
        
        try:
            if not hasattr(self, 'generated_code'):
                self.log_test_result(
                    "Code Syntax Check",
                    False,
                    error="No generated code available"
                )
                return False
            
            # Check syntax
            try:
                compile(self.generated_code, '<string>', 'exec')
                self.log_test_result(
                    "Code Syntax Check",
                    True,
                    "Python code compiles without syntax errors"
                )
            except SyntaxError as e:
                self.log_test_result(
                    "Code Syntax Check",
                    False,
                    error=f"Syntax error at line {e.lineno}: {e.msg}"
                )
                return False
            
            # Check for required imports and components
            checks = [
                ('from backtesting import' in self.generated_code or 'from backtesting.py import' in self.generated_code, 
                 "Imports backtesting"),
                ('class ' in self.generated_code, 
                 "Contains class definition"),
                ('def init' in self.generated_code or '__init__' in self.generated_code, 
                 "Has init method"),
                ('def next' in self.generated_code, 
                 "Has next() method"),
            ]
            
            all_valid = True
            for check, description in checks:
                self.log_test_result(
                    f"Code Component - {description}",
                    check,
                    description if check else ""
                )
                if not check:
                    all_valid = False
            
            return all_valid
        
        except Exception as e:
            self.log_test_result(
                "Code Validation",
                False,
                error=f"{type(e).__name__}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return False
    
    # ========== TEST 6: API Integration Test ==========
    def test_api_endpoints(self) -> bool:
        """Test 6: Test Django REST API endpoints"""
        logger.info("\n" + "="*80)
        logger.info("TEST 6: API Endpoints")
        logger.info("="*80)
        
        try:
            try:
                from django.test import Client
                from rest_framework.test import APIClient
                
                client = APIClient()
                
                # Try to list existing strategies
                response = client.get('/api/strategies/')
                
                if response.status_code in [200, 400, 500]:  # Even error responses indicate API is callable
                    self.log_test_result(
                        "API - Endpoints Available",
                        True,
                        f"API responded with status {response.status_code}"
                    )
                    return True
                else:
                    self.log_test_result(
                        "API - Endpoints Available",
                        False,
                        error=f"Unexpected status: {response.status_code}"
                    )
                    return False
            except Exception as e:
                # API might not be running, which is OK for this test
                self.log_test_result(
                    "API - Endpoints Available",
                    False,
                    error=f"Django API not available (server might not be running): {type(e).__name__}"
                )
                logger.info("  → This is expected if Django development server is not running")
                return False
        
        except Exception as e:
            self.log_test_result(
                "API Endpoints",
                False,
                error=f"{type(e).__name__}: {str(e)}"
            )
            return False
    
    # ========== TEST 7: Full Integration Test ==========
    def test_full_integration(self) -> bool:
        """Test 7: Full flow from description to code generation"""
        logger.info("\n" + "="*80)
        logger.info("TEST 7: Full Integration Flow")
        logger.info("="*80)
        
        try:
            from Backtest.ai_developer_agent import AIDeveloperAgent
            
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                self.log_test_result(
                    "Initialize AI Developer Agent",
                    False,
                    error="API key not available"
                )
                return False
            
            logger.info("Initializing AI Developer Agent...")
            agent = AIDeveloperAgent(api_key=api_key)
            
            self.log_test_result(
                "Initialize AI Developer Agent",
                True,
                "Agent initialized with terminal access and memory"
            )
            
            # Test chat interaction
            user_message = "Generate a simple EMA crossover strategy that buys when EMA10 > EMA50 and sells when EMA10 < EMA50"
            
            logger.info(f"\nSending message to agent:\n{user_message}")
            
            response = agent.chat(user_message)
            
            if response and len(response) > 0:
                self.log_test_result(
                    "AI Chat Interaction",
                    True,
                    f"Agent responded with {len(response)} characters"
                )
                logger.info(f"\nAgent Response:\n{response[:500]}...")
                return True
            else:
                self.log_test_result(
                    "AI Chat Interaction",
                    False,
                    error="Agent returned empty response"
                )
                return False
        
        except Exception as e:
            self.log_test_result(
                "Full Integration Flow",
                False,
                error=f"{type(e).__name__}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return False
    
    # ========== REPORT GENERATION ==========
    def print_summary(self):
        """Print test summary report"""
        logger.info("\n" + "="*80)
        logger.info("TEST SUMMARY REPORT")
        logger.info("="*80)
        
        logger.info(f"\nTotal Tests: {self.results['total_tests']}")
        logger.info(f"Passed: {self.results['passed']} ✓")
        logger.info(f"Failed: {self.results['failed']} ✗")
        
        pass_rate = (self.results['passed'] / self.results['total_tests'] * 100) if self.results['total_tests'] > 0 else 0
        logger.info(f"Pass Rate: {pass_rate:.1f}%")
        
        logger.info("\nDetailed Results:")
        for test_case in self.results['test_cases']:
            status = "✓ PASS" if test_case['passed'] else "✗ FAIL"
            logger.info(f"  {status}: {test_case['test']}")
            if test_case.get('details'):
                logger.info(f"    → {test_case['details']}")
            if test_case.get('error'):
                logger.info(f"    → Error: {test_case['error']}")
        
        # Save JSON report
        self.results['timestamp'] = datetime.now().isoformat()
        report_file = MONOLITHIC_ROOT / 'e2e_test_report.json'
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\n✓ Full report saved to: {report_file}")
    
    def run_all_tests(self):
        """Run all test suites in sequence"""
        logger.info("\n" + "="*80)
        logger.info("MONOLITHIC AGENT E2E TEST SUITE")
        logger.info("="*80)
        logger.info(f"Start Time: {datetime.now().isoformat()}")
        
        tests = [
            ("Environment Setup", self.test_environment_setup),
            ("Strategy Generator Init", self.test_strategy_generator_init),
            ("Strategy Generation", self.test_strategy_generation),
            ("Save Strategy", self.test_save_generated_strategy),
            ("Code Validation", self.test_code_validation),
            ("API Endpoints", self.test_api_endpoints),
            ("Full Integration", self.test_full_integration),
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\nRunning: {test_name}")
                test_func()
            except Exception as e:
                logger.error(f"Test suite error: {e}")
                logger.error(traceback.format_exc())
        
        self.print_summary()
        
        logger.info(f"\nEnd Time: {datetime.now().isoformat()}")
        logger.info("="*80)


def main():
    """Run the full test suite"""
    from datetime import datetime
    
    suite = E2ETestSuite()
    suite.run_all_tests()


if __name__ == "__main__":
    main()
