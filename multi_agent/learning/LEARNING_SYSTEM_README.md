# SQL-Backed Learning System

## Overview

The AI agent now includes a **persistent learning system** that records every iteration, error, and successful fix in a SQL database. This enables the agent to:

1. ✅ **Learn from mistakes** - Never repeat the same error twice
2. 🔍 **Search similar errors** - Find fixes from past iterations
3. 📊 **Track progress** - View analytics on error patterns and success rates
4. 💾 **Persist knowledge** - Learning survives across sessions
5. 🎯 **Improve confidence** - Better error classification over time

## Key Features

### 1. Advanced Error Classification

Instead of returning `'unknown_error'`, the system now uses **regex-based pattern matching** to classify errors into specific categories:

- `syntax_error` - Python syntax issues
- `import_error` - Missing or incorrect imports
- `attribute_error` - Object attribute access issues
- `type_error` - Type mismatches
- `name_error` - Undefined variables
- `key_error` - Dictionary key errors
- `index_error` - List/array index errors
- `value_error` - Invalid values
- `file_error` - File not found or IO errors
- `timeout_error` - Execution timeouts
- `assertion_error` - Test assertion failures
- `connection_error` - Network/connection issues
- And 10+ more specific categories

### 2. Iteration Logging

Every iteration is logged with full details:

```python
{
  "workflow_id": "rsi_strategy",
  "iteration_number": 3,
  "error_type": "attribute_error",
  "error_message": "DataFrame object has no attribute 'RSI'",
  "fix_attempted": "Add RSI indicator calculation",
  "success": true,
  "duration": 12.5,
  "error_details": {...},
  "fix_details": {...}
}
```

### 3. Knowledge Base

Successful fixes are stored with:

- **Error signature** - Normalized hash for matching
- **Fix description** - What was done to fix it
- **Code snippet** - Actual code that worked
- **Success count** - How many times this fix worked
- **Confidence score** - Success rate (0.0 to 1.0)
- **Tags** - For categorization
- **Average fix time** - Performance tracking

### 4. Similar Error Search

Before creating a fix task, the system searches for similar errors:

```python
similar_fixes = kb.search_similar_errors(
    error_message="DataFrame has no attribute 'RSI'",
    error_type="attribute_error",
    limit=3,
    min_confidence=0.5
)
```

If found, suggestions are included in the fix task description:

```
💡 Knowledge Base Suggestions:

1. attribute_error (used 5 times, 80% success rate):
   - Add missing indicator calculation before usage
   - Code example: data['RSI'] = talib.RSI(data['Close'], timeperiod=14)
```

## Database Schema

### Tables

1. **error_patterns** - Stores learned error-fix mappings
   - `error_signature` (unique hash)
   - `error_type`, `error_message`, `normalized_error`
   - `fix_description`, `fix_code_snippet`
   - `success_count`, `failure_count`, `confidence_score`
   - `workflow_ids`, `tags`
   - `first_seen`, `last_used`, `avg_fix_time`

2. **iteration_logs** - Complete iteration history
   - `workflow_id`, `iteration_number`, `timestamp`
   - `error_type`, `error_signature`
   - `fix_attempted`, `success`, `duration`
   - `error_details` (JSON), `fix_details` (JSON)

3. **error_type_stats** - Quick analytics
   - `error_type`, `total_occurrences`, `total_fixes`
   - `avg_iterations_to_fix`, `last_occurrence`

## Usage

### View Analytics

```bash
# View analytics in terminal
python view_learning_analytics.py

# Export analytics to JSON
python view_learning_analytics.py --export analytics.json

# Export full knowledge base
python view_learning_analytics.py --export-knowledge knowledge_export.json
```

### Sample Output

```
===========================================================================
 🧠 LEARNING SYSTEM ANALYTICS
===========================================================================

📊 Overall Statistics:
   Total Error Patterns Learned: 23
   Total Iterations Logged: 47
   Total Successful Fixes: 35
   Overall Success Rate: 74.47%

🔍 Error Type Breakdown:
   Error Type                Occurrences     Fixes        Fix Rate  
   ------------------------- --------------- ------------ ----------
   attribute_error           15              12            80.0%
   type_error                8               6             75.0%
   import_error              5               5            100.0%
   name_error                4               3             75.0%

💡 Top Fixes by Confidence:
   Error Type           Signature          Success    Confidence  
   -------------------- ------------------ ---------- ------------
   import_error         a3b2c1d4e5f6       5           100.0%
   attribute_error      f6e5d4c3b2a1       12           92.3%
   type_error           1a2b3c4d5e6f       6            85.7%
```

### Integration with CLI

The learning system is **automatically enabled** when running the iterative loop:

```bash
python cli.py --workflow rsi_strategy --mode iterative --max-iterations 5
```

