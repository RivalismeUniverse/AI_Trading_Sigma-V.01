"""
Technical Indicators Calculator
Includes 12 basic + 4 advanced indicators for AI Trading SIGMA
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
import ta  # Technical Analysis library


class TechnicalIndicators:
    """
    Calculate technical indicators for trading signals
    Includes Monte Carlo simulation and advanced volatility
    """
    
    def __init__(self):
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.bb_period = 20
        self.bb_std = 2.0
        
    def calculate_all(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate all basic technical indicators
        Returns dictionary with indicator values
        """
        try:
            close = df['close']
            high = df['high']
            low = df['low']
            volume = df['volume']
            
            indicators = {}
            
            # 1. RSI (Relative Strength Index)
            indicators['rsi'] = self._calculate_rsi(close)
            
            # 2. MACD (Moving Average Convergence Divergence)
            macd, signal, histogram = self._calculate_macd(close)
            indicators['macd'] = macd
            indicators['macd_signal'] = signal
            indicators['macd_histogram'] = histogram
            
            # 3. Moving Averages
            indicators['ema_9'] = self._calculate_ema(close, 9)
            indicators['ema_20'] = self._calculate_ema(close, 20)
            indicators['ema_50'] = self._calculate_ema(close, 50)
            indicators['sma_20'] = self._calculate_sma(close, 20)
            indicators['sma_50'] = self._calculate_sma(close, 50)
            
            # 4. Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close)
            indicators['bb_upper'] = bb_upper
            indicators['bb_middle'] = bb_middle
            indicators['bb_lower'] = bb_lower
            indicators['bb_width'] = (bb_upper - bb_lower) / bb_middle if bb_middle != 0 else 0
            indicators['bb_position'] = (close.iloc[-1] - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
            
            # 5. ATR (Average True Range)
            indicators['atr'] = self._calculate_atr(high, low, close)
            
            # 6. ADX (Average Directional Index)
            indicators['adx'] = self._calculate_adx(high, low, close)
            
            # 7. Stochastic Oscillator
            stoch_k, stoch_d = self._calculate_stochastic(high, low, close)
            indicators['stoch_k'] = stoch_k
            indicators['stoch_d'] = stoch_d
            
            # 8. CCI (Commodity Channel Index)
            indicators['cci'] = self._calculate_cci(high, low, close)
            
            # 9. MFI (Money Flow Index)
            indicators['mfi'] = self._calculate_mfi(high, low, close, volume)
            
            # 10. OBV (On-Balance Volume)
            indicators['obv'] = self._calculate_obv(close, volume)
            
            # 11. VWAP (Volume Weighted Average Price)
            indicators['vwap'] = self._calculate_vwap(high, low, close, volume)
            
            # 12. Volume indicators
            indicators['volume_sma'] = volume.rolling(20).mean().iloc[-1]
            indicators['volume_ratio'] = volume.iloc[-1] / indicators['volume_sma'] if indicators['volume_sma'] != 0 else 1
            
            return indicators
            
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return {}
    
    def _calculate_rsi(self, close: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 50
    
    def _calculate_macd(self, close: pd.Series) -> Tuple[float, float, float]:
        """Calculate MACD"""
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        return macd.iloc[-1], signal.iloc[-1], histogram.iloc[-1]
    
    def _calculate_ema(self, close: pd.Series, period: int) -> float:
        """Calculate Exponential Moving Average"""
        return close.ewm(span=period, adjust=False).mean().iloc[-1]
    
    def _calculate_sma(self, close: pd.Series, period: int) -> float:
        """Calculate Simple Moving Average"""
        return close.rolling(window=period).mean().iloc[-1]
    
    def _calculate_bollinger_bands(self, close: pd.Series, period: int = 20, std: float = 2.0) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands"""
        sma = close.rolling(window=period).mean()
        std_dev = close.rolling(window=period).std()
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        return upper.iloc[-1], sma.iloc[-1], lower.iloc[-1]
    
    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr.iloc[-1] if not atr.empty else 0
    
    def _calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """Calculate Average Directional Index"""
        try:
            # Using ta library for ADX calculation
            from ta.trend import ADXIndicator
            adx_i = ADXIndicator(high=high, low=low, close=close, window=period)
            return adx_i.adx().iloc[-1]
        except:
            return 25  # Default neutral value
    
    def _calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[float, float]:
        """Calculate Stochastic Oscillator"""
        try:
            from ta.momentum import StochasticOscillator
            stoch = StochasticOscillator(high=high, low=low, close=close, window=period)
            return stoch.stoch().iloc[-1], stoch.stoch_signal().iloc[-1]
        except:
            return 50, 50  # Default neutral values
    
    def _calculate_cci(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> float:
        """Calculate Commodity Channel Index"""
        try:
            from ta.trend import CCIIndicator
            cci = CCIIndicator(high=high, low=low, close=close, window=period)
            return cci.cci().iloc[-1]
        except:
            return 0  # Default neutral value
    
    def _calculate_mfi(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> float:
        """Calculate Money Flow Index"""
        try:
            from ta.volume import MFIIndicator
            mfi = MFIIndicator(high=high, low=low, close=close, volume=volume, window=period)
            return mfi.money_flow_index().iloc[-1]
        except:
            return 50  # Default neutral value
    
    def _calculate_obv(self, close: pd.Series, volume: pd.Series) -> float:
        """Calculate On-Balance Volume"""
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv.iloc[-1] if not obv.empty else 0
    
    def _calculate_vwap(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> float:
        """Calculate Volume Weighted Average Price"""
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap.iloc[-1] if not vwap.empty else close.iloc[-1]
    
    # ========== ADVANCED INDICATORS ==========
    
    def monte_carlo_simulation(self, prices: np.ndarray, n_simulations: int = 1000, n_periods: int = 20) -> Dict[str, Any]:
        """
        Monte Carlo simulation for price prediction
        Returns probability of price movement
        """
        try:
            if len(prices) < 30:
                return {"probability_up": 0.5, "expected_price": prices[-1], "confidence_bands": {}}
            
            # Calculate returns and statistics
            returns = np.diff(prices) / prices[:-1]
            
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            last_price = prices[-1]
            simulated_prices = []
            
            # Run simulations
            for _ in range(n_simulations):
                price_path = [last_price]
                for _ in range(n_periods):
                    random_return = np.random.normal(mean_return, std_return)
                    next_price = price_path[-1] * (1 + random_return)
                    price_path.append(next_price)
                simulated_prices.append(price_path[-1])
            
            simulated_prices = np.array(simulated_prices)
            
            # Calculate statistics
            probability_up = np.sum(simulated_prices > last_price) / n_simulations
            expected_price = np.mean(simulated_prices)
            
            # Confidence bands
            confidence_bands = {
                "70": {
                    "lower": np.percentile(simulated_prices, 15),
                    "upper": np.percentile(simulated_prices, 85)
                },
                "90": {
                    "lower": np.percentile(simulated_prices, 5),
                    "upper": np.percentile(simulated_prices, 95)
                },
                "95": {
                    "lower": np.percentile(simulated_prices, 2.5),
                    "upper": np.percentile(simulated_prices, 97.5)
                }
            }
            
            return {
                "probability_up": float(probability_up),
                "expected_price": float(expected_price),
                "confidence_bands": confidence_bands
            }
            
        except Exception as e:
            print(f"Monte Carlo simulation error: {e}")
            return {"probability_up": 0.5, "expected_price": prices[-1] if len(prices) > 0 else 0, "confidence_bands": {}}
    
    def garman_klass_volatility(self, df: pd.DataFrame) -> float:
        """
        Garman-Klass volatility estimator
        7.4x more efficient than close-to-close volatility
        """
        try:
            log_hl = np.log(df['high'] / df['low']) ** 2
            log_co = np.log(df['close'] / df['open']) ** 2
            
            # Garman-Klass formula
            variance = 0.5 * log_hl.mean() - (2 * np.log(2) - 1) * log_co.mean()
            
            # Annualize (assuming daily data)
            volatility = np.sqrt(variance * 365)
            
            return float(volatility)
            
        except Exception as e:
            print(f"Garman-Klass volatility error: {e}")
            return 0.0
    
    def z_score_mean_reversion(self, df: pd.DataFrame, lookback: int = 20) -> float:
        """
        Z-score for mean reversion detection
        Perfect for scalping in range-bound markets
        """
        try:
            close = df['close']
            
            if len(close) < lookback:
                return 0.0
            
            # Calculate rolling mean and std
            rolling_mean = close.rolling(window=lookback).mean()
            rolling_std = close.rolling(window=lookback).std()
            
            # Avoid division by zero
            rolling_std = rolling_std.replace(0, np.nan)
            
            # Calculate z-score
            z_score = (close.iloc[-1] - rolling_mean.iloc[-1]) / rolling_std.iloc[-1]
            
            return float(z_score) if not np.isnan(z_score) else 0.0
            
        except Exception as e:
            print(f"Z-score calculation error: {e}")
            return 0.0
    
    def linear_regression_slope(self, df: pd.DataFrame, lookback: int = 10) -> float:
        """
        Linear regression slope for micro-trend detection
        Positive slope = upward micro-trend
        """
        try:
            close = df['close'].tail(lookback).values
            
            if len(close) < lookback:
                return 0.0
            
            # Create time index
            x = np.arange(len(close))
            
            # Linear regression
            slope, intercept = np.polyfit(x, close, 1)
            
            # Normalize by price for consistency
            normalized_slope = slope / np.mean(close)
            
            return float(normalized_slope)
            
        except Exception as e:
            print(f"Linear regression slope error: {e}")
            return 0.0
