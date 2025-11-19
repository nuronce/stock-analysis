"""
Cache management module for storing and retrieving stock data efficiently.

Provides functionality to manage a local database of stock data,
reducing the need to re-download data frequently.
"""

import json
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional


class CacheManager:
    """Manages caching of stock data and metadata."""

    def __init__(self, cache_dir: str = "data", index_file: str = "data/index.json"):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store cached data
            index_file: File to store cache index metadata
        """
        self.cache_dir = cache_dir
        self.index_file = index_file
        os.makedirs(cache_dir, exist_ok=True)
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        """Load the cache index from file."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading index: {e}")
                return {}
        return {}

    def _save_index(self) -> None:
        """Save the cache index to file."""
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            print(f"Error saving index: {e}")

    def get_cached_symbol(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Get cached data for a symbol. Prefer parquet if available.

        Args:
            symbol: Stock ticker symbol

        Returns:
            DataFrame if cached, None otherwise
        """
        # Look for parquet files with frequency suffixes first (e.g., SYMBOL_daily.parquet, SYMBOL_1m.parquet)
        candidates = []
        for fname in os.listdir(self.cache_dir):
            if not fname.endswith('.parquet'):
                continue
            # match symbol or symbol_<freq>.parquet
            if fname == f"{symbol}.parquet" or fname.startswith(f"{symbol}_") or fname.startswith(f"{symbol}."):
                candidates.append(fname)

        # Prefer a daily file if present
        pref = None
        for c in candidates:
            if c.startswith(f"{symbol}_daily"):
                pref = c
                break
        if pref is None and candidates:
            pref = candidates[0]

        if pref:
            parquet_file = os.path.join(self.cache_dir, pref)
            try:
                df = pd.read_parquet(parquet_file)
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                return df
            except Exception as e:
                print(f"Error reading parquet cache for {symbol}: {e}")
                return None

        # Legacy CSV fallback (if any CSVs remain)
        cache_file = os.path.join(self.cache_dir, f"{symbol}.csv")
        if os.path.exists(cache_file):
            try:
                df = pd.read_csv(cache_file)
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                return df
            except Exception as e:
                print(f"Error reading cache for {symbol}: {e}")
                return None

        return None

    def save_cached_symbol(self, symbol: str, df: pd.DataFrame, freq: str = 'daily') -> bool:
        """
        Save data for a symbol to Parquet cache only (preferred).

        Args:
            symbol: Stock ticker symbol
            df: DataFrame with stock data
            freq: Frequency suffix used in filename (e.g., 'daily', '1m')
        """
        try:
            if df is None or len(df) == 0:
                return False
            
            os.makedirs(self.cache_dir, exist_ok=True)
            parquet_file = os.path.join(self.cache_dir, f"{symbol}_{freq}.parquet")
            df.to_parquet(parquet_file, index=False)

            key = f"{symbol}_{freq}"
            # Handle Date column safely
            start_date = None
            end_date = None
            if 'Date' in df.columns:
                start_date = str(df['Date'].min())
                end_date = str(df['Date'].max())
            
            self.index[key] = {
                'cached_date': datetime.now().isoformat(),
                'rows': len(df),
                'start_date': start_date,
                'end_date': end_date,
                'parquet': os.path.basename(parquet_file),
            }
            self._save_index()
            return True
        except Exception as e:
            print(f"Error saving parquet cache for {symbol}: {e}")
            return False

    def save_parquet_symbol(self, symbol: str, df: pd.DataFrame, freq: str = 'daily') -> bool:
        """Save DataFrame to Parquet with frequency suffix and update index.

        Args:
            symbol: ticker symbol
            df: DataFrame to save
            freq: frequency string used as suffix (e.g., 'daily', '1m')
        """
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            parquet_file = os.path.join(self.cache_dir, f"{symbol}_{freq}.parquet")
            df.to_parquet(parquet_file, index=False)

            key = f"{symbol}_{freq}"
            self.index[key] = {
                'cached_date': datetime.now().isoformat(),
                'rows': len(df),
                'start_date': str(df['Date'].min()),
                'end_date': str(df['Date'].max()),
                'parquet': os.path.basename(parquet_file),
            }
            self._save_index()
            return True
        except Exception as e:
            print(f"Error saving parquet for {symbol} ({freq}): {e}")
            return False


    def get_cached_symbols(self) -> List[str]:
        """Get list of all cached symbols."""
        symbols = set()
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.parquet'):
                # strip suffix like _daily or _1m
                base = filename.rsplit('.', 1)[0]
                if '_' in base:
                    base_sym = base.split('_', 1)[0]
                else:
                    base_sym = base
                symbols.add(base_sym)
            elif filename.endswith('.csv'):
                symbols.add(filename.replace('.csv', ''))
        return sorted(symbols)

    def get_cache_info(self, symbol: str) -> Optional[Dict]:
        """Get metadata about cached data for a symbol."""
        # Prefer daily info if present, otherwise return any matching frequency
        daily_key = f"{symbol}_daily"
        if daily_key in self.index:
            return self.index[daily_key]
        # search for any key that starts with symbol_
        for k, v in self.index.items():
            if k.startswith(f"{symbol}_"):
                return v
        # legacy single-key entries
        return self.index.get(symbol)

    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """
        Clear cache for symbol(s).

        Args:
            symbol: If provided, clear only this symbol. Otherwise clear all.
        """
        if symbol:
            # remove any parquet or csv for this symbol
            for fname in os.listdir(self.cache_dir):
                if fname.startswith(f"{symbol}") and (fname.endswith('.csv') or fname.endswith('.parquet')):
                    try:
                        os.remove(os.path.join(self.cache_dir, fname))
                    except Exception:
                        pass
            # remove index entries for this symbol
            keys = [k for k in list(self.index.keys()) if k == symbol or k.startswith(f"{symbol}_")]
            for k in keys:
                del self.index[k]
            self._save_index()
            print(f"Cleared cache for {symbol}")
        else:
            for fname in os.listdir(self.cache_dir):
                if fname.endswith('.csv') or fname.endswith('.parquet'):
                    try:
                        os.remove(os.path.join(self.cache_dir, fname))
                    except Exception:
                        pass
            self.index = {}
            self._save_index()
            print("Cleared all cache")

    def get_cache_summary(self) -> Dict:
        """Get summary statistics of cached data."""
        symbols = self.get_cached_symbols()
        total_rows = 0
        total_size = 0

        for symbol in symbols:
            cache_file = os.path.join(self.cache_dir, f"{symbol}.csv")
            if os.path.exists(cache_file):
                total_size += os.path.getsize(cache_file)
                info = self.get_cache_info(symbol)
                if info:
                    total_rows += info.get('rows', 0)

        return {
            'total_symbols': len(symbols),
            'total_rows': total_rows,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'symbols': symbols,
        }

    def export_summary(self, filename: str = "cache_summary.csv") -> None:
        """Export cache summary to CSV file."""
        data = []
        for symbol in self.get_cached_symbols():
            info = self.get_cache_info(symbol)
            if info:
                data.append({
                    'Symbol': symbol,
                    'Cached Date': info.get('cached_date'),
                    'Rows': info.get('rows'),
                    'Start Date': info.get('start_date'),
                    'End Date': info.get('end_date'),
                })

        if data:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            print(f"Summary exported to {filename}")
