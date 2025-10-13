# AlgoAgent/Data/data_fetcher.py

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class DataFetcher:
    def __init__(self):
        pass

    def fetch_historical_data(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """
        Fetches historical financial data for a given ticker.

        Args:
            ticker (str): The stock ticker symbol (e.g., "AAPL").
            period (str): The period over which to fetch data (e.g., "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max").
            interval (str): The interval of the data (e.g., "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "3mo").

        Returns:
            pd.DataFrame: A DataFrame containing the historical data.
        """
        try:
            data = yf.download(ticker, period=period, interval=interval)
            if data.empty:
                print(f"No data found for {ticker} with period {period} and interval {interval}")
            return data
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_data_by_date_range(self, ticker: str, start_date: str, end_date: str, interval: str = "1d") -> pd.DataFrame:
        """
        Fetches historical financial data for a given ticker within a specified date range.

        Args:
            ticker (str): The stock ticker symbol (e.g., "AAPL").
            start_date (str): The start date in "YYYY-MM-DD" format.
            end_date (str): The end date in "YYYY-MM-DD" format.
            interval (str): The interval of the data (e.g., "1d", "1wk", "1mo").

        Returns:
            pd.DataFrame: A DataFrame containing the historical data.
        """
        try:
            data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
            if data.empty:
                print(f"No data found for {ticker} between {start_date} and {end_date} with interval {interval}")
            return data
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

if __name__ == "__main__":
    fetcher = DataFetcher()

    # Example usage: Fetch 1 year of daily data for Apple
    aapl_data = fetcher.fetch_historical_data("AAPL", period="1y", interval="1d")
    if not aapl_data.empty:
        print("AAPL 1 year daily data:")
        print(aapl_data.head())

    # Example usage: Fetch data for Google between specific dates
    start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")
    goog_data = fetcher.fetch_data_by_date_range("GOOG", start_date=start, end_date=end, interval="1d")
    if not goog_data.empty:
        print(f"\nGOOG data from {start} to {end}:")
        print(goog_data.head())