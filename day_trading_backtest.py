"""
Day Trading Algorithm
Uses 10 years of daily data to develop patterns, then backtests against 
the last 7 days of 1-minute intraday data to simulate real day trades.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from cache_manager import CacheManager
from stock_list import get_all_stocks
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os


class DayTradingAlgorithm:
    """
    Day Trading Algorithm
    
    Strategy:
    1. Use 10 years daily data to identify stocks with volatility patterns
    2. Find stocks in uptrends with predictable intraday swings
    3. Trade the 1-minute data: buy dips, sell rips within the day
    4. Multiple entry/exit points per day for high-probability trades
    """

    ALGORITHM_FILE = 'trained_algorithm.json'

    def __init__(self, cache_mgr):
        self.cache_mgr = cache_mgr

    def analyze_daily_patterns(self, df_daily):
        """
        Analyze 10 years of daily data to find trading patterns.
        Returns metrics that predict good intraday trading opportunities.
        """
        if df_daily is None or len(df_daily) < 100:
            return None

        try:
            df = df_daily.sort_values('Date').copy()
            
            # Daily returns and volatility
            df['Daily_Return'] = df['Close'].pct_change()
            df['Volatility'] = df['Daily_Return'].rolling(window=20).std() * np.sqrt(252)
            
            # Trend indicators
            df['SMA50'] = df['Close'].rolling(window=50).mean()
            df['SMA200'] = df['Close'].rolling(window=200).mean()
            
            # Recent performance
            recent_20_return = (df.iloc[-1]['Close'] / df.iloc[-20]['Close'] - 1) * 100
            annual_volatility = df['Volatility'].iloc[-1]
            in_uptrend = df.iloc[-1]['SMA50'] > df.iloc[-1]['SMA200']
            
            # Average daily move (intraday trading range)
            df['High_Low_Pct'] = ((df['High'] - df['Low']) / df['Low']) * 100 if 'High' in df.columns else 0
            avg_daily_range = df['High_Low_Pct'].tail(60).mean()
            
            # Win rate based on close above open
            if 'Open' in df.columns:
                win_rate = (df['Close'] > df['Open']).tail(60).sum() / 60 * 100
            else:
                win_rate = 50.0
            
            return {
                'recent_trend_20d': recent_20_return,
                'annual_volatility': annual_volatility,
                'in_uptrend': in_uptrend,
                'avg_daily_range_pct': avg_daily_range,
                'win_rate': win_rate,
                'current_price': df.iloc[-1]['Close'],
            }
        except Exception as e:
            print(f"Error analyzing daily patterns: {e}")
            return None

    def save_algorithm(self, algorithm_dict):
        """Save trained algorithm (daily patterns) to JSON file."""
        # Convert non-JSON-serializable types
        safe_dict = {}
        for symbol, patterns in algorithm_dict.items():
            safe_dict[symbol] = {
                'recent_trend_20d': float(patterns['recent_trend_20d']),
                'annual_volatility': float(patterns['annual_volatility']),
                'in_uptrend': bool(patterns['in_uptrend']),
                'avg_daily_range_pct': float(patterns['avg_daily_range_pct']),
                'win_rate': float(patterns['win_rate']),
                'current_price': float(patterns['current_price']),
            }
        
        with open(self.ALGORITHM_FILE, 'w') as f:
            json.dump(safe_dict, f, indent=2)
        print(f"✓ Algorithm saved to {self.ALGORITHM_FILE} ({len(algorithm_dict)} symbols)")

    def load_algorithm(self):
        """Load trained algorithm from JSON file. Returns dict or None if file doesn't exist."""
        if not os.path.exists(self.ALGORITHM_FILE):
            return None
        
        try:
            with open(self.ALGORITHM_FILE, 'r') as f:
                algo_dict = json.load(f)
            print(f"✓ Algorithm loaded from {self.ALGORITHM_FILE} ({len(algo_dict)} symbols)")
            return algo_dict
        except Exception as e:
            print(f"Error loading algorithm: {e}")
            return None

    def backtest_intraday_trades(self, df_1m, daily_patterns):
        """
        Backtest intraday trades on 1-minute data using signals derived
        from daily patterns.
        
        Returns: list of trades with entry, exit, and P&L
        """
        if df_1m is None or len(df_1m) < 100:
            return None, None

        if daily_patterns is None:
            return None, None

        try:
            df = df_1m.sort_values('Date').copy()
            
            # Only proceed if we have daily volatility
            if daily_patterns['annual_volatility'] < 0.1:
                return None, None  # Too stable for day trading
            
            # Calculate 1-minute indicators
            df['SMA5'] = df['Close'].rolling(window=5).mean()
            df['SMA20'] = df['Close'].rolling(window=20).mean()
            
            # RSI on 1-minute
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Volatility bands (adaptive)
            df['Volatility_1m'] = df['Close'].rolling(window=20).std()
            
            trades = []
            in_trade = False
            entry_price = 0
            entry_idx = 0
            
            for i in range(20, len(df) - 5):
                current = df.iloc[i]
                prev = df.iloc[i - 1]
                
                # Entry conditions: Buy dips in uptrend
                if not in_trade and daily_patterns['in_uptrend']:
                    # Signal: Price pulls back (below SMA5) with oversold RSI
                    if current['Close'] < current['SMA5'] and current['RSI'] < 35:
                        entry_price = current['Close']
                        entry_idx = i
                        in_trade = True
                        continue
                
                # Exit conditions
                if in_trade:
                    # Profit target: 0.5-1.5% gain
                    profit_pct = ((current['Close'] - entry_price) / entry_price) * 100
                    
                    # Take profit
                    if profit_pct >= 0.8:
                        trades.append({
                            'entry_time': df.iloc[entry_idx]['Date'],
                            'entry_price': entry_price,
                            'exit_time': current['Date'],
                            'exit_price': current['Close'],
                            'profit_pct': profit_pct,
                            'hold_minutes': i - entry_idx,
                            'exit_reason': 'Profit Target',
                        })
                        in_trade = False
                    
                    # Stop loss: -0.5% loss
                    elif profit_pct <= -0.5:
                        trades.append({
                            'entry_time': df.iloc[entry_idx]['Date'],
                            'entry_price': entry_price,
                            'exit_time': current['Date'],
                            'exit_price': current['Close'],
                            'profit_pct': profit_pct,
                            'hold_minutes': i - entry_idx,
                            'exit_reason': 'Stop Loss',
                        })
                        in_trade = False
                    
                    # Time-based exit: close at 4% daily move or 60 minutes
                    elif (i - entry_idx) > 60 or abs(profit_pct) > 2.0:
                        trades.append({
                            'entry_time': df.iloc[entry_idx]['Date'],
                            'entry_price': entry_price,
                            'exit_time': current['Date'],
                            'exit_price': current['Close'],
                            'profit_pct': profit_pct,
                            'hold_minutes': i - entry_idx,
                            'exit_reason': 'Time Exit' if (i - entry_idx) > 60 else 'Large Move',
                        })
                        in_trade = False
            
            if trades:
                df_trades = pd.DataFrame(trades)
                win_count = (df_trades['profit_pct'] > 0).sum()
                total_pnl = df_trades['profit_pct'].sum()
                win_rate = (win_count / len(df_trades)) * 100
                avg_win = df_trades[df_trades['profit_pct'] > 0]['profit_pct'].mean() if win_count > 0 else 0
                avg_loss = df_trades[df_trades['profit_pct'] <= 0]['profit_pct'].mean() if (len(df_trades) - win_count) > 0 else 0
                
                stats = {
                    'total_trades': len(df_trades),
                    'winning_trades': win_count,
                    'losing_trades': len(df_trades) - win_count,
                    'win_rate': win_rate,
                    'total_pnl_pct': total_pnl,
                    'avg_win': avg_win,
                    'avg_loss': avg_loss,
                    'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
                }
                
                return df_trades, stats
            else:
                return None, None
        
        except Exception as e:
            print(f"Error in backtest: {e}")
            return None, None


