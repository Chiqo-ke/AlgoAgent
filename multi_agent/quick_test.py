"""Quick test runner - bypasses Docker for speed."""
import sys
import subprocess
from pathlib import Path

# Find one test file
test_dir = Path(__file__).parent / "tests"
test_files = list(test_dir.glob("test_ai_strategy_*.py"))

if not test_files:
    print("No test files found")
    sys.exit(1)

# Test just the first one
test_file = test_files[0]
print(f"Testing: {test_file.name}")
print()

result = subprocess.run(
    [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
    capture_output=True,
    text=True,
    timeout=30
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

print()
print(f"Exit code: {result.returncode}")
print("✅ PASSED" if result.returncode == 0 else "❌ FAILED")
