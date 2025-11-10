"""
Debug Docker Sandbox Test
"""
from pathlib import Path
from sandbox_orchestrator import SandboxRunner, SandboxConfig, SandboxOrchestrator
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print("="*60)
print("DEBUG DOCKER SANDBOX TEST")
print("="*60)

# Test 1: Create test file
print("\n1. Creating test file...")
test_file = Path("debug_test.py")
test_file.write_text('print("Hello from Docker!\\n2+2 =", 2+2)')
print(f"   ✅ Created: {test_file.absolute()}")

# Test 2: Initialize
print("\n2. Initializing sandbox...")
try:
    runner = SandboxRunner(workspace_root=Path(".."))
    print(f"   ✅ Runner initialized")
    print(f"   Workspace: {runner.orchestrator.workspace_root}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Run with longer timeout and debugging
print("\n3. Running script (timeout=60s)...")
# Script path should be relative to workspace root (AlgoAgent)
script_rel_path = f"Backtest/{test_file.name}"
print(f"   Script relative path: {script_rel_path}")
try:
    result = runner.run_python_script(script_rel_path, timeout=60)
    print(f"   Status: {result.status}")
    print(f"   Exit code: {result.exit_code}")
    print(f"   Execution time: {result.execution_time:.2f}s")
    print(f"   Stdout: {result.stdout}")
    print(f"   Stderr: {result.stderr}")
    
    if result.status == "completed" and result.exit_code == 0:
        print("\n   ✅ SUCCESS! Docker sandbox working!")
    else:
        print(f"\n   ❌ Failed: {result.status}")
        
except Exception as e:
    print(f"   ❌ Exception: {e}")
    import traceback
    traceback.print_exc()
finally:
    if test_file.exists():
        test_file.unlink()

print("\n" + "="*60)
