import sqlite3
import json
from datetime import datetime

# Connect to database
conn = sqlite3.connect(r'C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent\db.sqlite3')
cursor = conn.cursor()

# Get strategy details - first check what columns exist
cursor.execute("PRAGMA table_info(strategy_api_strategy)")
columns = cursor.fetchall()
print("=== AVAILABLE COLUMNS IN strategy_api_strategy ===")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

print("\n" + "="*50 + "\n")

cursor.execute('''
    SELECT id, name, description, status
    FROM strategy_api_strategy 
    WHERE id = 115
''')

row = cursor.fetchone()
if row:
    id, name, desc, status = row
    code = None
    symbol = "N/A"
    start = "N/A"
    end = "N/A"
    
    print(f"=== STRATEGY 115 DETAILS ===")
    print(f"Name: {name}")
    print(f"Description: {desc}")
    print(f"Symbol: {symbol}")
    print(f"Period: {start} to {end}")
    print(f"Status: {status}")
    print(f"Code length: {len(code) if code else 0} chars")
    
    # Extract what indicators/patterns this strategy uses
    if desc:
        desc_lower = desc.lower()
        print(f"\n=== EXPECTED PATTERNS ===")
        if 'ema' in desc_lower or 'moving average' in desc_lower:
            print("✓ Uses EMA/Moving Average crossover")
        if 'rsi' in desc_lower:
            print("✓ Uses RSI momentum")
        if 'macd' in desc_lower:
            print("✓ Uses MACD crossover")
        if 'bollinger' in desc_lower:
            print("✓ Uses Bollinger Bands")
            
    # Check all tables in database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\n=== DATABASE TABLES ===")
    for table in tables:
        print(f"  {table[0]}")
    
    print("\n=== BACKTEST STATUS ===")
    print("Note: Checking if backtest table exists...")
    
else:
    print("Strategy 115 not found in database")

conn.close()
