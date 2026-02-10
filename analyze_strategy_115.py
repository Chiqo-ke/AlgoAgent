import sqlite3

# Connect to database
conn = sqlite3.connect(r'C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent\db.sqlite3')
cursor = conn.cursor()

# Get strategy 115 details
cursor.execute('''
    SELECT id, name, description, strategy_code, status, created_at
    FROM strategy_api_strategy 
    WHERE id = 115
''')

row = cursor.fetchone()
if not row:
    print("Strategy 115 not found in database")
    conn.close()
    exit()

id, name, desc, code, status, created = row

print(f"{'='*80}")
print(f"STRATEGY 115: {name}")
print(f"{'='*80}")
print(f"Description: {desc}")
print(f"Status: {status}")
print(f"Created: {created}")
print(f"Code length: {len(code) if code else 0} characters")
print()

# Analyze what patterns this strategy should trade
if desc:
    desc_lower = desc.lower()
    print(f"{'='*80}")
    print(f"EXPECTED TRADING PATTERNS (from description):")
    print(f"{'='*80}")
    
    patterns_found = []
    if 'ema' in desc_lower or 'moving average' in desc_lower or 'ma' in desc_lower:
        patterns_found.append("✓ EMA/Moving Average crossover")
    if 'rsi' in desc_lower:
        patterns_found.append("✓ RSI momentum (oversold/overbought)")
    if 'macd' in desc_lower:
        patterns_found.append("✓ MACD crossover")
    if 'bollinger' in desc_lower:
        patterns_found.append("✓ Bollinger Bands")
    if 'stochastic' in desc_lower:
        patterns_found.append("✓ Stochastic oscillator")
        
    if patterns_found:
        for pattern in patterns_found:
            print(pattern)
    else:
        print("⚠️  No recognizable patterns in description")
    print()

# Check backtest runs
cursor.execute('''
    SELECT 
        br.id, br.run_id, br.status, br.total_trades, 
        br.total_return, br.win_rate, br.created_at, br.error_message
    FROM backtest_api_backtestrun br
    WHERE br.strategy_id = 115
    ORDER BY br.created_at DESC
    LIMIT 10
''')

backtests = cursor.fetchall()

print(f"{'='*80}")
print(f"BACKTEST HISTORY ({len(backtests)} runs found):")
print(f"{'='*80}")

if backtests:
    for bt in backtests:
        bt_id, run_id, bt_status, trades, ret, win_rate, bt_created, error = bt
        print(f"\n  Run {bt_id} ({run_id}):")
        print(f"    Status: {bt_status}")
        print(f"    Trades: {trades if trades is not None else 'N/A'}")
        print(f"    Return: {ret if ret is not None else 'N/A'}")
        print(f"    Win Rate: {win_rate if win_rate is not None else 'N/A'}")
        print(f"    Created: {bt_created}")
        if error:
            print(f"    Error: {error[:200]}...")
else:
    print("  ⚠️  NO BACKTESTS HAVE BEEN RUN YET")
    print("  This strategy has been created but never executed")
    print()

# Check if code has actual buy/sell calls
if code:
    print(f"\n{'='*80}")
    print(f"CODE ANALYSIS:")
    print(f"{'='*80}")
    
    code_lower = code.lower()
    has_buy = 'buy(' in code_lower or '.buy(' in code_lower or 'broker.buy' in code_lower or 'submit_signal' in code_lower and 'buy' in code_lower
    has_sell = 'sell(' in code_lower or '.sell(' in code_lower or 'broker.sell' in code_lower or 'submit_signal' in code_lower and 'sell' in code_lower
    has_on_bar = 'def on_bar' in code_lower
    has_class = 'class ' in code_lower
    
    print(f"  Has class definition: {'✓' if has_class else '✗'}")
    print(f"  Has on_bar method: {'✓' if has_on_bar else '✗'}")
    print(f"  Has buy() calls: {'✓' if has_buy else '✗'}")
    print(f"  Has sell() calls: {'✓' if has_sell else '✗'}")
    
    if not (has_buy or has_sell):
        print(f"\n  ⚠️  WARNING: Code does not contain buy() or sell() calls!")
        print(f"  This would explain why 0 trades were generated")
    
    # Check imports
    print(f"\n  Import Pattern Check:")
    if 'from Backtest.sim_broker import' in code:
        print(f"    ✓ Uses Backtest package imports (CORRECT)")
    elif 'from sim_broker import' in code:
        print(f"    ✗ Uses direct sim_broker imports (WRONG - will cause errors)")
    
    if 'parent.parent.parent' in code:
        print(f"    ✓ Uses 3-level path setup (CORRECT)")
    elif 'parent.parent' in code:
        print(f"    ✗ Uses 2-level path setup (WRONG - will cause import errors)")
else:
    print("\n⚠️  NO CODE FOUND - strategy_code field is empty!")

conn.close()