You'll see messages like:

```
[IterativeLoop] ✅ SQL Learning System enabled
...
   📝 macd_strategy
      Type: attribute_error
      Error: 'DataFrame' object has no attribute 'MACD'
      🔍 Found 2 similar error(s) in knowledge base
         1. attribute_error (confidence: 85%)
         2. name_error (confidence: 70%)
...
   🧠 Learning from successful fixes...
      ✅ Recorded fix for attribute_error in macd_strategy
   💾 Recorded 1 successful fix(es) to database
```

## How It Works

### 1. Error Occurs

When a test fails, the error is:
1. Classified using advanced regex patterns
2. Normalized (remove file paths, line numbers, etc.)
3. Hashed to create a unique signature
4. Logged to `iteration_logs` table

### 2. Similar Errors Searched

Before creating a fix task:
1. Search `error_patterns` for same signature (exact match)
2. If not found, search by error type + confidence score
3. Return top 3-5 similar fixes

### 3. Fix Task Enhanced

The fix task description includes:
- Standard fix instructions
- **💡 Knowledge Base Suggestions** section with:
  - Error type and success rate
  - Fix description from past successes
  - Code snippets that worked before

### 4. Success Recorded

When tests pass after fixing:
1. Extract what changed (from workflow tasks)
2. Record to `error_patterns` table
3. Update success count and confidence score
4. Log successful iteration to `iteration_logs`

### 5. Confidence Score Updates

```python
confidence = success_count / (success_count + failure_count)
```

- Starts at 0.8 for first success
- Increases with more successes
- Decreases when fix doesn't work

## Error Normalization

Errors are normalized for better matching:

**Original:**
```
AttributeError: 'DataFrame' object has no attribute 'RSI' at line 45 in C:\Users\...\strategy.py
```

**Normalized:**
```
AttributeError: '<OBJ>' object has no attribute 'RSI' at line <N> in <FILE>
```

This allows matching similar errors across different:
- File paths
- Line numbers
- Variable names
- Timestamps

## Database Location

Default: `AlgoAgent/multi_agent/learning/knowledge.db`

You can specify a different path:

```python
from learning.sql_knowledge_base import SQLKnowledgeBase

kb = SQLKnowledgeBase(db_path=Path("custom/path/knowledge.db"))
```

## Migration from JSON Knowledge Base

The old JSON-based `knowledge.json` is **not automatically migrated**. The new system starts fresh but learns quickly.

If you want to preserve old learnings:
1. Both systems can coexist
2. Old system: `learning/knowledge.json`
3. New system: `learning/knowledge.db`

## Performance

- **SQLite** with indexes for fast queries
- **Context manager** for proper connection handling
- **Batch operations** when possible
- **Analytics caching** for frequently accessed stats

## Privacy & Security

- All data stored **locally** in SQLite
- No external API calls for learning
- Knowledge base is **portable** - copy `.db` file to share

## Troubleshooting

### "SQL Learning System disabled"

Check:
1. SQLite is installed (included with Python)
2. `learning/sql_knowledge_base.py` exists
3. Write permissions for `learning/` directory

### Database locked error

- SQLite doesn't support concurrent writes well
- Each operation uses `with` context manager to release locks
- If persistent, restart the agent

### No similar errors found

- Database is empty (new system)
- Error is genuinely unique
- Try lowering `min_confidence` parameter

## Future Enhancements

- [ ] Export/import knowledge between agents
- [ ] Web UI for analytics dashboard
- [ ] Automatic fix suggestion ranking
- [ ] Integration with LLM for semantic error matching
- [ ] Multi-agent knowledge sharing
- [ ] Performance regression detection

## Example Workflow

1. **First run** - Agent fails with `AttributeError`
   ```
   Error: 'DataFrame' object has no attribute 'RSI'
   → No similar errors found (new database)
   → Creates standard fix task
   → Fixes error, tests pass
   → Records fix to database
   ```

2. **Second run** - Similar error occurs
   ```
   Error: 'DataFrame' object has no attribute 'MACD'
   → Found 1 similar error (attribute_error, 100% confidence)
   → Includes suggestion in fix task description
   → Agent applies learned fix pattern
   → Faster resolution!
   ```

3. **View progress**
   ```bash
   python view_learning_analytics.py
   → Shows 2 patterns learned
   → 100% success rate on attribute_error
   → Average fix time: 8.5 seconds
   ```

## Contributing

To improve the learning system:

1. Add new error patterns to `classify_error_advanced()`
2. Enhance normalization in `normalize_error()`
3. Add new analytics queries in `get_analytics()`
4. Improve fix extraction in `_extract_fix_description()`

## License

Same as parent project.

---

**Questions?** Check the code documentation in `learning/sql_knowledge_base.py`
