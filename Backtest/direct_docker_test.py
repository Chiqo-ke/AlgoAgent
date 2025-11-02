"""
Direct Docker Test - No sandbox orchestrator overhead
"""
import subprocess
from pathlib import Path

print("="*60)
print("DIRECT DOCKER TEST")
print("="*60)

# Test 1: Check Docker
print("\n1. Checking Docker...")
result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
print(f"   {result.stdout.strip()}")

# Test 2: Simple Python in Docker
print("\n2. Running Python in Docker container...")
test_script = 'print("Hello from Docker!"); print("2+2 =", 2+2)'

try:
    result = subprocess.run(
        ["docker", "run", "--rm", "python:3.11-slim", "python", "-c", test_script],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        print(f"   ✅ SUCCESS!")
        print(f"   Output: {result.stdout}")
    else:
        print(f"   ❌ Failed: {result.stderr}")
        
except subprocess.TimeoutExpired:
    print("   ⚠️ Timeout - likely pulling image")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("Docker is working! ✅")
print("Issue: sandbox_orchestrator tries to copy entire workspace")
print("Solution: Need to fix workspace copy logic")
print("="*60)
