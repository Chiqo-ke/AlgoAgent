# AlgoAgent Django API Integration

## 🎉 Integration Complete!

You now have a fully functional Django REST API integrated with your existing AlgoAgent system. The API provides access to your data fetching, strategy management, and backtesting capabilities through HTTP endpoints.

## 🚀 Quick Start

### 1. Start the API Server

```bash
# Activate virtual environment (if not already activated)
.venv\Scripts\activate

# Start Django development server
python manage.py runserver 8000
```

The API will be available at: **http://127.0.0.1:8000**

### 2. Access the API

- **API Root**: http://127.0.0.1:8000/api/
- **Browsable API**: http://127.0.0.1:8000/api/data/ (interactive documentation)
- **Admin Interface**: http://127.0.0.1:8000/admin/ (requires superuser)

## 📡 API Endpoints

### Data API (`/api/data/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/data/symbols/` | GET, POST | Manage trading symbols |
| `/api/data/market-data/` | GET, POST | Access market data |
| `/api/data/indicators/` | GET, POST | Manage indicators |
| `/api/data/api/fetch_data/` | POST | Fetch market data for symbols |
| `/api/data/api/calculate_indicator/` | POST | Calculate indicators |
| `/api/data/api/available_indicators/` | GET | List available indicators |
| `/api/data/api/health/` | GET | Health check |

### Strategy API (`/api/strategies/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/strategies/strategies/` | GET, POST | Manage strategies |
| `/api/strategies/templates/` | GET, POST | Strategy templates |
| `/api/strategies/validations/` | GET | View validations |
| `/api/strategies/api/create_strategy/` | POST | Create new strategy |
| `/api/strategies/api/generate_code/` | POST | AI code generation |
| `/api/strategies/api/search/` | POST | Advanced search |
| `/api/strategies/api/health/` | GET | Health check |

### Backtest API (`/api/backtests/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/backtests/runs/` | GET, POST | Manage backtest runs |
| `/api/backtests/configs/` | GET, POST | Backtest configurations |
| `/api/backtests/results/` | GET | View results |
| `/api/backtests/trades/` | GET | View trades |
| `/api/backtests/api/run_backtest/` | POST | Start new backtest |
| `/api/backtests/api/quick_run/` | POST | Quick backtest |
| `/api/backtests/api/create_config/` | POST | Create configuration |
| `/api/backtests/api/health/` | GET | Health check |

## 🧪 Testing the API

### Method 1: Simple Test Script

```bash
python simple_api_test.py
```

### Method 2: Comprehensive Test Suite

```bash
python test_api.py
```

### Method 3: Manual Browser Testing

1. Open http://127.0.0.1:8000/api/ in your browser
2. Navigate to any endpoint for interactive documentation
3. Use the Django REST Framework's browsable API

### Method 4: curl Examples

```bash
# Test API root
curl http://127.0.0.1:8000/api/

# Health checks
curl http://127.0.0.1:8000/api/data/api/health/
curl http://127.0.0.1:8000/api/strategies/api/health/
curl http://127.0.0.1:8000/api/backtests/api/health/

# Create a symbol
curl -X POST http://127.0.0.1:8000/api/data/symbols/ \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "name": "Apple Inc."}'

# Fetch market data
curl -X POST http://127.0.0.1:8000/api/data/api/fetch_data/ \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "period": "1mo", "interval": "1d"}'
```

## 📊 Database Models

### Data Models
- **Symbol**: Trading symbols (AAPL, MSFT, etc.)
- **MarketData**: OHLCV price data
- **Indicator**: Technical indicator definitions
- **IndicatorData**: Calculated indicator values
- **DataRequest**: Track data fetch requests
- **DataCache**: Cache for processed data

### Strategy Models
- **Strategy**: Trading strategy definitions
- **StrategyTemplate**: Reusable strategy templates
- **StrategyValidation**: Validation results
- **StrategyPerformance**: Performance metrics
- **StrategyComment**: User comments and reviews
- **StrategyTag**: Categorization tags

### Backtest Models
- **BacktestConfig**: Backtest parameters
- **BacktestRun**: Execution runs
- **BacktestResult**: Detailed results
- **Trade**: Individual trades
- **BacktestAlert**: Notifications and warnings

## 🔧 Configuration

### Django Settings (`algoagent_api/settings.py`)

The API is configured with:
- SQLite database for development
- Django REST Framework
- CORS headers for web access
- Custom pagination (50 items per page)
- Browsable API renderer
- Debug mode enabled for development

### Environment Variables

Create a `.env` file for production settings:

```
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost
DATABASE_URL=sqlite:///production.db
```

## 🔗 Integration with Existing Modules

