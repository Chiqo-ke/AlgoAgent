# AI-Powered Strategy API Integration Guide

## Overview

The Strategy API now integrates with the AI-powered Strategy Validator Bot (`interactive_strategy_tester.py` functionality) to provide intelligent strategy analysis, canonicalization, and recommendations via REST API endpoints.

## New Endpoints

### 1. Validate Strategy with AI
**Endpoint:** `POST /api/strategies/api/validate_strategy_with_ai/`

Validates and analyzes a strategy using AI without creating a database record.

**Request Body:**
```json
{
  "strategy_text": "1. Buy when RSI < 30\n2. Sell when RSI > 70...",
  "input_type": "auto",  // auto, numbered, freetext, url
  "use_gemini": true,    // Enable AI analysis
  "strict_mode": false   // Strict security validation
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "canonicalized_steps": [
    "Step 1: Entry - Buy when RSI < 30",
    "Step 2: Exit - Sell when RSI > 70"
  ],
  "classification": "Strategy Type: mean-reversion | Risk: medium",
  "classification_detail": {
    "type": "mean-reversion",
    "risk_tier": "medium",
    "primary_instruments": []
  },
  "recommendations": "1. Add stop-loss rule\n2. Define position sizing...",
  "recommendations_list": [
    {
      "title": "Add stop-loss rule",
      "priority": "high",
      "rationale": "Protect capital from large losses"
    }
  ],
  "confidence": "medium",
  "next_actions": [
    "Define position sizing",
    "Add risk management rules"
  ],
  "warnings": [],
  "canonical_json": "{...}",  // Compact canonical JSON
  "canonical_json_formatted": "{...}",  // Pretty-printed JSON
  "metadata": {...},
  "provenance": {...}
}
```

### 2. Create Strategy with AI
**Endpoint:** `POST /api/strategies/api/create_strategy_with_ai/`

Creates a new strategy with AI validation, auto-generates template, and optionally saves to Backtest/codes/.

**Request Body:**
```json
{
  "strategy_text": "RSI Mean Reversion: Buy when RSI < 30...",
  "input_type": "freetext",
  "name": "RSI Mean Reversion",  // Optional, auto-generated if omitted
  "description": "Simple RSI strategy",
  "template_id": null,  // Optional, auto-creates if omitted
  "tags": ["rsi", "mean-reversion"],
  "use_gemini": true,
  "strict_mode": false,
  "save_to_backtest": true  // Save canonical JSON to Backtest/codes/
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "strategy": {
    "id": 1,
    "name": "RSI Mean Reversion",
    "description": "Simple RSI strategy",
    "strategy_code": "{canonical JSON}",
    "risk_level": "medium",
    "timeframe": "1h",
    "tags": ["rsi", "mean-reversion"],
    "created_at": "2025-10-28T15:00:00Z"
  },
  "ai_validation": {
    "status": "success",
    "confidence": "high",
    "recommendations": [...],
    "warnings": []
  },
  "auto_created_template": {
    "id": 1,
    "name": "Template: RSI Mean Reversion",
    "message": "Template automatically created for tracking strategy evolution"
  },
  "saved_to_file": {
    "path": "C:/Users/.../AlgoAgent/Backtest/codes/rsi_mean_reversion.json",
    "message": "Canonical JSON saved to Backtest/codes/"
  }
}
```

### 3. Update Strategy with AI
**Endpoint:** `PUT /api/strategies/api/{strategy_id}/update_strategy_with_ai/`

Updates an existing strategy with AI re-validation and updates template chat history.

**Request Body:**
```json
{
  "strategy_text": "Enhanced RSI: Buy when RSI < 30 AND price > 200 SMA...",
  "input_type": "numbered",
  "use_gemini": true,
  "strict_mode": false,
  "update_description": "Added 200 SMA filter and tightened risk"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Strategy updated successfully",
  "strategy": {
    "id": 1,
    "name": "RSI Mean Reversion",
    "strategy_code": "{updated canonical JSON}",
    "updated_at": "2025-10-28T15:30:00Z"
  },
  "ai_validation": {
    "status": "success",
    "confidence": "high",
    "recommendations": [...],
    "warnings": []
  }
}
```

## Input Types

### `auto` (Default)
Automatically detects the format of the strategy text.

### `numbered`
Expects numbered steps:
```
1. Entry: Buy when RSI < 30
2. Exit: Sell when RSI > 70
3. Stop: 2% below entry
```

### `freetext`
Plain text description:
```
Buy when RSI drops below 30 indicating oversold conditions. 
Sell when it rises above 70. Use a 2% stop loss.
```

### `url`
URL to strategy content (YouTube, blog posts, etc.):
```
https://youtube.com/watch?v=strategy_video
```

## AI Features

### Canonicalization
Converts unstructured strategy text into a standardized canonical JSON schema:
- Extracts entry/exit rules
- Identifies indicators and parameters
- Structures conditions and triggers
- Adds metadata and provenance

### Classification
Automatically classifies strategies:
- **Type**: trend-following, mean-reversion, scalping, swing, etc.
- **Risk Tier**: low, medium, high based on risk management rules
- **Instruments**: Extracted primary trading instruments

### Recommendations
AI-powered prioritized recommendations:
- Missing elements (stops, sizing, etc.)
- Risk management improvements
- Parameter optimization suggestions
- Test configuration recommendations

