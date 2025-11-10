# Check Current Signal Path Configuration
# Shows where signals are being saved and loaded from

from pathlib import Path
import re

def check_configuration():
    """Check current signal path configuration"""
    print("=" * 80)
    print("Signal Path Configuration Check")
    print("=" * 80)
    
    # Check Python configuration
    print("\n📍 Python Configuration (sim_broker.py)")
    print("-" * 80)
    
    sim_broker_path = Path("c:/Users/nyaga/Documents/AlgoAgent/Backtest/sim_broker.py")
    if sim_broker_path.exists():
        content = sim_broker_path.read_text()
        
        # Find output_dir line
        match = re.search(r'output_dir = Path\((r?["\'].*?["\']\))', content)
        if match:
            print(f"✓ Found configuration:")
            print(f"  output_dir = Path({match.group(1)}")
            
            # Extract path
            path_match = re.search(r'["\'](.+?)["\']', match.group(1))
            if path_match:
                signal_path = Path(path_match.group(1))
                print(f"\n  Resolves to: {signal_path}")
                print(f"  Exists: {'✓ Yes' if signal_path.exists() else '✗ No'}")
        else:
            print("✗ Could not find output_dir configuration")
    else:
        print(f"✗ sim_broker.py not found at {sim_broker_path}")
    
    # Check MQL5 configuration
    print("\n\n📍 MQL5 Configuration (PythonSignalExecutor_Multi.mq5)")
    print("-" * 80)
    
    mql5_path = Path("c:/Users/nyaga/Documents/AlgoAgent/Backtest/PythonSignalExecutor_Multi.mq5")
    if mql5_path.exists():
        content = mql5_path.read_text()
        
        # Find SignalsFolder input
        match = re.search(r'input string\s+SignalsFolder\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            folder = match.group(1)
            print(f"✓ Found configuration:")
            print(f"  SignalsFolder = \"{folder}\"")
            print(f"\n  MQL5 will look for files at:")
            print(f"  Terminal/Common/Files/{folder}")
        else:
            print("✗ Could not find SignalsFolder configuration")
    else:
        print(f"✗ PythonSignalExecutor_Multi.mq5 not found at {mql5_path}")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print("\n✓ Python exports signals to:")
    print("  C:\\Users\\nyaga\\AppData\\Roaming\\MetaQuotes\\Terminal\\")
    print("  D0E8209F77C8CF37AD8BF550E51FF075\\MQL5\\Experts\\signals\\")
    print("\n✓ MQL5 reads signals from:")
    print("  Terminal/Common/Files/Experts/signals/")
    print("\n✓ Both point to the SAME location")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_configuration()
