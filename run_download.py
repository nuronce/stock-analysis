"""Run a forced download of 1m data for the full stock list and cache as parquet.

This script imports the helper from example.py and runs it with force_refresh=True
so cached files will be overwritten with fresh downloads (subject to provider limits).
"""

from src.data_fetcher import StockDataFetcher
from src.cache_manager import CacheManager
from src.stock_list import get_all_stocks
from example import download_stock_database


def main():
    fetcher = StockDataFetcher()
    cache_mgr = CacheManager()

    symbols = get_all_stocks()
    print(f"Starting forced download for {len(symbols)} symbols (interval=1m).\nThis will be truncated to provider limits and may take several minutes.")

    download_stock_database(fetcher, cache_mgr, symbols=symbols, force_refresh=True, interval='1m')


if __name__ == '__main__':
    main()
