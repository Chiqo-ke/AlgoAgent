# Strategy Code Generation Implementation

**Date:** October 31, 2025  
**Status:** ✅ Implemented

## Overview

This document describes the implementation of automatic executable Python strategy code generation from canonical JSON schemas in the AlgoAgent platform. The feature bridges the gap between AI-validated strategy definitions and executable backtesting code.

---

## Architecture Flow

```
┌─────────────────────┐
│  User Describes     │
│  Strategy in Chat   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  AI Validates &     │
│  Creates Canonical  │
│  JSON Schema        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  User Reviews &     │
│  Names Strategy     │
│  (Confirmation)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Backend Generates  │
│  Executable Python  │
│  Strategy Code      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Code Saved to      │
│  Backtest/codes/    │
│  Ready to Run       │
└─────────────────────┘
```

---

## Components Implemented

### 1. Backend API Endpoint

**File:** `AlgoAgent/strategy_api/views.py`  
**Endpoint:** `/api/strategies/api/generate_executable_code/`  
**Method:** POST

#### Request Format

```json
{
  "canonical_json": {
    "strategy_name": "RSI Mean Reversion",
    "description": "...",
    "entry_rules": [...],
    "exit_rules": [...],
    "risk_management": {...},
    "indicators": [...],
    "timeframe": "1d"
  },
  "strategy_name": "RSI Mean Reversion",
  "strategy_id": 123  // Optional
}
```

#### Response Format

```json
{
  "success": true,
  "strategy_code": "# Generated Python code...",
  "file_path": "/path/to/Backtest/codes/rsi_mean_reversion.py",
  "file_name": "rsi_mean_reversion.py",
  "json_file_path": "/path/to/Backtest/codes/rsi_mean_reversion.json",
  "strategy_id": 123,
  "message": "Executable strategy code generated successfully"
}
```

#### Features

- ✅ Parses canonical JSON (handles both string and object formats)
- ✅ Builds comprehensive strategy description from canonical schema
- ✅ Generates symbol-agnostic Python code using GeminiStrategyGenerator
- ✅ Saves Python code to `Backtest/codes/` directory
- ✅ Saves canonical JSON for reference
- ✅ Updates strategy record with generated code path
- ✅ Creates safe filenames with collision handling

#### Code Generation Process

1. **Parse Canonical JSON**: Extract strategy components
2. **Build Description**: 
   - Entry rules
   - Exit rules
   - Risk management (stop loss, take profit, position sizing)
   - Indicators used
   - Timeframe
3. **Add Instructions**: Symbol-agnostic guidelines for AI
4. **Generate Code**: Use Gemini AI to create executable Python
5. **Save Files**: 
   - `.py` file with executable code
   - `.json` file with canonical schema
6. **Update Database**: Link file path to strategy record

---

### 2. Frontend Integration

**File:** `Algo/src/pages/Dashboard.tsx`  
**Function:** `handleConfirmAndProceed()`

#### Implementation Details

The confirmation dialog now triggers code generation in two scenarios:

##### Scenario A: Existing Strategy (Edit Mode)

```typescript
// 1. Update strategy name if changed
// 2. Call generate_executable_code endpoint
// 3. Navigate to backtest page with code info
navigate('/backtest', { 
  state: { 
    strategyId: confirmationData.strategyId,
    strategyName: editedStrategyName.trim(),
    codeFilePath: codeGenData.file_path,
    codeFileName: codeGenData.file_name
  } 
});
```

##### Scenario B: New Strategy Creation

```typescript
// 1. Create strategy record
// 2. Call generate_executable_code endpoint
// 3. Navigate to backtest page with code info
navigate('/backtest', { 
  state: { 
    strategyId: data.id,
    strategyName: editedStrategyName.trim(),
    codeFilePath: codeGenData.file_path,
    codeFileName: codeGenData.file_name,
    fromNewStrategy: true
  } 
});
```

#### Error Handling

- Graceful degradation: If code generation fails, proceeds without blocking
- User notifications via toast messages
- Console logging for debugging
- Falls back to normal workflow on errors

---

### 3. File System Integration

#### Directory Structure

```
AlgoAgent/
└── Backtest/
    └── codes/
        ├── rsi_mean_reversion.py       # Generated Python code
        ├── rsi_mean_reversion.json     # Canonical JSON reference
        ├── momentum_scalper.py
        ├── momentum_scalper.json
        └── ...
```

#### File Naming Convention

