# Backtest Data Cache

This directory stores processed market data with computed indicators.

## Purpose

When strategies request data with indicators, the `data_loader` module:
1. Loads raw CSV data from `Data/data/` folder
2. Computes requested technical indicators
3. Caches the result here as `.parquet` files
4. Reuses cached data on subsequent runs (if source hasn't changed)

## File Format

Cached files are named:
```
TICKER_INDICATOR1_INDICATOR2_DATE_TIME.parquet
```

Example:
```
AAPL_RSI_SMA_20251013_182543.parquet
```

## Benefits

- **Performance**: Indicators computed once, cached for reuse
- **Consistency**: Same indicator values across multiple strategy runs
- **Efficiency**: Parquet format is faster to read than CSV

## Cleaning Cache

To force recomputation of indicators, delete files from this directory.

## DO NOT MODIFY

This directory is managed automatically by the `data_loader` module.
