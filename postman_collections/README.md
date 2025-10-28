# AlgoAgent Postman Collections

This folder contains comprehensive Postman collections for testing the AlgoAgent Django API system.

## 🚀 Quick Start

**New to AlgoAgent? Start here:**

Import **`Quick_AI_Strategy_Validation.json`** for instant access to AI-powered strategy validation:
- Validate strategies with AI analysis
- Create strategies with automatic canonicalization
- Update strategies with AI re-validation
- Pre-configured examples (RSI, EMA, Bollinger)
- Built-in environment variables (no setup needed!)

Just import and test! 🎉

---

## Collections Included

### Quick Collections (Recommended for Testing)

#### Quick_AI_Strategy_Validation.json ⭐ NEW!
**AI Strategy Validation - Quick Start**
- **7 endpoints** ready to test immediately
- **3 core operations**: Validate, Create, Update with AI
- **3 example strategies**: RSI, EMA Crossover, Bollinger Bands
- **1 health check**: Verify AI modules are available
- **Auto-configured**: No environment setup required
- **Built-in tests**: Automatic validation of responses

**Perfect for:**
- Testing new AI validation features
- Quick demos
- Learning the AI API
- Development testing

---

### Full Collections

### 1. Auth_API_Collection.json
**Authentication & AI Chat API** ⭐ NEW!
- **Authentication** (5 endpoints): Register, login, logout, token refresh, current user
- **User Profile** (2 endpoints): Get and update user profiles
- **AI Context** (3 endpoints): Create and manage AI contexts for strategy development
- **AI Chat Agent** (4 endpoints): Interactive chat with Gemini AI for strategy development
- **Health Check** (1 endpoint): Auth API health monitoring

### 2. Data_API_Collection.json
**Data Management & Market Data API**
- **Health & Status** (3 endpoints): API health checks and status monitoring
- **Symbol Management** (6 endpoints): Create, read, update symbols and market data
- **Market Data** (4 endpoints): Fetch historical data, OHLCV data, real-time quotes
- **Indicators** (5 endpoints): Technical indicators calculation and retrieval
- **Data Requests** (3 endpoints): Data request management and caching

### 3. Strategy_API_Collection.json
**Strategy Development & Management API**
- **Health & Status** (2 endpoints): Strategy API health and categories
- **Strategy Templates** (4 endpoints): Template management for reusable strategies
- **Strategy Management** (7 endpoints): Full CRUD operations for trading strategies
- **Strategy Validation** (4 endpoints): Code validation and testing
- **AI Code Generation** (2 endpoints): AI-powered strategy code generation
- **Advanced Search** (3 endpoints): Sophisticated strategy search and filtering
- **Performance & Comments** (4 endpoints): Performance tracking and user feedback
- **Tags Management** (3 endpoints): Strategy categorization and organization

### 4. Strategy_AI_Validation_Collection.json ⭐ NEW!
**AI-Powered Strategy Validation & Creation API**
- **AI Validation** (2 endpoints): Validate strategies with AI analysis and recommendations
- **AI Creation** (2 endpoints): Create strategies with AI canonicalization and auto-template generation
- **AI Update** (1 endpoint): Update existing strategies with AI re-validation
- **Examples** (1 endpoint): Pre-built strategy examples with AI validation
- **Features**:
  - Canonicalization: Convert free-text to structured JSON
  - Classification: Auto-detect strategy type and risk level
  - Recommendations: AI-powered improvement suggestions
  - Security: Built-in guardrails and safety checks
  - Integration: Works with `interactive_strategy_tester.py` logic

### 5. Backtest_API_Collection.json
**Backtesting & Performance Analysis API**
- **Health & Status** (2 endpoints): Backtest engine health monitoring
- **Backtest Execution** (4 endpoints): Simple, advanced, multi-symbol, and quick backtests
- **Backtest Management** (6 endpoints): Full backtest lifecycle management
- **Results & Analytics** (6 endpoints): Performance metrics and result analysis
- **Trade Analysis** (6 endpoints): Individual trade tracking and statistics
- **Comparison & Analysis** (4 endpoints): Strategy comparison and risk analysis
- **Reports & Export** (4 endpoints): Report generation and data export
- **Real-time Monitoring** (4 endpoints): Live backtest monitoring and control

### 6. AlgoAgent_Environment.json
**Environment Variables**
Pre-configured environment with common variables:
- Base URLs for all API endpoints
- Default user credentials (algotrader/Trading@2024)
- Test symbols (AAPL, GOOGL)
- Default date ranges and parameters
- JWT token storage (auto-set after login)
- Common configuration values

