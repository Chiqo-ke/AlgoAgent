"""
Determinism Checker - Verifies backtest produces same results with same seed.

Usage:
    python check_determinism.py --strategy codes/strategy.py --data fixtures/data.csv --runs 2
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict
import tempfile
import shutil


def run_backtest(strategy_file: Path, data_file: Path, output_dir: Path, seed: int) -> Dict:
    """
    Run backtest and return report.
    
    Args:
        strategy_file: Path to strategy file
        data_file: Path to data CSV
        output_dir: Output directory
        seed: RNG seed
        
    Returns:
        Report dict with metrics
    """
    cmd = [
        sys.executable,
        str(strategy_file),
        '--mode', 'backtest',
        '--data', str(data_file),
        '--out', str(output_dir),
        '--config', json.dumps({'rng_seed': seed})
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Backtest failed: {result.stderr}")
    
    # Load summary report
    summary_file = output_dir / 'summary.json'
    if not summary_file.exists():
        raise FileNotFoundError(f"Summary not found: {summary_file}")
    
    with open(summary_file) as f:
        return json.load(f)


def compare_reports(reports: List[Dict], tolerance: float = 1e-6) -> Dict:
    """
    Compare multiple reports for determinism.
    
    Args:
        reports: List of report dicts
        tolerance: Floating point tolerance
        
    Returns:
        Comparison result:
            - deterministic: bool
            - differences: List[str]
    """
    if len(reports) < 2:
        return {'deterministic': True, 'differences': []}
    
    differences = []
    base = reports[0]
    
    # Compare key metrics
    metrics = ['total_trades', 'total_pnl', 'win_rate', 'max_drawdown', 'profit_factor']
    
    for i, report in enumerate(reports[1:], start=1):
        for metric in metrics:
            base_val = base.get(metric)
            report_val = report.get(metric)
            
            if base_val is None or report_val is None:
                differences.append(f"Run {i}: Missing metric '{metric}'")
                continue
            
            # Compare with tolerance
            if isinstance(base_val, (int, float)) and isinstance(report_val, (int, float)):
                if abs(base_val - report_val) > tolerance:
                    differences.append(
                        f"Run {i}: {metric} mismatch - "
                        f"base={base_val}, run={report_val}, "
                        f"diff={abs(base_val - report_val)}"
                    )
            else:
                if base_val != report_val:
                    differences.append(
                        f"Run {i}: {metric} mismatch - "
                        f"base={base_val}, run={report_val}"
                    )
    
    return {
        'deterministic': len(differences) == 0,
        'differences': differences
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Check backtest determinism')
    parser.add_argument('--strategy', required=True, help='Strategy file path')
    parser.add_argument('--data', required=True, help='Data CSV file')
    parser.add_argument('--runs', type=int, default=2, help='Number of runs')
    parser.add_argument('--seed', type=int, default=42, help='RNG seed')
    parser.add_argument('--tolerance', type=float, default=1e-6, help='Float tolerance')
    
    args = parser.parse_args()
    
    strategy_file = Path(args.strategy)
    data_file = Path(args.data)
    
    if not strategy_file.exists():
        print(f"❌ Strategy not found: {strategy_file}")
        sys.exit(1)
    
    if not data_file.exists():
        print(f"❌ Data not found: {data_file}")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("DETERMINISM CHECK")
    print("="*60)
    print(f"Strategy: {strategy_file.name}")
    print(f"Data: {data_file.name}")
    print(f"Runs: {args.runs}")
    print(f"Seed: {args.seed}")
    print("="*60 + "\n")
    
    # Run backtests
    reports = []
    temp_dirs = []
    
    try:
        for i in range(args.runs):
            print(f"Run {i+1}/{args.runs}...", end=' ', flush=True)
            
            # Create temp output dir
            temp_dir = Path(tempfile.mkdtemp())
            temp_dirs.append(temp_dir)
            
            # Run backtest
            report = run_backtest(strategy_file, data_file, temp_dir, args.seed)
            reports.append(report)
            
            print(f"✅ (trades={report.get('total_trades', 0)}, pnl=${report.get('total_pnl', 0):.2f})")
        
        # Compare reports
        result = compare_reports(reports, tolerance=args.tolerance)
        
        print("\n" + "="*60)
        print("RESULT")
        print("="*60)
        
        if result['deterministic']:
            print("✅ DETERMINISTIC - All runs produced identical results")
            sys.exit(0)
        else:
            print("❌ NON-DETERMINISTIC - Runs produced different results")
            print("\nDifferences:")
            for diff in result['differences']:
                print(f"  - {diff}")
            sys.exit(1)
    
    finally:
        # Cleanup temp dirs
        for temp_dir in temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)


if __name__ == '__main__':
    main()
