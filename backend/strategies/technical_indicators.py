"""
Technical indicators calculation for trading strategies.
Fast Python implementations of common TA indicators.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class IndicatorResult:
    """Container for indicator calculation results"""
    name: str
    value: float
    data: Optional[np.ndarray] = None
    metadata: Optional[Dict] = None

class TechnicalIndicators:
    """Fast technical indicator calculations"""
    
    @staticmethod
    def sma(prices: np.ndarray, period: int) -> np.ndarray:
        """Simple Moving Average"""
        return pd.Series(prices).rolling(window=period).mean().values
    
    @staticmethod
    def ema(prices: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average"""
        return pd.Series(prices).ewm(span=period, adjust=False).mean().values
    
    @staticmethod
    def rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Relative Strength Index
        
        Returns:
            RSI values (0-100)
        """
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)
        
        for i in range(period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            
            rs = up / down if down != 0 else 0
            rsi[i] = 100. - 100. / (1. + rs)
        
        return rsi
    
    @staticmethod
    def macd(
        prices: np.ndarray,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        MACD (Moving Average Convergence Divergence)
        
        Returns:
            (macd_line, signal_line, histogram)
        """
        ema_fast = TechnicalIndicators.ema(prices, fast_period)
        ema_slow = TechnicalIndicators.ema(prices, slow_period)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(
        prices: np.ndarray,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Bollinger Bands
        
        Returns:
            (upper_band, middle_band, lower_band)
        """
        middle_band = TechnicalIndicators.sma(prices, period)
        std = pd.Series(prices).rolling(window=period).std().values
        
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return upper_band, middle_band, lower_band
    
    @staticmethod
    def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Average True Range
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period
            
        Returns:
            ATR values
        """
        high_low = high - low
        high_close = np.abs(high - np.roll(close, 1))
        low_close = np.abs(low - np.roll(close, 1))
        
        ranges = np.maximum(high_low, high_close, low_close)
        atr = pd.Series(ranges).rolling(window=period).mean().values
        
        return atr
    
    @staticmethod
    def stochastic(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        k_period: int = 14,
        d_period: int = 3
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Stochastic Oscillator
        
        Returns:
            (%K, %D)
        """
        lowest_low = pd.Series(low).rolling(window=k_period).min().values
        highest_high = pd.Series(high).rolling(window=k_period).max().values
        
        k = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-10)
        d = pd.Series(k).rolling(window=d_period).mean().values
        
        return k, d
    
    @staticmethod
    def adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Average Directional Index
        
        Returns:
            ADX values (0-100, strength of trend)
        """
        # Calculate directional movement
        up_move = high - np.roll(high, 1)
        down_move = np.roll(low, 1) - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Calculate true range
        tr = TechnicalIndicators.atr(high, low, close, 1)
        
        # Smooth the values
        plus_di = 100 * pd.Series(plus_dm).rolling(window=period).sum().values / \
                  pd.Series(tr).rolling(window=period).sum().values
        minus_di = 100 * pd.Series(minus_dm).rolling(window=period).sum().values / \
                   pd.Series(tr).rolling(window=period).sum().values
        
        # Calculate DX and ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = pd.Series(dx).rolling(window=period).mean().values
        
        return adx
    
    @staticmethod
    def cci(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 20) -> np.ndarray:
        """
        Commodity Channel Index
        
        Returns:
            CCI values (typically -100 to +100)
        """
        typical_price = (high + low + close) / 3
        sma_tp = pd.Series(typical_price).rolling(window=period).mean().values
        mean_deviation = pd.Series(np.abs(typical_price - sma_tp)).rolling(window=period).mean().values
        
        cci = (typical_price - sma_tp) / (0.015 * mean_deviation + 1e-10)
        
        return cci
    
    @staticmethod
    def mfi(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Money Flow Index
        
        Returns:
            MFI values (0-100)
        """
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume
        
        positive_flow = np.where(typical_price > np.roll(typical_price, 1), money_flow, 0)
        negative_flow = np.where(typical_price < np.roll(typical_price, 1), money_flow, 0)
        
        positive_mf = pd.Series(positive_flow).rolling(window=period).sum().values
        negative_mf = pd.Series(negative_flow).rolling(window=period).sum().values
        
        mfi = 100 - (100 / (1 + positive_mf / (negative_mf + 1e-10)))
        
        return mfi
    
    @staticmethod
    def obv(close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """
        On-Balance Volume
        
        Returns:
            OBV values
        """
        obv = np.zeros_like(close)
        obv[0] = volume[0]
        
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv[i] = obv[i-1] + volume[i]
            elif close[i] < close[i-1]:
                obv[i] = obv[i-1] - volume[i]
            else:
                obv[i] = obv[i-1]
        
        return obv
    
    @staticmethod
    def vwap(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """
        Volume Weighted Average Price
        
        Returns:
            VWAP values
        """
        typical_price = (high + low + close) / 3
        cumulative_tpv = np.cumsum(typical_price * volume)
        cumulative_volume = np.cumsum(volume)
        
        vwap = cumulative_tpv / (cumulative_volume + 1e-10)
        
        return vwap

class IndicatorCalculator:
    """High-level indicator calculator with caching"""
    
    def __init__(self):
        self.cache = {}
    
    def calculate_all(self, ohlcv: pd.DataFrame) -> Dict[str, IndicatorResult]:
        """
        Calculate all indicators from OHLCV data
        
        Args:
            ohlcv: DataFrame with columns [timestamp, open, high, low, close, volume]
            
        Returns:
            Dictionary of indicator results
        """
        results = {}
        
        # Extract arrays
        high = ohlcv['high'].values
        low = ohlcv['low'].values
        close = ohlcv['close'].values
        volume = ohlcv['volume'].values
        
        # RSI
        rsi = TechnicalIndicators.rsi(close, 14)
        results['rsi'] = IndicatorResult(
            name='RSI',
            value=rsi[-1] if len(rsi) > 0 else 50,
            data=rsi
        )
        
        # MACD
        macd_line, signal_line, histogram = TechnicalIndicators.macd(close)
        results['macd'] = IndicatorResult(
            name='MACD',
            value=macd_line[-1] if len(macd_line) > 0 else 0,
            data=macd_line,
            metadata={'signal': signal_line[-1] if len(signal_line) > 0 else 0,
                     'histogram': histogram[-1] if len(histogram) > 0 else 0}
        )
        
        # EMAs
        for period in [9, 20, 50, 200]:
            ema = TechnicalIndicators.ema(close, period)
            results[f'ema_{period}'] = IndicatorResult(
                name=f'EMA{period}',
                value=ema[-1] if len(ema) > 0 else close[-1],
                data=ema
            )
        
        # Bollinger Bands
        upper, middle, lower = TechnicalIndicators.bollinger_bands(close)
        results['bb'] = IndicatorResult(
            name='BollingerBands',
            value=middle[-1] if len(middle) > 0 else close[-1],
            data=middle,
            metadata={
                'upper': upper[-1] if len(upper) > 0 else close[-1],
                'lower': lower[-1] if len(lower) > 0 else close[-1],
                'bandwidth': ((upper[-1] - lower[-1]) / middle[-1] * 100) if len(middle) > 0 else 0
            }
        )
        
        # ATR
        atr = TechnicalIndicators.atr(high, low, close)
        results['atr'] = IndicatorResult(
            name='ATR',
            value=atr[-1] if len(atr) > 0 else 0,
            data=atr
        )
        
        # Stochastic
        k, d = TechnicalIndicators.stochastic(high, low, close)
        results['stochastic'] = IndicatorResult(
            name='Stochastic',
            value=k[-1] if len(k) > 0 else 50,
            data=k,
            metadata={'d': d[-1] if len(d) > 0 else 50}
        )
        
        # ADX
        adx = TechnicalIndicators.adx(high, low, close)
        results['adx'] = IndicatorResult(
            name='ADX',
            value=adx[-1] if len(adx) > 0 else 0,
            data=adx
        )
        
        # CCI
        cci = TechnicalIndicators.cci(high, low, close)
        results['cci'] = IndicatorResult(
            name='CCI',
            value=cci[-1] if len(cci) > 0 else 0,
            data=cci
        )
        
        # MFI
        mfi = TechnicalIndicators.mfi(high, low, close, volume)
        results['mfi'] = IndicatorResult(
            name='MFI',
            value=mfi[-1] if len(mfi) > 0 else 50,
            data=mfi
        )
        
        # OBV
        obv = TechnicalIndicators.obv(close, volume)
        results['obv'] = IndicatorResult(
            name='OBV',
            value=obv[-1] if len(obv) > 0 else 0,
            data=obv
        )
        
        # VWAP
        vwap = TechnicalIndicators.vwap(high, low, close, volume)
        results['vwap'] = IndicatorResult(
            name='VWAP',
            value=vwap[-1] if len(vwap) > 0 else close[-1],
            data=vwap
        )
        
        # Volume analysis
        avg_volume = volume[-20:].mean() if len(volume) >= 20 else volume.mean()
        results['volume'] = IndicatorResult(
            name='Volume',
            value=volume[-1] if len(volume) > 0 else 0,
            metadata={
                'avg_volume': avg_volume,
                'volume_ratio': volume[-1] / avg_volume if avg_volume > 0 else 1
            }
        )
        
        return results
    
    def get_signal_strength(self, indicators: Dict[str, IndicatorResult], side: str = 'long') -> float:
        """
        Calculate overall signal strength from indicators
        
        Args:
            indicators: Dictionary of indicator results
            side: 'long' or 'short'
            
        Returns:
            Signal strength (0-1)
        """
        signals = []
        
        # RSI signals
        rsi = indicators.get('rsi')
        if rsi:
            if side == 'long':
                signals.append(1.0 if rsi.value < 30 else (0.5 if rsi.value < 40 else 0))
            else:
                signals.append(1.0 if rsi.value > 70 else (0.5 if rsi.value > 60 else 0))
        
        # MACD signals
        macd = indicators.get('macd')
        if macd and macd.metadata:
            histogram = macd.metadata.get('histogram', 0)
            if side == 'long':
                signals.append(1.0 if histogram > 0 else 0)
            else:
                signals.append(1.0 if histogram < 0 else 0)
        
        # Stochastic signals
        stoch = indicators.get('stochastic')
        if stoch:
            if side == 'long':
                signals.append(1.0 if stoch.value < 20 else (0.5 if stoch.value < 30 else 0))
            else:
                signals.append(1.0 if stoch.value > 80 else (0.5 if stoch.value > 70 else 0))
        
        # Return average signal strength
        return sum(signals) / len(signals) if signals else 0.5

# Example usage
if __name__ == "__main__":
    # Create sample data
    np.random.seed(42)
    prices = np.cumsum(np.random.randn(100)) + 100
    
    # Calculate RSI
    rsi = TechnicalIndicators.rsi(prices, 14)
    print(f"Latest RSI: {rsi[-1]:.2f}")
    
    # Calculate MACD
    macd, signal, hist = TechnicalIndicators.macd(prices)
    print(f"Latest MACD: {macd[-1]:.4f}, Signal: {signal[-1]:.4f}, Histogram: {hist[-1]:.4f}")
    
    # Test with DataFrame
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='5T'),
        'open': prices,
        'high': prices + np.random.rand(100),
        'low': prices - np.random.rand(100),
        'close': prices,
        'volume': np.random.rand(100) * 1000
    })
    
    calculator = IndicatorCalculator()
    indicators = calculator.calculate_all(df)
    
    print("\n📊 All Indicators:")
    for name, result in indicators.items():
        print(f"{result.name}: {result.value:.4f}")
