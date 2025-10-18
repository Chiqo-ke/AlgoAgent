"""
Backtest Module Cleanup Script
===============================

Removes outdated documentation and redundant files from previous implementations.

This script will:
1. Remove old SUMMARY.md files (implementation notes)
2. Remove redundant documentation
3. Keep current MT5 integration docs
4. Keep core reference docs
5. Create a backup list before deletion

Run with --dry-run to see what would be deleted without actually deleting.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import sys

# Files to REMOVE (old summaries and redundant docs)
FILES_TO_REMOVE = [
    # Old implementation summaries
    "IMPLEMENTATION_COMPLETE.md",
    "IMPLEMENTATION_SUMMARY.md",
    "IMPORT_FIX_SUMMARY.md",
    "DATA_LOADER_SUMMARY.md",
    "GEMINI_INTEGRATION_SUMMARY.md",
    
    # Redundant MT5 doc (keeping README_MT5_INTEGRATION.md as the main summary)
    "MT5_INTEGRATION_SUMMARY.md",
    
    # Redundant column documentation
    "COLUMN_NAMING_STANDARD.md",
    "QUICK_REFERENCE_COLUMNS.md",
]

# Optional: Example strategies to remove (set REMOVE_OLD_STRATEGIES=True to enable)
REMOVE_OLD_STRATEGIES = False  # Set to True to remove old example strategies

OLD_STRATEGY_FILES = [
    "ema_strategy.py",           # Old generated EMA strategy
    "rsi_strategy.py",           # Old generated RSI strategy
    "my_strategy.py",            # Old generic test strategy
    "test_generated_strategy.py", # Tests for removed strategies
]

# Files to KEEP (for reference)
FILES_TO_KEEP = [
    "MT5_INTEGRATION_GUIDE.md",
    "MT5_QUICK_REFERENCE.md",
    "README_MT5_INTEGRATION.md",
    "README.md",
    "API_REFERENCE.md",
    "GEMINI_INTEGRATION_GUIDE.md",
    "QUICK_START_GUIDE.md",
    "STRATEGY_TEMPLATE.md",
    "SYSTEM_PROMPT.md",
    "example_mt5_integration.py",
    "example_strategy.py",
]


def create_backup_list(backtest_dir: Path, files: list) -> Path:
    """Create a list of files being deleted for reference"""
    backup_file = backtest_dir / f"DELETED_FILES_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(backup_file, 'w') as f:
        f.write("Files removed during cleanup\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        
        for file in files:
            if file.exists():
                f.write(f"{file.name}\n")
                f.write(f"  Path: {file}\n")
                f.write(f"  Size: {file.stat().st_size} bytes\n\n")
    
    return backup_file


def cleanup_backtest_module(dry_run: bool = False):
    """Clean up outdated files from Backtest module"""
    backtest_dir = Path(__file__).parent
    
    print("=" * 70)
    print("BACKTEST MODULE CLEANUP")
    print("=" * 70)
    print(f"Directory: {backtest_dir}")
    print(f"Mode: {'DRY RUN (no files will be deleted)' if dry_run else 'LIVE (files will be deleted)'}")
    print()
    
    # Determine which files to remove
    files_to_remove = FILES_TO_REMOVE.copy()
    if REMOVE_OLD_STRATEGIES:
        files_to_remove.extend(OLD_STRATEGY_FILES)
        print("⚠ Old strategy files will be removed (REMOVE_OLD_STRATEGIES=True)")
        print()
    
    # Find files to remove
    files_found = []
    files_not_found = []
    
    for filename in files_to_remove:
        filepath = backtest_dir / filename
        if filepath.exists():
            files_found.append(filepath)
        else:
            files_not_found.append(filename)
    
    # Report findings
    print(f"Files to remove: {len(files_found)}")
    print(f"Files not found: {len(files_not_found)}")
    print()
    
    if files_found:
        print("FILES TO BE REMOVED:")
        print("-" * 70)
        for file in files_found:
            size = file.stat().st_size
            print(f"  - {file.name:<40} ({size:>8,} bytes)")
        print()
    
    if files_not_found:
        print("FILES NOT FOUND (already removed?):")
        print("-" * 70)
        for filename in files_not_found:
            print(f"  - {filename}")
        print()
    
    # Show files being kept
    print("KEY FILES BEING KEPT:")
    print("-" * 70)
    kept_count = 0
    for filename in FILES_TO_KEEP:
        filepath = backtest_dir / filename
        if filepath.exists():
            print(f"  ✓ {filename}")
            kept_count += 1
    print(f"\nTotal kept: {kept_count}")
    print()
    
    # Calculate space savings
    total_size = sum(f.stat().st_size for f in files_found)
    print(f"Total space to be freed: {total_size:,} bytes ({total_size/1024:.2f} KB)")
    print()
    
    # Perform deletion
    if not dry_run and files_found:
        print("=" * 70)
        response = input("Proceed with deletion? (yes/no): ").strip().lower()
        
        if response == 'yes':
            # Create backup list
            backup_file = create_backup_list(backtest_dir, files_found)
            print(f"\n✓ Backup list created: {backup_file.name}")
            
            # Delete files
            deleted_count = 0
            failed_count = 0
            
            print("\nDeleting files...")
            for file in files_found:
                try:
                    file.unlink()
                    print(f"  ✓ Deleted: {file.name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  ✗ Failed to delete {file.name}: {e}")
                    failed_count += 1
            
            print()
            print("=" * 70)
            print("CLEANUP COMPLETE")
            print("=" * 70)
            print(f"Files deleted: {deleted_count}")
            print(f"Files failed: {failed_count}")
            print(f"Space freed: {total_size:,} bytes ({total_size/1024:.2f} KB)")
            print(f"Backup list: {backup_file.name}")
            print()
            print("✓ Backtest module cleaned up successfully!")
            
        else:
            print("\nCleanup cancelled.")
    
    elif dry_run:
        print("=" * 70)
        print("DRY RUN COMPLETE - No files were deleted")
        print("=" * 70)
        print()
        print("To perform actual cleanup, run without --dry-run flag:")
        print("  python cleanup_old_files.py")
        print()


def main():
    """Main entry point"""
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    
    try:
        cleanup_backtest_module(dry_run=dry_run)
    except KeyboardInterrupt:
        print("\n\nCleanup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during cleanup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
