"""Validators for test artifacts."""

import json
import re
from pathlib import Path
from typing import List, Tuple
import jsonschema

from .config import config


def validate_test_report_schema(report_path: Path) -> None:
    """
    Validate test_report.json against schema.
    
    Args:
        report_path: Path to test_report.json
        
    Raises:
        FileNotFoundError: If report file doesn't exist
        jsonschema.ValidationError: If schema validation fails
        json.JSONDecodeError: If JSON is malformed
    """
    if not report_path.exists():
        raise FileNotFoundError(f"Test report not found: {report_path}")
    
    # Load report
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    # Load schema
    schema_path = Path(__file__).parent.parent.parent / 'contracts' / 'test_report_schema.json'
    if not schema_path.exists():
        # If schema doesn't exist, do basic validation
        _validate_report_structure(report)
        return
    
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    # Validate against schema
    jsonschema.validate(instance=report, schema=schema)


def _validate_report_structure(report: dict) -> None:
    """Basic structure validation if schema file unavailable."""
    required_keys = ['summary', 'tests']
    for key in required_keys:
        if key not in report:
            raise ValueError(f"Test report missing required key: {key}")
    
    # Check summary has basic metrics
    summary = report.get('summary', {})
    if not isinstance(summary, dict):
        raise ValueError("Test report 'summary' must be a dict")


def scan_for_secrets(file_path: Path) -> List[Tuple[str, str, int]]:
    """
    Scan file for hardcoded secrets using regex patterns.
    
    Args:
        file_path: Path to file to scan
        
    Returns:
        List of (pattern_name, matched_text, line_number) tuples
    """
    if not file_path.exists():
        return []
    
    findings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        return []
    
    for line_num, line in enumerate(lines, start=1):
        for pattern in config.secret_patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                findings.append((
                    pattern[:50],  # Pattern name (truncated)
                    match.group(0)[:50],  # Matched text (truncated)
                    line_num
                ))
    
    return findings


def validate_artifacts(workspace: Path) -> Tuple[bool, List[str]]:
    """
    Validate that all required artifacts exist and are valid.
    
    Args:
        workspace: Path to workspace directory
        
    Returns:
        (success, list_of_errors)
    """
    errors = []
    
    for artifact_name in config.required_artifacts:
        artifact_path = workspace / artifact_name
        
        if not artifact_path.exists():
            errors.append(f"Missing artifact: {artifact_name}")
            continue
        
        # Check file is non-empty
        if artifact_path.stat().st_size == 0:
            errors.append(f"Empty artifact: {artifact_name}")
            continue
        
        # Additional validation for specific files
        if artifact_name == 'trades.csv':
            if not _validate_trades_csv(artifact_path):
                errors.append(f"Invalid trades.csv format")
        
        elif artifact_name == 'equity_curve.csv':
            if not _validate_equity_curve(artifact_path):
                errors.append(f"Invalid equity_curve.csv format")
        
        elif artifact_name == 'test_report.json':
            try:
                validate_test_report_schema(artifact_path)
            except Exception as e:
                errors.append(f"Invalid test_report.json: {e}")
    
    return (len(errors) == 0, errors)


def _validate_trades_csv(path: Path) -> bool:
    """Validate trades.csv has expected columns."""
    try:
        with open(path, 'r') as f:
            header = f.readline().strip()
        
        # Check for essential columns
        required_cols = ['time', 'symbol', 'action', 'volume', 'price']
        for col in required_cols:
            if col.lower() not in header.lower():
                return False
        
        return True
    except Exception:
        return False


def _validate_equity_curve(path: Path) -> bool:
    """Validate equity_curve.csv has expected format."""
    try:
        with open(path, 'r') as f:
            header = f.readline().strip()
        
        # Check for essential columns
        required_cols = ['time', 'balance', 'equity']
        for col in required_cols:
            if col.lower() not in header.lower():
                return False
        
        return True
    except Exception:
        return False
