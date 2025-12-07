import sqlite3

conn = sqlite3.connect('error_learning.db')
cur = conn.cursor()

print('\n' + '='*70)
print('LEARNING SYSTEM DATABASE ANALYSIS')
print('='*70)

print('\n=== LATEST ERRORS (Last 5) ===')
cur.execute('''
    SELECT id, strategy_name, error_type, fix_successful, fix_attempts, timestamp 
    FROM errors 
    ORDER BY id DESC 
    LIMIT 5
''')

for row in cur.fetchall():
    print(f'{row[0]:3d} | {row[1]:20s} | {row[2]:15s} | Success: {row[3]} | Attempts: {row[4]} | {row[5]}')

print('\n=== ERROR TYPE STATISTICS ===')
cur.execute('''
    SELECT 
        error_type, 
        COUNT(*) as total,
        SUM(CASE WHEN fix_successful=1 THEN 1 ELSE 0 END) as fixed,
        AVG(fix_attempts) as avg_attempts,
        AVG(resolution_time_seconds) as avg_time
    FROM errors 
    GROUP BY error_type
''')

for row in cur.fetchall():
    total, fixed = row[1], row[2]
    success_rate = (fixed * 100 // total) if total > 0 else 0
    print(f'{row[0]:20s}: {total:2d} total, {fixed:2d} fixed ({success_rate}%), avg {row[3]:.1f} attempts, {row[4]:.1f}s')

print('\n=== ENCODING ERROR DETAILS ===')
cur.execute('''
    SELECT id, strategy_name, fix_successful, fix_attempts, resolution_time_seconds, timestamp
    FROM errors
    WHERE error_type = 'encoding_error'
    ORDER BY id DESC
''')

for row in cur.fetchall():
    time_str = f'{row[4]:.1f}s' if row[4] is not None else 'N/A'
    print(f'ID {row[0]}: {row[1]} | Success: {row[2]} | Attempts: {row[3]} | Time: {time_str} | {row[5]}')

print('\n=== UNKNOWN ERROR DETAILS (Should be empty after fix) ===')
cur.execute('''
    SELECT id, strategy_name, fix_successful, fix_attempts, timestamp
    FROM errors
    WHERE error_type = 'unknown_error'
    ORDER BY id DESC
''')

rows = cur.fetchall()
if rows:
    for row in rows:
        print(f'ID {row[0]}: {row[1]} | Success: {row[2]} | Attempts: {row[3]} | {row[4]}')
else:
    print('No unknown errors (good!)')

conn.close()