1. Extract alphanumeric characters from strategy name
2. Convert to lowercase
3. Join with underscores (max 8 words)
4. Add `.py` or `.json` extension
5. Handle collisions with numeric suffixes

**Examples:**
- "RSI Mean Reversion Pro" → `rsi_mean_reversion_pro.py`
- "Simple Strategy" → `simple_strategy.py`
- "Strategy #2" → `strategy_2.py`

---

## Integration with Interactive Backtest Runner

The implementation follows the pattern established in `interactive_backtest_runner.py`:

### Similar Workflow

1. ✅ **Strategy Validation**: Both use AI validation
2. ✅ **Canonical JSON Generation**: Common format
3. ✅ **Code Generation**: Use `GeminiStrategyGenerator`
4. ✅ **File Storage**: Save to `Backtest/codes/`
5. ✅ **Symbol-Agnostic**: Works with any trading symbol

### Key Differences

| Interactive Runner | Web Dashboard |
|-------------------|---------------|
| Command-line interface | Web UI with dialog |
| Manual step-by-step | Automatic on confirmation |
| Immediate execution | Saves for later execution |
| User enters text in terminal | User chats with AI |

---

## Symbol-Agnostic Design

Both implementations ensure strategies work with ANY symbol:

### Instructions Added to AI Prompt

```
IMPORTANT INSTRUCTIONS FOR CODE GENERATION:
- Strategy should work with ANY symbol (do not hardcode symbols)
- Symbol will be provided dynamically through market_data parameter
- Use market_data dictionary to access OHLCV data for any symbol
- Constructor should only accept broker and trading parameters (no symbol parameter)
```

### Generated Code Pattern

```python
class MyStrategy:
    def __init__(self, broker: SimBroker, **kwargs):
        """Initialize strategy - NO SYMBOL PARAMETER"""
        self.broker = broker
        # ... other parameters
    
    def on_bar(self, timestamp: datetime, market_data: dict):
        """
        market_data = {
            'AAPL': {'open': 150.0, 'high': 151.0, ...},
            'MSFT': {'open': 300.0, 'high': 302.0, ...}
        }
        """
        # Strategy logic works with any symbol in market_data
        for symbol, data in market_data.items():
            # Process each symbol
            pass
```

---

## Database Schema Integration

### Strategy Model Updates

The `Strategy` model's `parameters` field is updated to include:

```json
{
  "generated_code_path": "/full/path/to/strategy.py",
  "generated_code_filename": "strategy.py",
  ... // other parameters
}
```

This allows:
- Tracking which strategies have generated code
- Quick lookup of code files
- Version management (if needed later)

---

## API Endpoints Summary

### Existing Endpoints Used

1. **Create Strategy**: `/api/strategies/api/create_strategy/`
   - Creates strategy record with canonical JSON

2. **Update Strategy**: `/api/strategies/api/strategies/{id}/`
   - Updates strategy name and other fields

3. **Validate Strategy**: `/api/strategies/api/validate_strategy_with_ai/`
   - AI validation and canonical JSON creation

### New Endpoint Added

4. **Generate Executable Code**: `/api/strategies/api/generate_executable_code/`
   - Converts canonical JSON to executable Python code
   - Saves to file system
   - Links to strategy record

---

## Testing Workflow

### End-to-End Test Scenario

1. **Start Chat Session**
   ```
   User: "Create a strategy that buys when RSI is below 30 
          and sells when RSI is above 70"
   ```

2. **AI Validates & Creates Canonical JSON**
   - Backend processes with Gemini AI
   - Returns canonical JSON structure
   - Shows formatted response to user

3. **User Confirms Strategy**
   - Opens confirmation dialog
   - Reviews canonical schema in human-readable format
   - Enters strategy name: "RSI Mean Reversion"
   - Clicks "Confirm & Proceed to Backtest"

4. **Automatic Code Generation**
   - Frontend calls `generate_executable_code` endpoint
   - Backend generates Python code
   - Saves to `Backtest/codes/rsi_mean_reversion.py`
   - Saves canonical JSON to `rsi_mean_reversion.json`

5. **Navigate to Backtest**
   - Redirects to backtest page
   - Strategy ID and code file info passed
   - Ready to run backtest with any symbol

### Expected Files Created

```
Backtest/codes/
├── rsi_mean_reversion.py      # 200-300 lines of Python code
└── rsi_mean_reversion.json    # Canonical JSON schema
```

### Expected Database Updates

```sql
-- Strategy record
UPDATE strategy 
SET parameters = jsonb_set(
  parameters, 
  '{generated_code_path}', 
  '"/full/path/Backtest/codes/rsi_mean_reversion.py"'
)
WHERE id = 123;
```