def main():
    cache_mgr = CacheManager()
    algo = DayTradingAlgorithm(cache_mgr)
    
    symbols = get_all_stocks()
    
    print("=" * 90)
    print("DAY TRADING ALGORITHM BACKTEST")
    print("Train: 10 years daily data | Test: Last 7 days 1-minute data")
    print("=" * 90)
    
    # Check if algorithm is already trained and available
    loaded_algo = algo.load_algorithm()
    
    if loaded_algo is not None:
        print("\nUsingexisting trained algorithm from file.")
        use_loaded = input("Press ENTER to use existing algorithm, or type 'retrain' to retrain: ").strip().lower()
        if use_loaded != 'retrain':
            algorithm_dict = loaded_algo
            skip_training = True
        else:
            algorithm_dict = {}
            skip_training = False
    else:
        print("\nNo existing algorithm found. Training from daily data...")
        algorithm_dict = {}
        skip_training = False
    
    # Training phase (if not skipped)
    if not skip_training:
        for symbol in symbols:
            # Load daily data
            df_daily = cache_mgr.get_cached_symbol(symbol)
            if df_daily is None or len(df_daily) < 100:
                continue
            
            # Filter daily to only daily (some may have 1m in the same symbol)
            df_daily = df_daily[df_daily['Date'].dt.hour == 0] if 'hour' in df_daily['Date'].dt.__dir__() else df_daily
            if len(df_daily) < 100:
                continue
            
            # Analyze 10 years of daily patterns
            daily_patterns = algo.analyze_daily_patterns(df_daily)
            if daily_patterns is not None:
                algorithm_dict[symbol] = daily_patterns
        
        # Save trained algorithm
        if algorithm_dict:
            algo.save_algorithm(algorithm_dict)
        else:
            print("No valid symbols found for training.")
            return
    
    # Backtesting phase
    print("\nRunning backtest with trained algorithm...")
    results = []
    
    for symbol in algorithm_dict.keys():
        daily_patterns = algorithm_dict[symbol]
        
        # Load 1-minute intraday data from parquet file
        try:
            parquet_1m = os.path.join(cache_mgr.cache_dir, f"{symbol}_1m.parquet")
            if os.path.exists(parquet_1m):
                df_1m = pd.read_parquet(parquet_1m)
                if 'Date' in df_1m.columns:
                    df_1m['Date'] = pd.to_datetime(df_1m['Date'])
            else:
                continue
        except:
            continue
        
        if len(df_1m) < 100:
            continue
        
        # Backtest
        trades_df, stats = algo.backtest_intraday_trades(df_1m, daily_patterns)
        
        if stats is None or stats['total_trades'] < 3:
            continue
        
        results.append({
            'symbol': symbol,
            'daily_patterns': daily_patterns,
            'stats': stats,
            'trades': trades_df,
        })
    
    # Sort by total PnL
    results.sort(key=lambda x: x['stats']['total_pnl_pct'], reverse=True)
    
    # Display results
    print("\nTOP 15 PROFITABLE DAY TRADING OPPORTUNITIES")
    print("-" * 90)
    print(f"{'Symbol':>8} {'Trades':>8} {'Win%':>8} {'PnL%':>10} {'AvgWin%':>10} {'AvgLoss%':>10} {'PF':>8}")
    print("-" * 90)
    
    for i, r in enumerate(results[:15]):
        s = r['stats']
        print(
            f"{r['symbol']:>8} {s['total_trades']:>8.0f} {s['win_rate']:>8.1f}% "
            f"{s['total_pnl_pct']:>10.2f}% {s['avg_win']:>10.2f}% "
            f"{s['avg_loss']:>10.2f}% {s['profit_factor']:>8.2f}"
        )
    
    # Detailed analysis of top symbol
    if results:
        print("\n" + "=" * 90)
        print("DETAILED ANALYSIS: TOP PERFORMER")
        print("=" * 90)
        
        top = results[0]
        symbol = top['symbol']
        patterns = top['daily_patterns']
        stats = top['stats']
        trades = top['trades']
        
        print(f"\nSymbol: {symbol}")
        print(f"Daily Patterns (10-year analysis):")
        print(f"  - 20-day trend: {patterns['recent_trend_20d']:>6.2f}%")
        print(f"  - Annual volatility: {patterns['annual_volatility']*100:>6.2f}%")
        print(f"  - In uptrend: {patterns['in_uptrend']}")
        print(f"  - Avg daily range: {patterns['avg_daily_range_pct']:>6.2f}%")
        print(f"  - Historical win rate (close > open): {patterns['win_rate']:>6.2f}%")
        
        print(f"\nBacktest Results (Last 7 days, 1-minute data):")
        print(f"  - Total trades: {stats['total_trades']}")
        print(f"  - Winning trades: {stats['winning_trades']} ({stats['win_rate']:.1f}%)")
        print(f"  - Losing trades: {stats['losing_trades']}")
        print(f"  - Total P&L: {stats['total_pnl_pct']:+.2f}%")
        print(f"  - Avg win: {stats['avg_win']:+.2f}%")
        print(f"  - Avg loss: {stats['avg_loss']:+.2f}%")
        print(f"  - Profit Factor: {stats['profit_factor']:.2f} (>1.5 is good)")
        
        print(f"\nSample Trades:")
        print(f"{'Entry Time':>20} {'Entry':>10} {'Exit':>10} {'P&L%':>10} {'Duration':>12}")
        print("-" * 65)
        for idx, trade in enumerate(trades.head(10).itertuples()):
            entry_time = str(trade[1])[-8:] if trade[1] is not None else "N/A"
            entry_price = trade[2]
            exit_price = trade[4]
            pnl = trade[5]
            duration = int(trade[6])
            print(
                f"{entry_time:>20} ${entry_price:>9.2f} ${exit_price:>9.2f} "
                f"{pnl:>9.2f}% {duration:>8}m"
            )
    
    print("\n" + "=" * 90)
    print("ALGORITHM EXPLANATION")
    print("=" * 90)
    print("""
**Daily Pattern Analysis (Training Phase):**
- Analyzes 10 years of historical daily data
- Identifies stocks with strong trends (SMA 50 > SMA 200)
- Measures volatility and historical win rates
- Selects stocks suitable for intraday trading

**Intraday Trading Rules (1-Minute Data):**
1. Entry: Buy when price dips below 5-min SMA with RSI < 35 (oversold)
   - Only trade stocks in established uptrends
   - Avoids picking bottoms in downtrends

2. Profit Target: Exit at +0.8% gain (quick scalp)
   - Average hold time: 5-60 minutes
   - Limits risk exposure during the day

3. Stop Loss: Exit at -0.5% loss
   - Protects capital from unexpected reversals

4. Time Exit: Close position after 60 minutes
   - Avoids extended overnight holds

**Key Metrics:**
- Win Rate: % of profitable trades (target: >55%)
- Profit Factor: Avg Win / Avg Loss (target: >1.5)
- Total P&L: Sum of all trade percentages
- Best for: Liquid stocks with volatility patterns

**Risk Management:**
- Max 2% of account per trade
- Daily loss limit: Stop if -3% cumulative loss
- Never hold overnight
- Trade only during peak hours (9:30-16:00)
""")
    
    print("\n" + "=" * 90)
    print("DISCLAIMER:")
    print("Past performance does not guarantee future results.")
    print("Day trading involves high risk. Use proper position sizing and stop losses.")
    print("=" * 90)


if __name__ == '__main__':
    main()