The Django API seamlessly integrates with your existing AlgoAgent modules:

### Data Integration
- **DataFetcher** (`Data/data_fetcher.py`): Used for fetching market data
- **IndicatorCalculator** (`Data/indicator_calculator.py`): For computing indicators
- **Registry** (`Data/registry.py`): Lists available indicators

### Strategy Integration
- **StrategyValidator** (`Strategy/strategy_validator.py`): Validates strategies
- **GeminiIntegrator** (`Strategy/gemini_strategy_integrator.py`): AI-powered analysis

### Backtest Integration
- **InteractiveBacktestRunner** (`Backtest/interactive_backtest_runner.py`): Executes backtests
- **StrategyManager** (`Backtest/strategy_manager.py`): Manages strategy lifecycle

## 📦 Dependencies

The Django integration adds these new dependencies:
- `django` - Web framework
- `djangorestframework` - REST API framework
- `django-cors-headers` - CORS support

All existing dependencies are preserved and utilized.

## 🛠️ Development Workflow

### 1. Making API Changes

```bash
# After model changes
python manage.py makemigrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### 2. Adding New Endpoints

1. Update models in `{app}/models.py`
2. Create serializers in `{app}/serializers.py`
3. Add views in `{app}/views.py`
4. Update URLs in `{app}/urls.py`

### 3. Testing Changes

```bash
# Run Django tests
python manage.py test

# Run API tests
python test_api.py
```

## 🌐 Production Deployment

### 1. Environment Setup

```bash
# Set environment variables
export DEBUG=False
export SECRET_KEY="your-production-secret-key"
export ALLOWED_HOSTS="yourdomain.com"

# Collect static files
python manage.py collectstatic

# Create superuser
python manage.py createsuperuser
```

### 2. WSGI Deployment

Use a production WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn algoagent_api.wsgi:application --bind 0.0.0.0:8000
```

### 3. Database Migration

For production, consider PostgreSQL:

```bash
pip install psycopg2
# Update DATABASES setting in settings.py
python manage.py migrate
```

## 📝 API Usage Examples

### Python Client Example

```python
import requests

# Base URL
API_BASE = "http://127.0.0.1:8000/api"

# Fetch market data
response = requests.post(f"{API_BASE}/data/api/fetch_data/", json={
    "symbol": "AAPL",
    "period": "1y",
    "interval": "1d",
    "indicators": ["sma", "rsi"]
})
data = response.json()

# Create a strategy
strategy_data = {
    "name": "My Strategy",
    "strategy_code": "# Your strategy code here",
    "description": "A test strategy"
}
response = requests.post(f"{API_BASE}/strategies/api/create_strategy/", json=strategy_data)
strategy = response.json()

# Run a quick backtest
backtest_data = {
    "strategy_code": "# Simple strategy",
    "symbol": "AAPL",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
}
response = requests.post(f"{API_BASE}/backtests/api/quick_run/", json=backtest_data)
results = response.json()
```

### JavaScript/Web Client Example

```javascript
// Fetch available indicators
fetch('http://127.0.0.1:8000/api/data/api/available_indicators/')
  .then(response => response.json())
  .then(data => console.log('Indicators:', data.indicators));

// Create and run backtest
const backtestData = {
  strategy_code: '# Your strategy here',
  symbol: 'AAPL',
  start_date: '2024-01-01',
  end_date: '2024-12-31'
};

fetch('http://127.0.0.1:8000/api/backtests/api/quick_run/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(backtestData)
})
.then(response => response.json())
.then(results => console.log('Backtest results:', results));
```

## 🎯 Next Steps

1. **Create Admin User**: `python manage.py createsuperuser`
2. **Explore the API**: Visit http://127.0.0.1:8000/api/data/ for interactive docs
3. **Test Integration**: Run your existing strategies through the API
4. **Build Frontend**: Create a web interface using the API
5. **Scale Up**: Deploy to production with proper WSGI server

## 🆘 Troubleshooting

### Common Issues

1. **Port Already in Use**:
   ```bash
   # Use different port
   python manage.py runserver 8080
   ```

2. **Module Import Errors**:
   - Ensure virtual environment is activated
   - Check that all original modules are accessible

3. **Database Issues**:
   ```bash
   # Reset database
   rm db.sqlite3
   python manage.py migrate
   ```

4. **API Not Responding**:
   - Check server logs in terminal
   - Verify firewall/antivirus settings
   - Try different browser/client

### Getting Help

- Check Django logs in the terminal running the server
- Use the browsable API for debugging endpoints
- Review the health check endpoints for module availability

---

🎉 **Congratulations!** Your AlgoAgent system now has a full REST API interface. You can now build web frontends, mobile apps, or integrate with other systems using standard HTTP requests.