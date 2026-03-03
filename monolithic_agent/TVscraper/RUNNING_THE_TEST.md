# Running the Multi-Symbol Data Fetcher

## Prerequisites

Before running the test script, you need to have the following set up:

### 1. MCP Chrome Server Running

The TradingView scraper uses the **Model Context Protocol (MCP) Chrome DevTools** to interact with the browser. You need to:

1. Install the MCP Chrome tools:
   ```powershell
   npm install -g @modelcontextprotocol/server-chrome
   ```

2. Start the MCP Chrome server:
   ```powershell
   npx @modelcontextprotocol/server-chrome
   ```

3. The server should be running and accessible

### 2. TradingView Page Open in Chrome

1. Open Google Chrome browser
2. Navigate to https://www.tradingview.com/chart/
3. Make sure you're logged in (if required)
4. The chart should be fully loaded

### 3. Python Environment

Install required packages:
```powershell
pip install -r requirements.txt
```

## Running the Test

Once all prerequisites are met:

```powershell
cd C:\Users\nyaga\Documents\TVscraper
python test_multi_symbol_fetch.py
```

## What the Script Does

The script will:

1. ✓ Create a `DataTV` folder
2. ✓ Initialize the scraper
3. For each symbol (MSFT, AAPL, TSLA):
   - Change to the symbol
   - Set timeframe to 5 minutes
   - Clear existing indicators
   - Add EMA 20 indicator
   - Add EMA 50 indicator
   - Fetch current market data
   - Save to CSV file

## Expected Output

```
======================================================================
TradingView Multi-Symbol Data Fetcher
======================================================================

⚠️  PREREQUISITES:
   1. TradingView must be open in Chrome
   2. MCP Chrome server must be running

✓ Data folder created: C:\Users\nyaga\Documents\TVscraper\DataTV

Initializing TradingView scraper...
✓ Scraper initialized

[1/3] Processing MSFT
--------------------------------------------------
  → Changing to MSFT...
  ✓ Symbol changed to MSFT
  → Setting timeframe to 5 minutes...
  ✓ Timeframe set to 5m
  → Clearing existing indicators...
  → Adding EMA 20...
  ✓ EMA 20 added
  → Adding EMA 50...
  ✓ EMA 50 added
  → Fetching market data...
  ✓ Data fetched successfully
    - Price: $425.50
    - Volume: 15234567
    - Indicators found: 2
      • EMA(20): 424.30
      • EMA(50): 422.10
  → Saving to CSV: MSFT_5m_ema.csv...
  ✓ Data saved to C:\Users\nyaga\Documents\TVscraper\DataTV\MSFT_5m_ema.csv

[2/3] Processing AAPL
--------------------------------------------------
  ... (similar output)

[3/3] Processing TSLA
--------------------------------------------------
  ... (similar output)

======================================================================
SUMMARY
======================================================================
✓ Successfully created 3 CSV files:
  • MSFT_5m_ema.csv (1,234 bytes)
  • AAPL_5m_ema.csv (1,189 bytes)
  • TSLA_5m_ema.csv (1,256 bytes)

Data folder location: C:\Users\nyaga\Documents\TVscraper\DataTV
```

## Troubleshooting

### Error: "cannot connect to MCP server"
- Make sure the MCP Chrome server is running: `npx @modelcontextprotocol/server-chrome`
- Check that Chrome is open with TradingView loaded

### Error: "MCPTradingViewScraper has no attribute 'open_tradingview'"
- This is expected - the scraper doesn't open TradingView automatically
- You must open TradingView in Chrome manually before running the script

### Error: "Symbol change failed"
- The chart might not be fully loaded
- Try increasing the `time.sleep()` values in the script
- Make sure you're on the TradingView chart page, not another page

### No indicators in output
- The indicator detection might need more time
- Try increasing delays after adding indicators
- Check that indicators are visible on the chart manually

### CSV files empty or missing data
- The `get_market_data()` method might need implementation
- Check the mcp_scraper.py file for the actual implementation
- Some methods might be using placeholder/demo code

## Alternative: Demo Mode

If you don't have MCP set up, you can modify the script to use demo data by:

1. Commenting out the actual scraper calls
2. Using sample data instead
3. Just creating the CSV files with mock data

See [examples/demo.py](examples/demo.py) for a demo mode example.

## Output Files

The CSV files in the `DataTV` folder will contain:

```csv
timestamp,symbol,timeframe,price,volume,ema_20,ema_50
2026-02-08 14:30:00,MSFT,5m,425.50,15234567,424.30,422.10
```

You can open these in:
- Excel
- Python (pandas): `pd.read_csv('DataTV/MSFT_5m_ema.csv')`
- Any CSV viewer

## Next Steps

After successfully running the script:

1. Analyze the CSV data
2. Compare EMA values across symbols
3. Use the data for backtesting strategies
4. Modify the script to fetch different indicators or timeframes