## Setup Instructions

### Step 1: Import Collections
1. Open Postman
2. Click "Import" button
3. Select all 6 JSON files from this folder (including Strategy_AI_Validation_Collection.json)
4. Click "Import"
1. Open Postman
2. Click "Import" button
3. Select all 5 JSON files from this folder (including Auth_API_Collection.json)
4. Click "Import"

### Step 2: Set Environment
1. In Postman, click the environment dropdown (top right)
2. Select "AlgoAgent Development Environment"
3. Verify the `baseUrl` is set to `http://127.0.0.1:8000`

### Step 3: Start Django Server
Before testing, ensure your Django server is running:
```bash
cd c:\Users\nyaga\Documents\AlgoAgent\algoagent_api
python manage.py runserver
```

## Usage Guide

### Testing Workflow

#### 1. Start with Health Checks
- Test "API Root Health Check" in Data API
- Test "Strategy API Health Check" in Strategy API  
- Test "Backtest API Health Check" in Backtest API

#### 2. Set Up Basic Data
```
Data API → Symbol Management → Create Symbol (AAPL)
Data API → Market Data → Add Market Data
Data API → Indicators → Create Indicator
```

#### 3. Create and Test Strategies
```
Strategy API → Strategy Management → Create Strategy (Simple)
Strategy API → Strategy Validation → Validate Strategy
Strategy API → AI Code Generation → Generate Strategy Code
```

#### 4. Run Backtests
```
Backtest API → Backtest Execution → Run Simple Backtest
Backtest API → Results & Analytics → Get Backtest Results
Backtest API → Trade Analysis → Get All Trades
```

### Sample Test Sequences

#### Quick API Verification
1. **Data API → Health & Status → API Root Health Check**
2. **Strategy API → Health & Status → Strategy API Health Check**
3. **Backtest API → Health & Status → Backtest API Health Check**

#### Create Complete Strategy Workflow
1. **Data API → Symbol Management → Create Symbol**
2. **Strategy API → Strategy Management → Create Strategy (Simple)**
3. **Strategy API → Strategy Validation → Validate Strategy**
4. **Backtest API → Backtest Execution → Run Simple Backtest**
5. **Backtest API → Results & Analytics → Get Backtest Results**

#### Performance Analysis Workflow
1. **Backtest API → Backtest Execution → Run Advanced Backtest**
2. **Backtest API → Results & Analytics → Get Performance Metrics**
3. **Backtest API → Trade Analysis → Get Trade Statistics**
4. **Backtest API → Reports & Export → Generate Full Report**

## Environment Variables Reference

Key variables you can customize:

- `baseUrl`: Django server URL (default: http://127.0.0.1:8000)
- `testSymbol`: Primary test symbol (default: AAPL)
- `testStartDate`: Default backtest start date (default: 2024-01-01)
- `testEndDate`: Default backtest end date (default: 2024-12-31)
- `testCapital`: Default initial capital (default: 10000)

## API Authentication

Currently, the API does not require authentication. For production deployment, consider adding:
- JWT tokens
- API keys
- OAuth integration

## Error Handling

Common HTTP status codes:
- **200**: Success
- **201**: Created successfully
- **400**: Bad request (check JSON payload)
- **404**: Resource not found
- **500**: Server error (check Django logs)

## Tips for Effective Testing

1. **Use Environment Variables**: Leverage `{{variable}}` syntax for reusable values
2. **Test in Sequence**: Some endpoints depend on data created by others
3. **Check Responses**: Verify response structure matches expected format
4. **Save Examples**: Use Postman's "Save as Example" for successful requests
5. **Monitor Server**: Keep an eye on Django server console for error messages

## Troubleshooting

### Common Issues

**Django Server Not Running**
- Ensure server is started: `python manage.py runserver`
- Check if port 8000 is available

**Database Errors**
- Run migrations: `python manage.py migrate`
- Check SQLite database permissions

**Import Errors**
- Verify Django apps are properly installed
- Check module paths in settings.py

**CORS Issues**
- Ensure `django-cors-headers` is installed
- Verify CORS settings in Django configuration

## Advanced Usage

### Custom Test Scripts
You can add Postman test scripts to automate validations:

```javascript
// Example test script for API health check
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has status field", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('status');
});
```

### Collection Runner
Use Postman's Collection Runner to:
1. Run entire collections automatically
2. Test with different data sets
3. Generate test reports
4. Schedule automated tests

## Support

For issues with the API or these collections:
1. Check Django server logs
2. Verify database state
3. Test individual endpoints
4. Review API documentation in `/api/` endpoint

Happy testing! 🚀