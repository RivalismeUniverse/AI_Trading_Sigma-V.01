"""
Technical Indicators - 16 Indicators (12 Basic + 4 Advanced)
Complete indicator suite for AI Trading Sigma-V.01
Optimized for stability with WEEX Bypass
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
        Calculate all indicators at once with safety fallback
        """
        # 1. DATA SANITIZER: Pastikan kolom huruf kecil (close, high, low, open, volume)
        df.columns = [x.lower() for x in df.columns]
        
        # Ambil harga terakhir untuk default value
        last_price = df['close'].iloc[-1] if not df.empty else 0.0
        
        # 2. DEFAULT VALUES: Mencegah KeyError ('rsi', 'current_price', dll)
        # Jika data belum cukup, bot akan menggunakan nilai netral ini
        indicators = {
            'current_price': last_price,
            'rsi': 50.0,
            'macd': 0.0, 'macd_signal': 0.0, 'macd_histogram': 0.0,
            'stoch_k': 50.0, 'stoch_d': 50.0,
            'ema_9': last_price, 'ema_20': last_price, 
            'ema_50': last_price, 'ema_200': last_price, 
            'sma_20': last_price,
            'bb_upper': last_price, 'bb_middle': last_price, 'bb_lower': last_price, 
            'bb_width': 0.0,
            'atr': 0.0, 'adx': 20.0, 'cci': 0.0, 'mfi': 50.0,
            'obv': 0.0, 'vwap': last_price,
            'mc_probability': 0.5, 'mc_expected_price': last_price,
            'gk_volatility': 0.0, 'z_score': 0.0, 'lr_slope': 0.0
        }

        # 3. VALIDATION: Minimal butuh beberapa baris data untuk mulai hitung
        if len(df) < 5:
            return indicators

        try:
            # 4. CALCULATE: Mulai menimpa nilai default dengan hasil asli
            # Momentum
            indicators['rsi'] = TechnicalIndicators.rsi(df['close'])
            macd, signal, histogram = TechnicalIndicators.macd(df['close'])
            indicators.update({'macd': macd, 'macd_signal': signal, 'macd_histogram': histogram})
            
            sk, sd = TechnicalIndicators.stochastic(df['high'], df['low'], df['close'])
            indicators.update({'stoch_k': sk, 'stoch_d': sd})
            
            # Trend
            indicators['ema_9'] = TechnicalIndicators.ema(df['close'], 9)
            indicators['ema_20'] = TechnicalIndicators.ema(df['close'], 20)
            indicators['ema_50'] = TechnicalIndicators.ema(df['close'], 50)
            indicators['ema_200'] = TechnicalIndicators.ema(df['close'], 200)
            indicators['sma_20'] = TechnicalIndicators.sma(df['close'], 20)
            
            # Volatility
            bbu, bbm, bbl = TechnicalIndicators.bollinger_bands(df['close'])
            indicators.update({'bb_upper': bbu, 'bb_middle': bbm, 'bb_lower': bbl})
            indicators['bb_width'] = (bbu - bbl) / bbm if bbm != 0 else 0
            indicators['atr'] = TechnicalIndicators.atr(df['high'], df['low'], df['close'])
            
            # Strength
            indicators['adx'] = TechnicalIndicators.adx(df['high'], df['low'], df['close'])
            indicators['cci'] = TechnicalIndicators.cci(df['high'], df['low'], df['close'])
            indicators['mfi'] = TechnicalIndicators.mfi(df['high'], df['low'], df['close'], df['volume'])
            
            # Volume
            indicators['obv'] = TechnicalIndicators.obv(df['close'], df['volume'])
            indicators['vwap'] = TechnicalIndicators.vwap(df['high'], df['low'], df['close'], df['volume'])
            
            # Advanced (Secret Sauce)
            prob, exp_p = TechnicalIndicators.monte_carlo_simulation(df['close'])
            indicators.update({'mc_probability': prob, 'mc_expected_price': exp_p})
            indicators['gk_volatility'] = TechnicalIndicators.garman_klass_volatility(df['high'], df['low'], df['open'], df['close'])
            indicators['z_score'] = TechnicalIndicators.z_score(df['close'])
            indicators['lr_slope'] = TechnicalIndicators.linear_regression_slope(df['close'])

        except Exception as e:
            # Jika ada error kalkulasi, tetap kembalikan dict yang sudah ada agar bot tidak crash
            print(f"Indicator calculation warning: {e}")
            
        return indicators

    # --- IMPLEMENTASI INDIKATOR ---
    
    @staticmethod
    def rsi(close: pd.Series, period: int = 14) -> float:
        if len(close) < period: return 50.0
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        val = rsi.iloc[-1]
        return val if not np.isnan(val) else 50.0

    @staticmethod
    def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        return macd_line.iloc[-1], signal_line.iloc[-1], (macd_line - signal_line).iloc[-1]

    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[float, float]:
        if len(close) < period: return 50.0, 50.0
        low_min = low.rolling(window=period).min()
        high_max = high.rolling(window=period).max()
        stoch_k = 100 * (close - low_min) / (high_max - low_min)
        stoch_d = stoch_k.rolling(window=3).mean()
        return stoch_k.fillna(50.0).iloc[-1], stoch_d.fillna(50.0).iloc[-1]

    @staticmethod
    def ema(close: pd.Series, period: int) -> float:
        return close.ewm(span=period, adjust=False).mean().iloc[-1]

    @staticmethod
    def sma(close: pd.Series, period: int) -> float:
        return close.rolling(window=period).mean().iloc[-1]

    @staticmethod
    def bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        return (sma + (std * std_dev)).iloc[-1], sma.iloc[-1], (sma - (std * std_dev)).iloc[-1]

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        tr = pd.concat([high - low, np.abs(high - close.shift()), np.abs(low - close.shift())], axis=1).max(axis=1)
        return tr.rolling(window=period).mean().iloc[-1]

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        if len(close) < period: return 20.0
        plus_dm = high.diff().clip(lower=0)
        minus_dm = (-low.diff()).clip(lower=0)
        tr = pd.concat([high - low, np.abs(high - close.shift()), np.abs(low - close.shift())], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        return dx.rolling(window=period).mean().iloc[-1]

    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> float:
        tp = (high + low + close) / 3
        sma = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        return ((tp - sma) / (0.015 * mad)).iloc[-1]

    @staticmethod
    def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> float:
        tp = (high + low + close) / 3
        pos_mf = (tp * volume).where(tp > tp.shift(), 0).rolling(period).sum()
        neg_mf = (tp * volume).where(tp < tp.shift(), 0).rolling(period).sum()
        res = 100 - (100 / (1 + pos_mf / neg_mf)).iloc[-1]
        return res if not np.isnan(res) else 50.0

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> float:
        return (np.sign(close.diff()).fillna(0) * volume).cumsum().iloc[-1]

    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> float:
        tp = (high + low + close) / 3
        return (tp * volume).cumsum().iloc[-1] / volume.cumsum().iloc[-1]

    @staticmethod
    def monte_carlo_simulation(close: pd.Series, simulations: int = 50, horizon: int = 10) -> Tuple[float, float]:
        returns = close.pct_change().dropna()
        if len(returns) < 5: return 0.5, close.iloc[-1]
        drift, vol = returns.mean(), returns.std()
        shocks = np.random.normal(drift, vol, (simulations, horizon))
        final_prices = close.iloc[-1] * np.prod(1 + shocks, axis=1)
        return np.mean(final_prices > close.iloc[-1]), np.mean(final_prices)

    @staticmethod
    def garman_klass_volatility(high: pd.Series, low: pd.Series, open_price: pd.Series, close: pd.Series, window: int = 20) -> float:
        if len(close) < window: return 0.0
        log_hl = (np.log(high) - np.log(low)) ** 2
        log_co = (np.log(close) - np.log(open_price)) ** 2
        gk = 0.5 * log_hl - (2 * np.log(2) - 1) * log_co
        return np.sqrt(gk.rolling(window=window).mean().iloc[-1] * 252)

    @staticmethod
    def z_score(close: pd.Series, window: int = 20) -> float:
        if len(close) < window: return 0.0
        return ((close - close.rolling(window).mean()) / close.rolling(window).std()).iloc[-1]

    @staticmethod
    def linear_regression_slope(close: pd.Series, window: int = 10) -> float:
        if len(close) < window: return 0.0
        y = close.iloc[-window:].values
        x = np.arange(len(y))
        slope, _, _, _, _ = stats.linregress(x, y)
        return slope / y[-1]

__all__ = ['TechnicalIndicators']