"""
Test Report Validator - Validates test_report.json against schema.

Usage:
    python validate_test_report.py artifacts/test_report.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from jsonschema import validate, ValidationError


# Test report schema (matches pytest-json-report format)
TEST_REPORT_SCHEMA = {
    "type": "object",
    "required": ["summary", "tests"],
    "properties": {
        "summary": {
            "type": "object",
            "required": ["total", "passed", "failed"],
            "properties": {
                "total": {"type": "integer", "minimum": 0},
                "passed": {"type": "integer", "minimum": 0},
                "failed": {"type": "integer", "minimum": 0},
                "skipped": {"type": "integer", "minimum": 0},
                "error": {"type": "integer", "minimum": 0},
                "duration": {"type": "number", "minimum": 0}
            }
        },
        "tests": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["nodeid", "outcome"],
                "properties": {
                    "nodeid": {"type": "string"},
                    "outcome": {"type": "string", "enum": ["passed", "failed", "skipped", "error"]},
                    "duration": {"type": "number"},
                    "call": {"type": "object"}
                }
            }
        }
    }
}


def validate_test_report(report_path: Path) -> Dict:
    """
    Validate test report against schema.
    
    Args:
        report_path: Path to test_report.json
        
    Returns:
        Validation result dict:
            - valid: bool
            - errors: List[str]
            - summary: Dict (if valid)
    """
    if not report_path.exists():
        return {
            'valid': False,
            'errors': [f'Test report not found: {report_path}'],
            'summary': None
        }
    
    try:
        with open(report_path) as f:
            report = json.load(f)
    except json.JSONDecodeError as e:
        return {
            'valid': False,
            'errors': [f'Invalid JSON: {e}'],
            'summary': None
        }
    
    # Validate schema
    errors = []
    try:
        validate(instance=report, schema=TEST_REPORT_SCHEMA)
    except ValidationError as e:
        errors.append(f'Schema validation failed: {e.message}')
    
    # Additional validations
    if 'summary' in report:
        summary = report['summary']
        
        # Check totals match
        expected_total = summary.get('passed', 0) + summary.get('failed', 0) + summary.get('skipped', 0)
        if summary.get('total', 0) != expected_total:
            errors.append(
                f"Total mismatch: {summary['total']} != {expected_total} "
                f"(passed + failed + skipped)"
            )
        
        # Check for failures
        if summary.get('failed', 0) > 0:
            errors.append(f"Tests failed: {summary['failed']} failures")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'summary': report.get('summary')
    }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_test_report.py <test_report.json>")
        sys.exit(1)
    
    report_path = Path(sys.argv[1])
    result = validate_test_report(report_path)
    
    print("\n" + "="*60)
    print("TEST REPORT VALIDATION")
    print("="*60)
    
    if result['valid']:
        print("✅ VALID")
        if result['summary']:
            s = result['summary']
            print(f"\nSummary:")
            print(f"  Total: {s.get('total', 0)}")
            print(f"  Passed: {s.get('passed', 0)}")
            print(f"  Failed: {s.get('failed', 0)}")
            print(f"  Duration: {s.get('duration', 0):.2f}s")
        sys.exit(0)
    else:
        print("❌ INVALID")
        print(f"\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()