---

## Error Handling & Edge Cases

### 1. Code Generation Failure

**Scenario**: Gemini API fails or generates invalid code  
**Handling**: 
- Log error to console
- Show warning toast
- Continue to backtest page without code file
- User can manually create strategy later

### 2. File System Issues

**Scenario**: Unable to write to `Backtest/codes/`  
**Handling**:
- Return 500 error with details
- Toast shows "Failed to generate executable code"
- Strategy still saved (canonical JSON in database)

### 3. Invalid Canonical JSON

**Scenario**: Malformed JSON structure  
**Handling**:
- Return 400 error with JSON parsing details
- User sees descriptive error message
- Can retry with corrected data

### 4. File Name Collisions

**Scenario**: Strategy name already exists  
**Handling**:
- Automatically append numeric suffix (`_1`, `_2`, etc.)
- No overwriting of existing files
- Each strategy gets unique filename

### 5. Missing Strategy Components

**Scenario**: Canonical JSON lacks entry/exit rules  
**Handling**:
- Generator creates best-effort description
- Includes all available components
- Adds comments in generated code about missing logic

---

## Future Enhancements

### Potential Improvements

1. **Code Versioning**
   - Track multiple versions of generated code
   - Compare changes between versions
   - Rollback to previous versions

2. **Code Preview**
   - Show generated code in UI before saving
   - Allow manual edits before confirmation
   - Syntax highlighting

3. **Direct Execution**
   - Run backtest immediately after generation
   - Stream results in real-time
   - No manual navigation needed

4. **Code Validation**
   - Lint generated Python code
   - Run unit tests automatically
   - Flag potential issues

5. **Template Customization**
   - Allow users to provide code templates
   - Support multiple strategy frameworks
   - Custom indicator libraries

6. **Multi-File Strategies**
   - Generate helper modules
   - Create indicator libraries
   - Support complex strategy structures

---

## Dependencies

### Backend

- `google.generativeai`: Gemini AI API for code generation
- `GeminiStrategyGenerator`: Strategy code generator class
- Django REST Framework: API endpoints
- PostgreSQL: Strategy storage

### Frontend

- React Router: Navigation between pages
- Fetch API: HTTP requests to backend
- Toast notifications: User feedback

### File System

- Write permissions to `Backtest/codes/` directory
- Sufficient disk space for generated files

---

## Configuration

### Environment Variables

```bash
# .env file
GEMINI_API_KEY=your_gemini_api_key_here
```

### Django Settings

```python
# settings.py
BACKTEST_CODES_DIR = BASE_DIR / "Backtest" / "codes"
```

---

## Troubleshooting

### Common Issues

#### Issue: "Strategy generator not available"

**Cause**: `GeminiStrategyGenerator` import failed  
**Solution**: 
1. Check `GEMINI_API_KEY` is set
2. Verify `google-generativeai` is installed
3. Ensure `Backtest/gemini_strategy_generator.py` exists

#### Issue: "Failed to save generated code"

**Cause**: File system permissions  
**Solution**:
1. Check write permissions on `Backtest/codes/`
2. Create directory if missing: `mkdir -p Backtest/codes`
3. Verify disk space available

#### Issue: "Generated code doesn't run"

**Cause**: Invalid Python syntax or missing imports  
**Solution**:
1. Check console logs for AI generation errors
2. Manually review generated `.py` file
3. Report to AI model (Gemini) for improvement
4. Use interactive runner as reference

---

## Conclusion

The strategy code generation feature successfully bridges the gap between AI-validated strategies and executable backtesting code. By following the established patterns in `interactive_backtest_runner.py`, the implementation ensures consistency across the platform.

### Key Benefits

✅ **Seamless Workflow**: From chat to backtest in a few clicks  
✅ **Symbol-Agnostic**: Strategies work with any trading symbol  
✅ **Fully Automated**: No manual code writing required  
✅ **Production-Ready**: Executable code saved and ready to run  
✅ **Error-Tolerant**: Graceful handling of failures  
✅ **Auditable**: Canonical JSON saved alongside code  

### Next Steps

1. Test the complete workflow with various strategy types
2. Monitor Gemini API usage and costs
3. Gather user feedback on generated code quality
4. Implement suggested enhancements
5. Create unit tests for code generation endpoint

---

**Document Version:** 1.0  
**Last Updated:** October 31, 2025  
**Author:** AlgoAgent Development Team
