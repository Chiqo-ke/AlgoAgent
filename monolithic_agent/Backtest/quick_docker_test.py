"""
Quick Docker Sandbox Test - Fast execution
"""
from pathlib import Path
from sandbox_orchestrator import SandboxRunner

print("="*60)
print("QUICK DOCKER SANDBOX TEST")
print("="*60)

# Test 1: Simple execution
print("\n1. Testing simple Python execution...")
test_file = Path("quick_test.py")
test_file.write_text('print("Hello from Docker!\\n2+2 =", 2+2)')

try:
    runner = SandboxRunner(workspace_root=Path(".."))
    print("   Runner initialized ✅")
    
    result = runner.run_python_script(str(test_file), timeout=10)
    print(f"   Status: {result.status}")
    print(f"   Output: {result.stdout}")
    
    if result.status == "success":
        print("   ✅ Docker sandbox WORKING!")
    else:
        print(f"   ❌ Failed: {result.stderr}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
finally:
    if test_file.exists():
        test_file.unlink()

print("\n" + "="*60)
