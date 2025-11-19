"""
Module for analyzing stock market data.

Provides various analysis functions including technical indicators,
trend analysis, and performance metrics.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict


class StockAnalyzer:
    """Analyzes stock market data and generates insights."""

    def __init__(self, df: pd.DataFrame):
        """
        Initialize the analyzer with a DataFrame of stock data.

        Args:
            df: DataFrame with columns: Date, Open, High, Low, Close, Volume
        """
        self.df = df.copy()
        self.df = self.df.sort_values('Date').reset_index(drop=True)

    def calculate_moving_average(self, window: int = 20) -> pd.Series:
        """Calculate simple moving average."""
        return self.df['Close'].rolling(window=window).mean()

    def calculate_exponential_moving_average(self, window: int = 20) -> pd.Series:
        """Calculate exponential moving average."""
        return self.df['Close'].ewm(span=window, adjust=False).mean()

    def calculate_rsi(self, window: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).

        Returns values between 0 and 100.
        """
        delta = self.df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Returns:
            Tuple of (MACD line, Signal line)
        """
        ema_fast = self.df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = self.df['Close'].ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal, adjust=False).mean()
        return macd, signal

    def calculate_bollinger_bands(self, window: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.

        Returns:
            Tuple of (Upper band, Middle band, Lower band)
        """
        sma = self.df['Close'].rolling(window=window).mean()
        std = self.df['Close'].rolling(window=window).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        return upper, sma, lower

    def calculate_returns(self, period: int = 1) -> pd.Series:
        """Calculate percentage returns over specified period."""
        return self.df['Close'].pct_change(periods=period) * 100

    def calculate_volatility(self, window: int = 20) -> pd.Series:
        """Calculate rolling volatility (standard deviation of returns)."""
        returns = self.calculate_returns()
        return returns.rolling(window=window).std()

    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance metrics."""
        close_prices = self.df['Close']
        returns = self.calculate_returns()

        total_return = ((close_prices.iloc[-1] - close_prices.iloc[0]) / close_prices.iloc[0]) * 100
        annual_volatility = returns.std() * np.sqrt(252)  # Assuming 252 trading days
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0

        max_price = close_prices.max()
        min_price = close_prices.min()
        current_price = close_prices.iloc[-1]

        return {
            'total_return_pct': round(total_return, 2),
            'annual_volatility_pct': round(annual_volatility, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_price': round(max_price, 2),
            'min_price': round(min_price, 2),
            'current_price': round(current_price, 2),
            'start_date': self.df['Date'].min(),
            'end_date': self.df['Date'].max(),
            'trading_days': len(self.df),
            'avg_daily_return_pct': round(returns.mean(), 4),
        }

    def identify_trends(self, window: int = 50) -> Dict:
        """Identify current trend based on moving averages."""
        sma_short = self.df['Close'].rolling(window=20).mean()
        sma_long = self.df['Close'].rolling(window=window).mean()

        current_short = sma_short.iloc[-1]
        current_long = sma_long.iloc[-1]

        if current_short > current_long:
            trend = "Uptrend"
        elif current_short < current_long:
            trend = "Downtrend"
        else:
            trend = "Neutral"

        return {
            'trend': trend,
            'short_ma': round(current_short, 2),
            'long_ma': round(current_long, 2),
        }

    def find_support_resistance(self, window: int = 20, num_points: int = 5) -> Dict:
        """
        Find support and resistance levels.

        Args:
            window: Window size for finding local extrema
            num_points: Number of top support/resistance levels to return
        """
        highs = self.df['Close'].rolling(window=window).max()
        lows = self.df['Close'].rolling(window=window).min()

        resistance_levels = highs.value_counts().head(num_points).index.tolist()
        support_levels = lows.value_counts().head(num_points).index.tolist()

        return {
            'resistance_levels': [round(x, 2) for x in resistance_levels],
            'support_levels': [round(x, 2) for x in support_levels],
        }
