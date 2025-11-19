"""
Example script demonstrating stock data analysis.

This script shows how to fetch and cache stock data for 100 popular stocks,
and perform various analyses without re-downloading.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_fetcher import StockDataFetcher
from analyzer import StockAnalyzer
from cache_manager import CacheManager
from stock_list import get_all_stocks, get_stocks_by_category
import pandas as pd
from datetime import datetime, timedelta


def download_stock_database(fetcher, cache_mgr, symbols=None, force_refresh=False, interval='1d', start_date=None, end_date=None):
    """
    Download and cache stock data for multiple symbols.

    Args:
        fetcher: StockDataFetcher instance
        cache_mgr: CacheManager instance
        symbols: List of symbols to download (default: all 100 stocks)
        force_refresh: Force re-download even if cached
    """
    if symbols is None:
        symbols = get_all_stocks()

    print("=" * 70)
    print(f"Stock Database Download & Cache")
    print("=" * 70)
    print(f"Total stocks to process: {len(symbols)}\n")

    successful = 0
    failed = 0
    skipped = 0

    for i, symbol in enumerate(symbols, 1):
        # Check if already cached
        if not force_refresh and cache_mgr.get_cached_symbol(symbol) is not None:
            print(f"[{i:3d}/{len(symbols)}] {symbol:6s} - Already cached (skipped)")
            skipped += 1
            continue

        print(f"[{i:3d}/{len(symbols)}] {symbol:6s} - Downloading...", end=" ")

        try:
            df = fetcher.fetch_yahoo_historical(symbol, start_date=start_date, end_date=end_date, interval=interval, use_cache=False)

            if not df.empty:
                cache_mgr.save_cached_symbol(symbol, df)
                print(f"✓ ({len(df)} rows)")
                successful += 1
            else:
                print("✗ (No data)")
                failed += 1

        except Exception as e:
            print(f"✗ (Error: {str(e)[:40]})")
            failed += 1
        finally:
            # small delay to avoid aggressive request bursts
            import time
            time.sleep(0.5)

    print("\n" + "=" * 70)
    print(f"Results: {successful} successful, {failed} failed, {skipped} skipped")
    print("=" * 70)

    # Show cache summary
    summary = cache_mgr.get_cache_summary()
    print(f"\nCache Summary:")
    print(f"  Total symbols cached: {summary['total_symbols']}")
    print(f"  Total data rows:      {summary['total_rows']:,}")
    print(f"  Cache size:           {summary['total_size_mb']:.2f} MB")


def analyze_category(analyzer_class, cache_mgr, category=None):
    """
    Analyze stocks in a category or all stocks.

    Args:
        analyzer_class: StockAnalyzer class
        cache_mgr: CacheManager instance
        category: Category to analyze (e.g., 'mega_cap', 'finance', etc.)
    """
    if category:
        symbols = get_stocks_by_category(category)
        print(f"\n{'=' * 70}")
        print(f"Analysis: {category.upper()} Stocks")
        print(f"{'=' * 70}\n")
    else:
        symbols = cache_mgr.get_cached_symbols()
        print(f"\n{'=' * 70}")
        print(f"Analysis: All Cached Stocks ({len(symbols)})")
        print(f"{'=' * 70}\n")

    results = []

    for symbol in symbols:
        df = cache_mgr.get_cached_symbol(symbol)

        if df is None or len(df) == 0:
            continue

        try:
            analyzer = analyzer_class(df)
            summary = analyzer.get_performance_summary()

            results.append({
                'Symbol': symbol,
                'Return %': summary['total_return_pct'],
                'Volatility %': summary['annual_volatility_pct'],
                'Sharpe Ratio': summary['sharpe_ratio'],
                'Price': summary['current_price'],
                'High': summary['max_price'],
                'Low': summary['min_price'],
            })
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")

    if results:
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values('Return %', ascending=False)

        print(df_results.to_string(index=False))

        # Summary statistics
        print(f"\n{'Category Statistics:':^70}")
        print(f"  Average Return:      {df_results['Return %'].mean():>7.2f}%")
        print(f"  Average Volatility:  {df_results['Volatility %'].mean():>7.2f}%")
        print(f"  Avg Sharpe Ratio:    {df_results['Sharpe Ratio'].mean():>7.2f}")
        print(f"  Best Performer:      {df_results.iloc[0]['Symbol']:>7} ({df_results.iloc[0]['Return %']:.2f}%)")
        print(f"  Worst Performer:     {df_results.iloc[-1]['Symbol']:>7} ({df_results.iloc[-1]['Return %']:.2f}%)")

        return df_results
    else:
        print("No data available for analysis")
        return None


def show_cache_status(cache_mgr):
    """Show cache status and statistics."""
    print("\n" + "=" * 70)
    print("Cache Status")
    print("=" * 70)

    summary = cache_mgr.get_cache_summary()
    print(f"\nTotal Cached Symbols: {summary['total_symbols']}")
    print(f"Total Data Rows:     {summary['total_rows']:,}")
    print(f"Cache Size:          {summary['total_size_mb']:.2f} MB\n")

    if summary['symbols']:
        print("Cached Symbols:")
        # Print in columns
        cols = 10
        for i in range(0, len(summary['symbols']), cols):
            print("  " + "  ".join(f"{s:6s}" for s in summary['symbols'][i:i+cols]))

    # Export summary
    cache_mgr.export_summary()


def main():
    """Run example analysis."""
    fetcher = StockDataFetcher()
    cache_mgr = CacheManager()

    print("\n" + "=" * 70)
    print("Stock Market Database & Analysis Tool")
    print("=" * 70)

    # Check if we need to download data
    cached = cache_mgr.get_cached_symbols()

    if len(cached) == 0:
        print("\n📥 No cached data found. Downloading 100 stocks (1m interval, truncated to provider limits)...")
        download_stock_database(fetcher, cache_mgr, force_refresh=True, interval='1m')
    else:
        print(f"\n✓ Found {len(cached)} cached stocks. Using cached data.")
        print("  (Run 'download_stock_database(fetcher, cache_mgr, force_refresh=True)' to refresh)")

    # Show cache status
    show_cache_status(cache_mgr)

    # Analyze specific categories
    print("\n📊 Analyzing Stock Categories...")

    # Analyze mega-cap stocks
    mega_results = analyze_category(StockAnalyzer, cache_mgr, 'mega_cap')

    # Analyze tech stocks
    tech_results = analyze_category(StockAnalyzer, cache_mgr, 'large_tech')

    # Analyze finance sector
    finance_results = analyze_category(StockAnalyzer, cache_mgr, 'finance')

    # Top performers across all
    print("\n" + "=" * 70)
    print("Top 10 Performers (All Cached Stocks)")
    print("=" * 70 + "\n")

    all_results = analyze_category(StockAnalyzer, cache_mgr)

    if all_results is not None:
        print("\n" + all_results.head(10).to_string(index=False))

        # Bottom performers
        print("\nBottom 10 Performers:\n")
        print(all_results.tail(10).to_string(index=False))

    print("\n" + "=" * 70)
    print("Analysis Complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  - Modify the code to analyze different categories")
    print("  - Implement technical indicators for specific stocks")
    print("  - Create visualizations of stock performance")
    print("  - Set up alerts for stocks meeting criteria")


if __name__ == "__main__":
    main()

