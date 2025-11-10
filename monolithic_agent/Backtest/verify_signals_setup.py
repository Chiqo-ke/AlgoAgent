# Verify MT5 Signals Directory Setup
# Quick check to ensure everything is configured correctly

from pathlib import Path
import sys

# MT5 Signals directory
SIGNALS_DIR = Path(r"C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\signals")

def verify_setup():
    """Verify MT5 signals directory setup"""
    print("=" * 70)
    print("MT5 Signals Directory Verification")
    print("=" * 70)
    
    # Check if directory exists
    print(f"\n1. Checking directory: {SIGNALS_DIR}")
    if SIGNALS_DIR.exists():
        print("   ✓ Directory exists")
    else:
        print("   ✗ Directory does NOT exist")
        print("\n   Creating directory...")
        try:
            SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
            print("   ✓ Directory created successfully")
        except Exception as e:
            print(f"   ✗ Failed to create directory: {e}")
            return False
    
    # Check if writable
    print("\n2. Checking write permissions...")
    test_file = SIGNALS_DIR / "test_write.txt"
    try:
        test_file.write_text("test")
        test_file.unlink()
        print("   ✓ Directory is writable")
    except Exception as e:
        print(f"   ✗ Directory is NOT writable: {e}")
        return False
    
    # List existing signal files
    print("\n3. Listing existing signal files...")
    csv_files = list(SIGNALS_DIR.glob("*.csv"))
    json_files = list(SIGNALS_DIR.glob("*.json"))
    
    if csv_files or json_files:
        print(f"   Found {len(csv_files)} CSV files and {len(json_files)} JSON files")
        if csv_files:
            print("\n   CSV Files:")
            for f in csv_files[:5]:  # Show first 5
                print(f"   - {f.name}")
            if len(csv_files) > 5:
                print(f"   ... and {len(csv_files) - 5} more")
        if json_files:
            print("\n   JSON Files:")
            for f in json_files[:5]:  # Show first 5
                print(f"   - {f.name}")
            if len(json_files) > 5:
                print(f"   ... and {len(json_files) - 5} more")
    else:
        print("   No signal files found (this is OK for fresh setup)")
    
    # Check parent directories
    print("\n4. Verifying MT5 installation...")
    mt5_root = SIGNALS_DIR.parents[2]  # Go up to Terminal folder
    if mt5_root.exists():
        print(f"   ✓ MT5 Terminal found at: {mt5_root}")
    else:
        print(f"   ✗ MT5 Terminal NOT found at: {mt5_root}")
        return False
    
    # Summary
    print("\n" + "=" * 70)
    print("✓ Setup Verification PASSED")
    print("=" * 70)
    print("\nYou can now:")
    print("1. Run Python backtests with enable_mt5_export=True")
    print("2. Signals will be saved automatically to this directory")
    print("3. MQL5 EA will read signals from: Experts/signals/")
    print("\nNext step: Run a backtest to generate signals")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    try:
        success = verify_setup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        sys.exit(1)
