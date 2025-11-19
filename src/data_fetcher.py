"""
Module for fetching publicly available stock market data.

This module provides functionality to fetch historical stock price data
from free public sources using yfinance library.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import time


class StockDataFetcher:
    """Fetches stock market data from publicly available sources."""

    def __init__(self, cache_dir: str = "data"):
        """
        Initialize the data fetcher.

        Args:
            cache_dir: Directory to cache downloaded data
        """
        self.cache_dir = cache_dir

    def fetch_yahoo_historical(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d",
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch historical stock data from Yahoo Finance using yfinance.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            start_date: Start date in YYYY-MM-DD format (default: 1 year ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            interval: Data interval - '1d', '1wk', '1mo'
            use_cache: Try to load from cache first if True

        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Volume, Adj Close
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Try loading from cache first
        if use_cache:
            cached_df = self._load_from_cache(symbol)
            if cached_df is not None and len(cached_df) > 0:
                # Filter by date range if requested
                if start_date and end_date:
                    cached_df = cached_df[
                        (cached_df['Date'] >= start_date) & 
                        (cached_df['Date'] <= end_date)
                    ]
                return cached_df
        
        # Handle minute-level interval limits
        minute_intervals = {"1m": 7, "2m": 60, "5m": 60, "15m": 365, "30m": 365, "60m": 365}
        if interval in minute_intervals:
            # yfinance / Yahoo generally only provides very short-term minute data for free.
            # We'll enforce conservative limits to avoid large, impossible requests.
            max_days = minute_intervals.get(interval, 7)
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d') if start_date else datetime.now() - timedelta(days=max_days)
                end_dt = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()
            except Exception:
                start_dt = datetime.now() - timedelta(days=max_days)
                end_dt = datetime.now()

            delta_days = (end_dt - start_dt).days
            if delta_days > max_days:
                # Truncate the range to the maximum allowed for minute data
                new_start = end_dt - timedelta(days=max_days)
                print(f"Requested minute-level range ({delta_days} days) exceeds available limit for '{interval}'. Truncating to last {max_days} days: {new_start.date()} -> {end_dt.date()}")
                start_date = new_start.strftime('%Y-%m-%d')
                # proceed with truncated dates

        try:
            # Use yfinance to fetch data
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval=interval)

            if df.empty:
                print(f"No data retrieved for {symbol}")
                return pd.DataFrame()

            # Reset index to make Date/Datetime a column
            df = df.reset_index()
            
            # Handle both 'Date' (daily) and 'Datetime' (intraday) column names
            if 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'Date'})
            elif 'Date' not in df.columns:
                # If neither exists, create one from index
                df['Date'] = df.index
            
            # Ensure Date column is datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('Date')

            # Cache the data (if use_cache is True; normally False for this new pipeline)
            if use_cache:
                self._save_to_cache(df, symbol)

            return df

        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_multiple_symbols(
        self,
        symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple symbols with rate limiting.

        Args:
            symbols: List of stock ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            use_cache: Use cached data if available

        Returns:
            Dictionary mapping symbol to DataFrame
        """
        data = {}
        for i, symbol in enumerate(symbols):
            print(f"[{i+1}/{len(symbols)}] Fetching data for {symbol}...")
            df = self.fetch_yahoo_historical(symbol, start_date, end_date, use_cache=use_cache)
            data[symbol] = df

            # Rate limiting: wait 0.5 seconds between requests
            if i < len(symbols) - 1:
                time.sleep(0.5)

        return data

    def get_current_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get current stock quote information.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with quote information or None if failed
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                'symbol': symbol,
                'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
                'previous_close': info.get('previousClose'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'dividend_yield': info.get('dividendYield'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
            }

        except Exception as e:
            print(f"Error fetching quote for {symbol}: {e}")
            return None

    def _save_to_cache(self, df: pd.DataFrame, symbol: str) -> None:
        """Save DataFrame to cache file."""
        import os
        os.makedirs(self.cache_dir, exist_ok=True)
        cache_file = os.path.join(self.cache_dir, f"{symbol}.csv")
        df.to_csv(cache_file, index=False)

    def _load_from_cache(self, symbol: str) -> Optional[pd.DataFrame]:
        """Load DataFrame from cache file."""
        import os
        cache_file = os.path.join(self.cache_dir, f"{symbol}.csv")

        if os.path.exists(cache_file):
            try:
                df = pd.read_csv(cache_file)
                df['Date'] = pd.to_datetime(df['Date'])
                return df
            except Exception as e:
                print(f"Error loading cache for {symbol}: {e}")
                return None
        return None

    def save_to_csv(self, df: pd.DataFrame, filename: str) -> None:
        """Save DataFrame to CSV file."""
        import os
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")

    def load_from_csv(self, filename: str) -> pd.DataFrame:
        """Load DataFrame from CSV file."""
        df = pd.read_csv(filename)
        df['Date'] = pd.to_datetime(df['Date'])
        return df

    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """
        Clear cache for specific symbol or all symbols.

        Args:
            symbol: If provided, clear only this symbol's cache. Otherwise clear all.
        """
        import os
        import glob

        if symbol:
            cache_file = os.path.join(self.cache_dir, f"{symbol}.csv")
            if os.path.exists(cache_file):
                os.remove(cache_file)
                print(f"Cleared cache for {symbol}")
        else:
            cache_files = glob.glob(os.path.join(self.cache_dir, "*.csv"))
            for f in cache_files:
                os.remove(f)
            print(f"Cleared cache for all stocks")
