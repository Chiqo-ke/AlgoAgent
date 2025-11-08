"""
Quick test script to demonstrate CLI with AI agent execution
"""

import subprocess
import sys
from pathlib import Path

# Get paths
cli_path = Path(__file__).parent / "cli.py"
python_exe = Path(__file__).parent.parent / ".venv" / "Scripts" / "python.exe"

print("="*70)
print("  TESTING CLI WITH AI AGENT EXECUTION")
print("="*70)
print()

# Test 1: Submit request
print("TEST 1: Submit request with AI")
print("-" * 70)
result = subprocess.run(
    [str(python_exe), str(cli_path), "--request", "Create RSI strategy"],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.returncode != 0:
    print("STDERR:", result.stderr)

# Extract workflow ID from output
workflow_id = None
for line in result.stdout.split('\n'):
    if 'Workflow loaded:' in line:
        workflow_id = line.split('Workflow loaded:')[1].strip()
        break

if workflow_id:
    print(f"\n✓ Workflow created: {workflow_id}")
    print()
    
    # Test 2: Execute workflow
    print(f"TEST 2: Execute workflow {workflow_id}")
    print("-" * 70)
    result = subprocess.run(
        [str(python_exe), str(cli_path), "--execute", workflow_id],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print("STDERR:", result.stderr)
else:
    print("\n❌ Could not extract workflow ID")

print()
print("="*70)
print("  TEST COMPLETE")
print("="*70)
