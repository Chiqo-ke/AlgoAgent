#!/usr/bin/env python3
"""
AlgoAgent Data Management Script
================================

Utility script to view and manage saved CSV files in the data directory.

Usage:
    python data_manager.py [command]
    
Commands:
    list    - List all saved CSV files
    info    - Show detailed information about files
    clean   - Clean up old files (interactive)
    view    - Preview a specific file
"""

import os
import sys
import pandas as pd
from datetime import datetime
import glob

def list_csv_files():
    """List all CSV files in the data directory"""
    data_dir = os.path.join("Data", "data")
    
    if not os.path.exists(data_dir):
        print("❌ Data directory not found")
        return []
    
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    if not csv_files:
        print("📁 No CSV files found in data directory")
        return []
    
    print(f"\n📊 Found {len(csv_files)} CSV file(s) in {data_dir}:")
    print("-" * 60)
    
    files_info = []
    for file_path in sorted(csv_files):
        filename = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        modified = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        size_str = f"{size:,} bytes" if size < 1024*1024 else f"{size/(1024*1024):.1f} MB"
        
        print(f"📄 {filename}")
        print(f"   Size: {size_str}")
        print(f"   Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        files_info.append({
            'filename': filename,
            'path': file_path,
            'size': size,
            'modified': modified
        })
    
    return files_info

def show_file_info():
    """Show detailed information about CSV files"""
    files = list_csv_files()
    
    if not files:
        return
    
    print("📋 Detailed File Information:")
    print("=" * 60)
    
    total_size = 0
    for file_info in files:
        try:
            df = pd.read_csv(file_info['path'], index_col=0, parse_dates=True)
            
            print(f"\n📊 {file_info['filename']}")
            print(f"   Rows: {df.shape[0]:,}")
            print(f"   Columns: {df.shape[1]}")
            print(f"   Date Range: {df.index[0].date()} to {df.index[-1].date()}")
            print(f"   Columns: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
            print(f"   File Size: {file_info['size']:,} bytes")
            
            total_size += file_info['size']
            
        except Exception as e:
            print(f"❌ Error reading {file_info['filename']}: {e}")
    
    print(f"\n📁 Total Storage Used: {total_size:,} bytes ({total_size/(1024*1024):.1f} MB)")

def preview_file():
    """Preview a specific file"""
    files = list_csv_files()
    
    if not files:
        return
    
    print("\nSelect a file to preview:")
    for i, file_info in enumerate(files, 1):
        print(f"{i}. {file_info['filename']}")
    
    try:
        choice = int(input("\nEnter file number: ")) - 1
        if 0 <= choice < len(files):
            file_path = files[choice]['path']
            filename = files[choice]['filename']
            
            print(f"\n📊 Previewing: {filename}")
            print("=" * 60)
            
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            
            print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            print(f"Date Range: {df.index[0]} to {df.index[-1]}")
            print(f"\nFirst 5 rows:")
            print(df.head())
            
            print(f"\nLast 5 rows:")
            print(df.tail())
            
            print(f"\nBasic Statistics:")
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            if len(numeric_cols) > 0:
                print(df[numeric_cols].describe().round(2))
            
        else:
            print("❌ Invalid selection")
            
    except (ValueError, IndexError):
        print("❌ Invalid input")
    except Exception as e:
        print(f"❌ Error reading file: {e}")

def clean_files():
    """Interactive file cleanup"""
    files = list_csv_files()
    
    if not files:
        return
    
    print("\n🧹 File Cleanup Options:")
    print("1. Delete files older than 7 days")
    print("2. Delete files larger than 10MB")
    print("3. Keep only latest 5 files")
    print("4. Manual selection")
    print("5. Cancel")
    
    try:
        choice = int(input("\nSelect cleanup option: "))
        
        if choice == 1:
            # Delete old files
            cutoff = datetime.now().timestamp() - (7 * 24 * 60 * 60)
            to_delete = [f for f in files if f['modified'].timestamp() < cutoff]
            
        elif choice == 2:
            # Delete large files
            to_delete = [f for f in files if f['size'] > 10 * 1024 * 1024]
            
        elif choice == 3:
            # Keep only latest 5
            sorted_files = sorted(files, key=lambda x: x['modified'], reverse=True)
            to_delete = sorted_files[5:]
            
        elif choice == 4:
            # Manual selection
            print("\nSelect files to delete (comma-separated numbers):")
            for i, file_info in enumerate(files, 1):
                print(f"{i}. {file_info['filename']} ({file_info['size']:,} bytes)")
            
            selections = input("\nFiles to delete: ").strip()
            if selections:
                indices = [int(x.strip()) - 1 for x in selections.split(',')]
                to_delete = [files[i] for i in indices if 0 <= i < len(files)]
            else:
                to_delete = []
        
        elif choice == 5:
            print("Cleanup cancelled")
            return
        
        else:
            print("❌ Invalid option")
            return
        
        if to_delete:
            print(f"\n⚠️  Files to be deleted:")
            for file_info in to_delete:
                print(f"   - {file_info['filename']}")
            
            confirm = input(f"\nDelete {len(to_delete)} file(s)? (y/N): ").strip().lower()
            if confirm == 'y':
                for file_info in to_delete:
                    os.remove(file_info['path'])
                    print(f"🗑️  Deleted: {file_info['filename']}")
                print(f"✅ Cleanup complete! Deleted {len(to_delete)} file(s)")
            else:
                print("Cleanup cancelled")
        else:
            print("✅ No files match cleanup criteria")
            
    except (ValueError, IndexError) as e:
        print(f"❌ Invalid input: {e}")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        command = "list"
    
    print("🗂️  AlgoAgent Data Management")
    print("=" * 40)
    
    if command == "list":
        list_csv_files()
    elif command == "info":
        show_file_info()
    elif command == "view":
        preview_file()
    elif command == "clean":
        clean_files()
    else:
        print(f"❌ Unknown command: {command}")
        print("\nAvailable commands: list, info, view, clean")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())