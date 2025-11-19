"""
Configuration for day trading algorithm
Adjust these parameters to tune trading behavior
"""

# ===== ENTRY SIGNALS =====
RSI_OVERSOLD_THRESHOLD = 35  # RSI below this triggers buy signal
SMA_PERIOD = 5               # Short-term moving average period for entry

# ===== EXIT RULES =====
PROFIT_TARGET_PCT = 0.8      # Sell when profit reaches this % (e.g., 0.8%)
STOP_LOSS_PCT = 0.5          # Sell when loss reaches this % (e.g., -0.5%)
MAX_HOLD_TIME_MINUTES = 480   # Close position after this many minutes
LARGE_MOVE_EXIT_PCT = 2.0    # Exit if price moves beyond this % (volatile move)

# ===== TRADING HOURS =====
TRADING_START_HOUR = 9       # Start trading at 9:30 AM (in 24-hour format)
TRADING_START_MINUTE = 30
TRADING_END_HOUR = 16        # Stop trading at 4:00 PM
TRADING_END_MINUTE = 0

# ===== COSTS & SLIPPAGE =====
COMMISSION_PER_TRADE = 0  # 0.1% commission per trade (entry + exit)
                               # E.g., $0.01 per share on a $10 stock = 0.1%
COMMISSION_FLAT_RATE = 0    # Flat rate per trade in dollars (e.g., $1 per trade)
                               # Set to 0 to use percentage-only commission
SLIPPAGE_PCT = 0.01           # Slippage as % of entry price
                               # E.g., 0.01% means you expect 1 cent slippage on $100 stock

# ===== POSITION SIZING =====
ACCOUNT_SIZE = 10000.0        # Starting account size (for position sizing)
RISK_PER_TRADE_PCT = 0.02     # Risk 2% of account per trade
MAX_DAILY_LOSS_PCT = 0.03     # Stop trading if cumulative daily loss hits 3%

# ===== TRADE FILTERS =====
MIN_VOLATILITY = 0.10         # Skip stocks with < 10% annual volatility (too stable)
REQUIRE_UPTREND = True        # Only trade stocks in uptrend (SMA50 > SMA200)
MIN_TRADES_TO_REPORT = 3      # Only report symbols with at least 3 trades
