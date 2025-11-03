"""
CLI Tool for Switching Data Processing Modes
=============================================

This script allows easy switching between STREAMING and BATCH modes
for strategy code generation.

Usage:
    python set_mode.py streaming  # Enable sequential processing
    python set_mode.py batch      # Enable bulk processing
    python set_mode.py info       # Show current mode information

Version: 1.0.0
Created: 2025-11-03
"""

import sys
from pathlib import Path


def read_config_file(config_path: Path) -> list:
    """Read the sequential_config.py file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return f.readlines()


def write_config_file(config_path: Path, lines: list):
    """Write updated lines to sequential_config.py"""
    with open(config_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def set_mode(mode: str):
    """
    Update the default mode in sequential_config.py
    
    Args:
        mode: "streaming" or "batch"
    """
    
    if mode not in ['streaming', 'batch']:
        print(f"❌ Invalid mode: {mode}")
        print("   Valid options: streaming, batch")
        return False
    
    config_path = Path(__file__).parent / "sequential_config.py"
    
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    # Read current config
    lines = read_config_file(config_path)
    
    # Update DEFAULT_MODE line
    updated_lines = []
    mode_updated = False
    
    for line in lines:
        if line.strip().startswith('DEFAULT_MODE'):
            updated_lines.append(f'DEFAULT_MODE = "{mode}"  # Options: "streaming" or "batch"\n')
            mode_updated = True
        else:
            updated_lines.append(line)
    
    if not mode_updated:
        print("❌ Could not find DEFAULT_MODE in configuration file")
        return False
    
    # Write updated config
    write_config_file(config_path, updated_lines)
    
    print("=" * 70)
    print(f"✅ Mode successfully set to: {mode.upper()}")
    print("=" * 70)
    
    if mode == "streaming":
        print("\n🔄 STREAMING MODE")
        print("   • Sequential row-by-row processing")
        print("   • Simulates real-time data feed")
        print("   • Prevents look-ahead bias")
        print("   • More realistic backtesting")
        print("   • Slightly slower performance")
    else:
        print("\n⚡ BATCH MODE")
        print("   • Bulk data processing")
        print("   • All data loaded at once")
        print("   • Allows vectorized operations")
        print("   • Faster performance")
        print("   • May allow look-ahead bias")
    
    print("\n📝 All new strategies will be generated using this mode.")
    print("=" * 70)
    
    return True


def show_info():
    """Show current mode and configuration information"""
    
    config_path = Path(__file__).parent / "sequential_config.py"
    
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return
    
    # Import the config to get current settings
    sys.path.insert(0, str(config_path.parent))
    try:
        from sequential_config import get_mode_info
        
        info = get_mode_info()
        
        print("=" * 70)
        print("SEQUENTIAL DATA PROCESSING CONFIGURATION")
        print("=" * 70)
        
        print(f"\n📊 Current Mode: {info['current_mode'].upper()}")
        print(f"   {info['current_description']}")
        
        print(f"\n✨ Use Cases for {info['current_mode'].upper()} mode:")
        for use_case in info['use_cases'][info['current_mode']]:
            print(f"   • {use_case}")
        
        print("\n🔀 Available Modes:")
        for mode in info['available_modes']:
            marker = "→" if mode == info['current_mode'] else " "
            print(f"   {marker} {mode.upper()}: {info['all_descriptions'][mode]}")
        
        print("\n💡 To change mode:")
        print("   python set_mode.py streaming")
        print("   python set_mode.py batch")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")


def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        print("=" * 70)
        print("Data Processing Mode Configuration Tool")
        print("=" * 70)
        print("\nUsage:")
        print("  python set_mode.py streaming    # Enable sequential processing")
        print("  python set_mode.py batch        # Enable bulk processing")
        print("  python set_mode.py info         # Show current configuration")
        print("\nExamples:")
        print("  python set_mode.py streaming    # For realistic backtesting")
        print("  python set_mode.py batch        # For faster prototyping")
        print("=" * 70)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "info":
        show_info()
    elif command in ["streaming", "batch"]:
        success = set_mode(command)
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Unknown command: {command}")
        print("   Valid commands: streaming, batch, info")
        sys.exit(1)


if __name__ == "__main__":
    main()
