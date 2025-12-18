"""
Technical Indicators - 16 Indicators (12 Basic + 4 Advanced)
Complete indicator suite for scalping strategy
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple
from scipy import stats


class TechnicalIndicators:
    """
    Calculate all technical indicators for trading signals
    16 indicators total: 12 basic + 4 advanced
    """
    
    @staticmethod
    def calculate_all(df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate all indicators at once
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with all indicator values
        """
        indicators = {}
        
        # Basic Momentum Indicators
        indicators['rsi'] = TechnicalIndicators.rsi(df['close'])
        macd, signal, histogram = TechnicalIndicators.macd(df['close'])
        indicators['macd'] = macd
        indicators['macd_signal'] = signal
        indicators['macd_histogram'] = histogram
        
        stoch_k, stoch_d = TechnicalIndicators.stochastic(df['high'], df['low'], df['close'])
        indicators['stoch_k'] = stoch_k
        indicators['stoch_d'] = stoch_d
        
        # Trend Indicators
        indicators['ema_9'] = TechnicalIndicators.ema(df['close'], 9)
        indicators['ema_20'] = TechnicalIndicators.ema(df['close'], 20)
        indicators['ema_50'] = TechnicalIndicators.ema(df['close'], 50)
        indicators['ema_200'] = TechnicalIndicators.ema(df['close'], 200)
        indicators['sma_20'] = TechnicalIndicators.sma(df['close'], 20)
        
        # Volatility Indicators
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(df['close'])
        indicators['bb_upper'] = bb_upper
        indicators['bb_middle'] = bb_middle
        indicators['bb_lower'] = bb_lower
        indicators['bb_width'] = (bb_upper - bb_lower) / bb_middle if bb_middle != 0 else 0
        indicators['atr'] = TechnicalIndicators.atr(df['high'], df['low'], df['close'])
        
        # Strength Indicators
        indicators['adx'] = TechnicalIndicators.adx(df['high'], df['low'], df['close'])
        indicators['cci'] = TechnicalIndicators.cci(df['high'], df['low'], df['close'])
        indicators['mfi'] = TechnicalIndicators.mfi(df['high'], df['low'], df['close'], df['volume'])
        
        # Volume Indicators
        indicators['obv'] = TechnicalIndicators.obv(df['close'], df['volume'])
        indicators['vwap'] = TechnicalIndicators.vwap(df['high'], df['low'], df['close'], df['volume'])
        
        # Advanced Indicators (Our Secret Sauce)
        indicators['mc_probability'], indicators['mc_expected_price'] = TechnicalIndicators.monte_carlo_simulation(df['close'])
        indicators['gk_volatility'] = TechnicalIndicators.garman_klass_volatility(df['high'], df['low'], df['open'], df['close'])
        indicators['z_score'] = TechnicalIndicators.z_score(df['close'])
        indicators['lr_slope'] = TechnicalIndicators.linear_regression_slope(df['close'])
        
        return indicators
    
    # ========================================================================
    # BASIC INDICATORS (12)
    # ========================================================================
    
    @staticmethod
    def rsi(close: pd.Series, period: int = 14) -> float:
        """Relative Strength Index"""
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 50.0
    
    @staticmethod
    def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Moving Average Convergence Divergence"""
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return (
            macd_line.iloc[-1] if not macd_line.empty else 0.0,
            signal_line.iloc[-1] if not signal_line.empty else 0.0,
            histogram.iloc[-1] if not histogram.empty else 0.0
        )
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[float, float]:
        """Stochastic Oscillator"""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        
        stoch_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        stoch_d = stoch_k.rolling(window=3).mean()
        
        return (
            stoch_k.iloc[-1] if not stoch_k.empty else 50.0,
            stoch_d.iloc[-1] if not stoch_d.empty else 50.0
        )
    
    @staticmethod
    def ema(close: pd.Series, period: int) -> float:
        """Exponential Moving Average"""
        ema = close.ewm(span=period, adjust=False).mean()
        return ema.iloc[-1] if not ema.empty else close.iloc[-1]
    
    @staticmethod
    def sma(close: pd.Series, period: int) -> float:
        """Simple Moving Average"""
        sma = close.rolling(window=period).mean()
        return sma.iloc[-1] if not sma.empty else close.iloc[-1]
    
    @staticmethod
    def bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
        """Bollinger Bands"""
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return (
            upper.iloc[-1] if not upper.empty else close.iloc[-1],
            sma.iloc[-1] if not sma.empty else close.iloc[-1],
            lower.iloc[-1] if not lower.empty else close.iloc[-1]
        )
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """Average True Range"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr.iloc[-1] if not atr.empty else 0.0
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """Average Directional Index"""
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = pd.concat([high - low, np.abs(high - close.shift()), np.abs(low - close.shift())], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx.iloc[-1] if not adx.empty else 0.0
    
    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> float:
        """Commodity Channel Index"""
        typical_price = (high + low + close) / 3
        sma = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        
        cci = (typical_price - sma) / (0.015 * mean_deviation)
        return cci.iloc[-1] if not cci.empty else 0.0
    
    @staticmethod
    def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> float:
        """Money Flow Index"""
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume
        
        positive_flow = money_flow.where(typical_price > typical_price.shift(), 0).rolling(window=period).sum()
        negative_flow = money_flow.where(typical_price < typical_price.shift(), 0).rolling(window=period).sum()
        
        mfi = 100 - (100 / (1 + positive_flow / negative_flow))
        return mfi.iloc[-1] if not mfi.empty else 50.0
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> float:
        """On-Balance Volume"""
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv.iloc[-1] if not obv.empty else 0.0
    
    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> float:
        """Volume Weighted Average Price"""
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap.iloc[-1] if not vwap.empty else close.iloc[-1]
    
    # ========================================================================
    # ADVANCED INDICATORS (4) - Our Secret Sauce
    # ========================================================================
    
    @staticmethod
    def monte_carlo_simulation(
        close: pd.Series,
        simulations: int = 1000,
        horizon: int = 12
    ) -> Tuple[float, float]:
        """
        Monte Carlo Simulation for probability-based trading
        
        Returns:
            (probability_up, expected_price)
        """
        returns = close.pct_change().dropna()
        
        if len(returns) < 2:
            return 0.5, close.iloc[-1]
        
        # Calculate drift and volatility
        drift = returns.mean()
        volatility = returns.std()
        
        last_price = close.iloc[-1]
        
        # Run simulations
        final_prices = []
        for _ in range(simulations):
            price = last_price
            for _ in range(horizon):
                shock = np.random.normal(drift, volatility)
                price *= (1 + shock)
            final_prices.append(price)
        
        # Calculate probability and expected price
        probability_up = sum(1 for p in final_prices if p > last_price) / simulations
        expected_price = np.mean(final_prices)
        
        return probability_up, expected_price
    
    @staticmethod
    def garman_klass_volatility(
        high: pd.Series,
        low: pd.Series,
        open_price: pd.Series,
        close: pd.Series,
        window: int = 20
    ) -> float:
        """
        Garman-Klass Volatility (7.4x more efficient than standard)
        Uses OHLC data for better volatility estimation
        """
        log_hl = (np.log(high) - np.log(low)) ** 2
        log_co = (np.log(close) - np.log(open_price)) ** 2
        
        gk = 0.5 * log_hl - (2 * np.log(2) - 1) * log_co
        gk_vol = np.sqrt(gk.rolling(window=window).mean() * 252)  # Annualized
        
        return gk_vol.iloc[-1] if not gk_vol.empty else 0.0
    
    @staticmethod
    def z_score(close: pd.Series, window: int = 20) -> float:
        """
        Z-Score for mean reversion signals
        Perfect for scalping in ranging markets
        """
        sma = close.rolling(window=window).mean()
        std = close.rolling(window=window).std()
        
        z = (close - sma) / std
        return z.iloc[-1] if not z.empty else 0.0
    
    @staticmethod
    def linear_regression_slope(close: pd.Series, window: int = 10) -> float:
        """
        Linear Regression Slope for micro-trend detection
        Catches early momentum shifts
        """
        if len(close) < window:
            return 0.0
        
        recent_prices = close.iloc[-window:].values
        x = np.arange(len(recent_prices))
        
        slope, _, _, _, _ = stats.linregress(x, recent_prices)
        
        # Normalize slope
        normalized_slope = slope / close.iloc[-1] if close.iloc[-1] != 0 else 0.0
        
        return normalized_slope


# Export
__all__ = ['TechnicalIndicators']