### Security Guardrails
Built-in safety checks:
- Credential request detection
- Live trading approval requirements
- Pump-and-dump scheme detection
- Excessive risk warnings

## Integration with Interactive Tester

The API endpoints use the same core logic as `interactive_strategy_tester.py`:

| Interactive Tester Function | API Endpoint |
|------------------------------|--------------|
| `bot.process_input()` | `validate_strategy_with_ai` |
| Enter + Validate + Save | `create_strategy_with_ai` |
| Modify + Re-validate | `update_strategy_with_ai` |
| AI recommendations | Included in all responses |
| Save to Backtest/codes/ | `save_to_backtest: true` |

## Usage Examples

### Example 1: Quick Validation
```bash
curl -X POST http://localhost:8000/api/strategies/api/validate_strategy_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_text": "Buy when 50 EMA crosses above 200 EMA. Stop at 2%. Target 5%.",
    "input_type": "auto",
    "use_gemini": true
  }'
```

### Example 2: Create Complete Strategy
```bash
curl -X POST http://localhost:8000/api/strategies/api/create_strategy_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_text": "1. Buy: RSI < 30\n2. Sell: RSI > 70\n3. Stop: 3%\n4. Size: 2% risk",
    "input_type": "numbered",
    "name": "RSI Strategy",
    "tags": ["rsi", "momentum"],
    "save_to_backtest": true
  }'
```

### Example 3: Update Strategy
```bash
curl -X PUT http://localhost:8000/api/strategies/api/1/update_strategy_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_text": "Enhanced: Buy RSI<30 AND above 200 SMA...",
    "update_description": "Added SMA filter"
  }'
```

## Response Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success (validation/update) |
| 201 | Created (new strategy) |
| 400 | Bad Request (validation failed, missing fields) |
| 404 | Not Found (strategy ID doesn't exist) |
| 500 | Internal Server Error |
| 503 | Service Unavailable (validator not available) |

## Error Handling

### Validation Failure
```json
{
  "error": "Strategy validation failed",
  "validation_result": {
    "status": "error",
    "message": "Strategy contains security violations",
    "issues": [
      "Excessive risk detected",
      "Missing stop-loss rules"
    ]
  }
}
```

### Security Violation
```json
{
  "status": "approval_required",
  "message": "Live trading requires manual approval. Contact administrator."
}
```

## Template Auto-Creation

When creating a strategy without a `template_id`, the API automatically:
1. Creates a new StrategyTemplate
2. Links it to the strategy
3. Initializes chat history with AI validation results
4. Tracks strategy evolution over time

Template naming:
- Base: `"Template: {strategy_name}"`
- If exists: `"Template: {strategy_name} (1)"`

## Saving to Backtest/codes/

When `save_to_backtest: true`:
1. Generates AI-recommended filename (max 8 words)
2. Saves canonical JSON to `Backtest/codes/`
3. Auto-increments if file exists
4. Returns file path in response

Example filenames:
- `rsi_mean_reversion_scalping.json`
- `ema_crossover_trend_following.json`
- `bollinger_breakout_momentum.json`

## Chat History Tracking

Templates track strategy evolution:
```json
{
  "chat_history": [
    {
      "timestamp": "2025-10-28T15:00:00Z",
      "message": "Strategy created with AI validation. Confidence: high",
      "user": "api_user",
      "confidence": "high",
      "warnings": []
    },
    {
      "timestamp": "2025-10-28T15:30:00Z",
      "message": "Added 200 SMA filter and tightened risk",
      "user": "api_user",
      "confidence": "high",
      "warnings": []
    }
  ]
}
```

## Postman Collection

Import `Strategy_AI_Validation_Collection.json` for ready-to-use examples:
1. Open Postman
2. Import → File → Select `Strategy_AI_Validation_Collection.json`
3. Set environment variable `base_url` (default: `http://localhost:8000`)
4. Run requests

## Testing

Run the test script:
```bash
cd AlgoAgent
python test_ai_strategy_api.py
```

Or with custom URL:
```bash
python test_ai_strategy_api.py http://your-server:8000
```

## Configuration

### Enable/Disable AI
Set `use_gemini: false` to disable AI analysis (uses basic validation only).

### Strict Mode
Set `strict_mode: true` to enable strict security validation (raises exceptions on violations).

## Troubleshooting

### "Strategy validator not available"
**Cause:** `Strategy/strategy_validator.py` not found  
**Fix:** Ensure Strategy module is in Python path

### "Gemini API error"
**Cause:** Invalid API key or quota exceeded  
**Fix:** Check `GEMINI_API_KEY` environment variable

### "Template not found"
**Cause:** Invalid `template_id`  
**Fix:** Use valid template ID or omit for auto-creation

## Next Steps

1. **Backtest Integration**: Link canonical JSON directly to backtesting engine
2. **Live Trading**: Add approval workflow for live trading strategies
3. **Version Control**: Track strategy versions with git-like diff
4. **Collaboration**: Share strategies and templates between users
5. **Performance Tracking**: Automatically track backtest results

## See Also

- [Strategy Module Documentation](../Strategy/README.md)
- [Interactive Strategy Tester](../Strategy/interactive_strategy_tester.py)
- [Canonical Schema](../Backtest/canonical_schema.py)
- [Gemini Integration](../Strategy/gemini_strategy_integrator.py)
