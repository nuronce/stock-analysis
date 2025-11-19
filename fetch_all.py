"""
Download helper to fetch daily 10y and available intraday (most granular) data
and save as Parquet-only files using `CacheManager`.

This script is a controlled runner — it does not start automatically when imported.
Run it with `python fetch_all.py` when you want to perform the full download.
"""

import time
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

# ensure src is on path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_fetcher import StockDataFetcher
from cache_manager import CacheManager
from stock_list import get_all_stocks


def fetch_for_symbol(fetcher, cache_mgr, symbol, verbose=True):
    # 1) Daily 10y
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=365 * 10)
    daily_ok = False
    if verbose:
        print(f"[{symbol}] Fetching daily from {start} to {end}...", end=" ")
    try:
        df_daily = fetcher.fetch_yahoo_historical(symbol, start_date=str(start), end_date=str(end), interval='1d', use_cache=False)
        if df_daily is not None and len(df_daily) > 0:
            cache_mgr.save_cached_symbol(symbol, df_daily, freq='daily')
            print(f"✓ ({len(df_daily)} rows)")
            daily_ok = True
        else:
            print("✗ (no data)")
    except Exception as e:
        print(f"✗ ({str(e)[:30]})")

    # 2) Most granular intraday — try 1m and let fetcher truncate to provider limits
    # Skip if daily failed (skip intraday to save time)
    if not daily_ok:
        return
    
    try:
        if verbose:
            print(f"[{symbol}] Fetching intraday 1m...", end=" ")
        df_1m = fetcher.fetch_yahoo_historical(symbol, start_date=None, end_date=None, interval='1m', use_cache=False)
        if df_1m is not None and len(df_1m) > 0:
            cache_mgr.save_cached_symbol(symbol, df_1m, freq='1m')
            print(f"✓ ({len(df_1m)} rows)")
        else:
            print("✗ (no data)")
    except Exception as e:
        print(f"✗ ({str(e)[:30]})")


def main(symbols=None, delay=0.6):
    fetcher = StockDataFetcher()
    cache_mgr = CacheManager()

    if symbols is None:
        symbols = get_all_stocks()

    total = len(symbols)
    print(f"Starting fetch for {total} symbols (daily 10y + available 1m). This may take a while.")

    for i, s in enumerate(symbols, 1):
        print(f"\n[{i}/{total}] Processing {s}")
        fetch_for_symbol(fetcher, cache_mgr, s)
        time.sleep(delay)

    print("\nFetch run complete. Use example.py to analyze cached data.")


if __name__ == '__main__':
    main()
