"""
Test script for the new unified strategy generation endpoint
Tests Copilot integration with full execution and auto-fix features
"""

import requests
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/strategies/api/generate_strategy_unified/"

# Test strategy specification (canonical JSON format)
test_strategy = {
    "canonical_json": {
        "strategy_name": "Simple RSI Strategy",
        "description": "A basic RSI-based mean reversion strategy",
        "timeframe": "1d",
        "entry_rules": [
            {
                "description": "Buy when RSI(14) crosses below 30 (oversold)",
                "type": "indicator_condition",
                "indicator": "RSI",
                "period": 14,
                "operator": "<",
                "value": 30
            }
        ],
        "exit_rules": [
            {
                "description": "Sell when RSI(14) crosses above 70 (overbought)",
                "type": "indicator_condition",
                "indicator": "RSI",
                "period": 14,
                "operator": ">",
                "value": 70
            }
        ],
        "risk_management": {
            "stop_loss": "15 pips",
            "take_profit": "40 pips",
            "position_sizing": "fixed"
        },
        "indicators": [
            {
                "name": "RSI",
                "type": "momentum",
                "period": 14
            }
        ]
    },
    "strategy_name": "RSI_Mean_Reversion_Strategy",
    "ai_provider": "copilot",  # Use Copilot!
    "test_config": {
        "symbol": "AAPL",
        "period": "1y",
        "interval": "1d"
    },
    "auto_execute": False,  # Disable execution for now to test generation only
    "auto_fix": False,
    "max_fix_attempts": 3
}

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def print_result(key, value, indent=0):
    """Print a key-value pair with indentation"""
    prefix = "  " * indent
    if isinstance(value, (dict, list)):
        print(f"{prefix}{key}: {json.dumps(value, indent=2)}")
    else:
        print(f"{prefix}{key}: {value}")

def test_unified_endpoint():
    """Test the unified strategy generation endpoint"""
    
    print_section("Testing Unified Strategy Generation Endpoint")
    print(f"Endpoint: {API_URL}")
    print(f"Strategy: {test_strategy['strategy_name']}")
    print(f"AI Provider: {test_strategy['ai_provider']}")
    print(f"Auto Execute: {test_strategy['auto_execute']}")
    print(f"Auto Fix: {test_strategy['auto_fix']}")
    
    print_section("Sending Request")
    start_time = datetime.now()
    
    try:
        response = requests.post(
            API_URL,
            json=test_strategy,
            headers={'Content-Type': 'application/json'},
            timeout=120  # 2 minute timeout for generation + execution
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"Status Code: {response.status_code}")
        print(f"Duration: {duration:.2f} seconds")
        
        if response.status_code == 200:
            print_section("✅ SUCCESS - Response Data")
            data = response.json()
            
            # Print key information
            print_result("Success", data.get('success'))
            print_result("AI Provider Used", data.get('ai_provider'))
            print_result("File Name", data.get('file_name'))
            print_result("File Path", data.get('file_path'))
            print_result("Code Length", len(data.get('strategy_code', '')))
            
            # Execution results
            print_section("Execution Results")
            execution = data.get('execution', {})
            print_result("Attempted", execution.get('attempted'))
            print_result("Success", execution.get('success'))
            print_result("Validation Status", execution.get('validation_status'))
            
            if execution.get('metrics'):
                print("\nMetrics:")
                for key, value in execution['metrics'].items():
                    print_result(key, value, indent=1)
            
            if execution.get('error_message'):
                print_result("Error Message", execution.get('error_message'))
            
            # Error fixing results
            print_section("Error Fixing Results")
            error_fixing = data.get('error_fixing', {})
            print_result("Attempted", error_fixing.get('attempted'))
            print_result("Attempts", error_fixing.get('attempts'))
            print_result("Final Status", error_fixing.get('final_status'))
            
            if error_fixing.get('history'):
                print("\nFix History:")
                for i, fix in enumerate(error_fixing['history'], 1):
                    print(f"\n  Attempt {i}:")
                    print_result("Error Type", fix.get('error_type'), indent=2)
                    print_result("Success", fix.get('success'), indent=2)
                    print_result("Description", fix.get('description'), indent=2)
            
            # Validation checks
            print_section("Validation Checks")
            
            # Check if Copilot was used
            if data.get('ai_provider') == 'copilot':
                print("✅ Copilot was used for generation")
            else:
                print(f"⚠️  Expected 'copilot' but got '{data.get('ai_provider')}'")
            
            # Check if code was generated
            code = data.get('strategy_code', '')
            if code:
                print(f"✅ Code generated ({len(code)} characters)")
                
                # Check for SimBroker imports
                if 'from Backtest.copilot_strategy_generator import CopilotStrategyGenerator' in code:
                    print("✅ Contains Copilot imports")
                else:
                    print("⚠️  Missing Copilot imports")
                
                if 'BacktestConfig' in code:
                    print("✅ Uses BacktestConfig")
                else:
                    print("⚠️  Missing BacktestConfig")
                
                # Check for RSI logic
                if 'rsi' in code.lower() or 'RSI' in code:
                    print("✅ Contains RSI logic")
                else:
                    print("⚠️  Missing RSI logic")
            else:
                print("❌ No code generated")
            
            # Check execution success
            if execution.get('success'):
                print("✅ Strategy executed successfully")
                if execution.get('metrics'):
                    print(f"   - Trades: {execution['metrics'].get('num_trades')}")
                    print(f"   - Return: {execution['metrics'].get('return_pct'):.2f}%")
            else:
                print("⚠️  Execution failed or not attempted")
            
            # Save generated code to file for inspection
            if code:
                output_file = f"test_unified_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                print(f"\n📝 Generated code saved to: {output_file}")
            
            print_section("Overall Result")
            if (data.get('ai_provider') == 'copilot' and 
                code and 
                execution.get('validation_status') in ['passed', 'pending']):
                print("🎉 TEST PASSED - Unified endpoint working correctly with Copilot!")
            else:
                print("⚠️  TEST INCOMPLETE - Some checks failed")
            
        else:
            print_section("❌ ERROR - Request Failed")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print_section("❌ ERROR - Request Timeout")
        print("The request took longer than 2 minutes")
    except requests.exceptions.ConnectionError:
        print_section("❌ ERROR - Connection Failed")
        print("Could not connect to the server. Is Django running on port 8000?")
    except Exception as e:
        print_section("❌ ERROR - Exception")
        print(f"Error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    test_unified_endpoint()
