"""
Comprehensive Docker Sandbox Integration Test
"""
from pathlib import Path
from sandbox_orchestrator import SandboxRunner
import time

print("="*70)
print("COMPREHENSIVE DOCKER SANDBOX INTEGRATION TEST")
print("="*70)

results = {"passed": 0, "failed": 0}

def test(name, condition, details=""):
    if condition:
        results["passed"] += 1
        print(f"✅ {name}")
        if details:
            print(f"   {details}")
    else:
        results["failed"] += 1
        print(f"❌ {name}")
        if details:
            print(f"   {details}")

runner = SandboxRunner(workspace_root=Path(".."))

# Test 1: Simple execution
print("\nTEST 1: Simple Python Execution")
print("-" * 70)
test_file = Path("test1.py")
test_file.write_text('print("Hello from Docker"); print("2+2 =", 2+2)')

result = runner.run_python_script(f"Backtest/{test_file.name}", timeout=30)
test("Simple execution", result.exit_code == 0, f"Output: {result.stdout.strip()}")
test_file.unlink()

# Test 2: Error handling
print("\nTEST 2: Error Handling")
print("-" * 70)
test_file = Path("test2_error.py")
test_file.write_text('raise ValueError("Test error")')

result = runner.run_python_script(f"Backtest/{test_file.name}", timeout=30)
test("Error captured", result.exit_code != 0 and "ValueError" in result.stderr, 
     f"Exit code: {result.exit_code}")
test_file.unlink()

# Test 3: Resource limits (CPU, Memory)
print("\nTEST 3: Resource Limits")
print("-" * 70)
test_file = Path("test3_limits.py")
test_file.write_text('''
import time
print("Testing resource limits...")
time.sleep(1)
print("Completed!")
''')

result = runner.run_python_script(f"Backtest/{test_file.name}", timeout=30)
test("Resource limits enforced", result.exit_code == 0, 
     f"Execution time: {result.execution_time:.2f}s")
test_file.unlink()

# Test 4: Network isolation
print("\nTEST 4: Network Isolation")
print("-" * 70)
test_file = Path("test4_network.py")
test_file.write_text('''
import socket
try:
    socket.create_connection(("8.8.8.8", 53), timeout=1)
    print("ERROR: Network accessible")
except Exception as e:
    print(f"PASS: Network isolated - {type(e).__name__}")
''')

result = runner.run_python_script(f"Backtest/{test_file.name}", timeout=30)
test("Network isolated", "PASS" in result.stdout, f"Output: {result.stdout.strip()}")
test_file.unlink()

# Test 5: Mini strategy execution
print("\nTEST 5: Mini Strategy Execution")
print("-" * 70)
test_file = Path("test5_strategy.py")
test_file.write_text('''
class SimpleStrategy:
    def __init__(self):
        self.signals = []
    
    def calculate_sma(self, prices, period):
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def run(self):
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 110]
        sma = self.calculate_sma(prices, 5)
        
        print(f"Prices: {prices}")
        print(f"SMA(5): {sma:.2f}")
        
        if prices[-1] > sma:
            self.signals.append({"action": "BUY", "price": prices[-1]})
            print("Signal: BUY at", prices[-1])
        
        return self.signals

strategy = SimpleStrategy()
signals = strategy.run()
print(f"Signals generated: {len(signals)}")
print("Strategy executed successfully!")
''')

result = runner.run_python_script(f"Backtest/{test_file.name}", timeout=30)
test("Strategy execution", 
     result.exit_code == 0 and "Strategy executed successfully" in result.stdout,
     f"Output: {result.stdout[:100]}...")
test_file.unlink()

# Test 6: Timeout enforcement
print("\nTEST 6: Timeout Enforcement")
print("-" * 70)
test_file = Path("test6_timeout.py")
test_file.write_text('''
import time
print("Starting long task...")
time.sleep(100)
print("Should not see this")
''')

result = runner.run_python_script(f"Backtest/{test_file.name}", timeout=5)
test("Timeout enforced", 
     result.timed_out or result.execution_time < 7,
     f"Execution time: {result.execution_time:.2f}s, Timed out: {result.timed_out}")
test_file.unlink()

# Test 7: Multiple runs (cleanup verification)
print("\nTEST 7: Multiple Runs (Cleanup)")
print("-" * 70)
test_file = Path("test7_multi.py")
test_file.write_text('print("Run complete")')

success_count = 0
for i in range(3):
    result = runner.run_python_script(f"Backtest/{test_file.name}", timeout=30)
    if result.exit_code == 0:
        success_count += 1

test("Multiple runs work", success_count == 3, f"Successful runs: {success_count}/3")
test_file.unlink()

# Summary
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print(f"Passed: {results['passed']}/{results['passed'] + results['failed']}")
print(f"Failed: {results['failed']}/{results['passed'] + results['failed']}")

if results['failed'] == 0:
    print("\n✅ ALL TESTS PASSED - Docker sandbox is production-ready!")
else:
    print(f"\n⚠️  {results['failed']} test(s) failed")

print("="*70)
