"""
ENHANCED Technical Indicators for Trading Strategies
Fast Python implementations with Monte Carlo, GK Volatility, Z-Score
Complete integration for scalping optimization
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

class EnhancedScalpingIndicators:
    """
    Advanced indicators specifically for scalping
    Based on Master Prompt Phase 1, 3, 5
    """
    
    # ===== PHASE 1: MONTE CARLO SIMULATION =====
    
    @staticmethod
    def monte_carlo_price_simulation(
        prices: np.ndarray,
        n_simulations: int = 5000,
        forecast_horizon: int = 30,
        timeframe_minutes: int = 5
    ) -> Dict[str, any]:
        """
        Monte Carlo simulation for price probability
        
        Args:
            prices: Historical price array
            n_simulations: Number of simulation paths (5000 recommended)
            forecast_horizon: How many candles to forecast (20-30)
            timeframe_minutes: Candle timeframe in minutes
            
        Returns:
            {
                'expected_prices': array of expected prices,
                'confidence_bands': {70%, 90%, 95%},
                'probability_up': probability of price going up,
                'probability_target': probability of reaching specific targets
            }
        """
        # Calculate drift and volatility from historical data
        returns = np.diff(np.log(prices))
        drift = np.mean(returns[-50:])  # Rolling 50-period mean
        volatility = np.std(returns[-50:])  # Rolling volatility
        
        # Time delta (fraction of day)
        dt = timeframe_minutes / 1440  # 1 day = 1440 minutes
        
        # Initialize simulation matrix
        simulated_paths = np.zeros((n_simulations, forecast_horizon))
        current_price = prices[-1]
        
        # Run Monte Carlo simulation
        for i in range(n_simulations):
            # Generate random normal samples
            random_shocks = np.random.normal(0, 1, forecast_horizon)
            
            # Simulate price path
            price_path = [current_price]
            for t in range(forecast_horizon):
                # Geometric Brownian Motion formula
                next_price = price_path[-1] * np.exp(
                    (drift - 0.5 * volatility**2) * dt + 
                    volatility * np.sqrt(dt) * random_shocks[t]
                )
                price_path.append(next_price)
            
            simulated_paths[i] = price_path[1:]
        
        # Calculate statistics
        expected_prices = np.mean(simulated_paths, axis=0)
        
        # Confidence bands (percentiles)
        confidence_bands = {
            '70%': {
                'lower': np.percentile(simulated_paths, 15, axis=0),
                'upper': np.percentile(simulated_paths, 85, axis=0)
            },
            '90%': {
                'lower': np.percentile(simulated_paths, 5, axis=0),
                'upper': np.percentile(simulated_paths, 95, axis=0)
            },
            '95%': {
                'lower': np.percentile(simulated_paths, 2.5, axis=0),
                'upper': np.percentile(simulated_paths, 97.5, axis=0)
            }
        }
        
        # Calculate probabilities
        final_prices = simulated_paths[:, -1]
        probability_up = np.sum(final_prices > current_price) / n_simulations
        
        # Target probabilities (1%, 2%, 3% moves)
        target_probabilities = {
            '+1%': np.sum(final_prices > current_price * 1.01) / n_simulations,
            '+2%': np.sum(final_prices > current_price * 1.02) / n_simulations,
            '+3%': np.sum(final_prices > current_price * 1.03) / n_simulations,
            '-1%': np.sum(final_prices < current_price * 0.99) / n_simulations,
            '-2%': np.sum(final_prices < current_price * 0.98) / n_simulations,
            '-3%': np.sum(final_prices < current_price * 0.97) / n_simulations,
        }
        
        return {
            'expected_prices': expected_prices,
            'confidence_bands': confidence_bands,
            'probability_up': probability_up,
            'target_probabilities': target_probabilities,
            'simulated_paths': simulated_paths,  # For visualization
            'drift': drift,
            'volatility': volatility
        }
    
    # ===== PHASE 3: GARMAN-KLASS VOLATILITY =====
    
    @staticmethod
    def garman_klass_volatility(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        open: np.ndarray,
        window: int = 20
    ) -> np.ndarray:
        """
        Garman-Klass volatility estimator (more accurate than standard vol)
        
        Formula:
        GK_Vol = sqrt( 0.5 * ln(H/L)^2 - (2*ln(2)-1) * ln(C/O)^2 )
        
        This estimator is 7.4x more efficient than close-to-close volatility
        """
        # Prevent division by zero
        high = high + 1e-10
        low = low + 1e-10
        open = open + 1e-10
        close = close + 1e-10
        
        # Calculate components
        hl_component = 0.5 * (np.log(high / low)) ** 2
        co_component = (2 * np.log(2) - 1) * (np.log(close / open)) ** 2
        
        # Garman-Klass volatility
        gk_variance = hl_component - co_component
        
        # Rolling window average
        gk_vol = pd.Series(gk_variance).rolling(window=window).mean().values
        gk_vol = np.sqrt(np.maximum(gk_vol, 0))  # Ensure non-negative
        
        # Annualize (assuming 1440 minutes per day for 1m timeframe)
        # Adjust based on your timeframe
        gk_vol = gk_vol * np.sqrt(1440)
        
        return gk_vol
    
    @staticmethod
    def combined_volatility_score(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        open: np.ndarray,
        atr: np.ndarray
    ) -> np.ndarray:
        """
        Combined volatility score from Master Prompt
        
        Formula:
        Vol_Score = 0.6 × GK_Vol + 0.4 × ATR_Vol
        """
        # Garman-Klass volatility
        gk_vol = EnhancedScalpingIndicators.garman_klass_volatility(
            high, low, close, open
        )
        
        # ATR-based volatility (normalized)
        atr_vol = atr / close
        
        # Combine (60% GK, 40% ATR)
        combined_vol = 0.6 * gk_vol + 0.4 * atr_vol
        
        return combined_vol
    
    # ===== PHASE 5: Z-SCORE MEAN REVERSION =====
    
    @staticmethod
    def z_score_indicator(
        prices: np.ndarray,
        period: int = 20
    ) -> Tuple[np.ndarray, Dict[str, any]]:
        """
        Z-Score for mean reversion scalping
        
        Formula:
        Z_Score = (Current_Price - SMA) / StdDev
        
        Signals:
        - Z > 2: Overbought (short signal)
        - Z < -2: Oversold (long signal)
        - |Z| < 0.5: No trade zone
        
        Returns:
            (z_scores, signals)
        """
        # Calculate SMA and StdDev
        sma = pd.Series(prices).rolling(window=period).mean().values
        std = pd.Series(prices).rolling(window=period).std().values
        
        # Calculate Z-Score
        z_scores = (prices - sma) / (std + 1e-10)  # Avoid division by zero
        
        # Generate signals
        signals = {
            'oversold': z_scores < -2,      # Long signal
            'overbought': z_scores > 2,     # Short signal
            'neutral': np.abs(z_scores) < 0.5,  # No trade zone
            'moderate_long': (z_scores < -1) & (z_scores >= -2),
            'moderate_short': (z_scores > 1) & (z_scores <= 2)
        }
        
        return z_scores, signals
    
    @staticmethod
    def linear_regression_slope(
        prices: np.ndarray,
        period: int = 10
    ) -> np.ndarray:
        """
        Linear regression slope for micro-trend detection
        Perfect for scalping!
        
        Formula:
        Slope = (n×Σ(xy) - Σ(x)×Σ(y)) / (n×Σ(x²) - (Σ(x))²)
        """
        slopes = np.zeros(len(prices))
        
        for i in range(period, len(prices)):
            window = prices[i-period:i]
            x = np.arange(period)
            
            # Calculate slope using least squares
            n = period
            sum_x = np.sum(x)
            sum_y = np.sum(window)
            sum_xy = np.sum(x * window)
            sum_x2 = np.sum(x ** 2)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            slopes[i] = slope
        
        return slopes
    
    @staticmethod
    def bollinger_squeeze_detector(
        prices: np.ndarray,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Bollinger Band Squeeze detection
        Identifies consolidation before breakout
        
        Returns:
            (bb_width, squeeze_signal)
        """
        # Calculate Bollinger Bands
        sma = pd.Series(prices).rolling(window=period).mean().values
        std = pd.Series(prices).rolling(window=period).std().values
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        # BB Width (normalized)
        bb_width = (upper_band - lower_band) / (sma + 1e-10)
        
        # BB Width 20-period low (squeeze condition)
        bb_width_20_low = pd.Series(bb_width).rolling(window=20).min().values
        
        # Squeeze signal (current width is at 20-period low)
        squeeze_signal = bb_width <= (bb_width_20_low * 1.05)  # 5% tolerance
        
        return bb_width, squeeze_signal
    
    # ===== BONUS: KELLY POSITION SIZING =====
    
    @staticmethod
    def kelly_position_size(
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        account_balance: float,
        current_volatility: float,
        target_volatility: float = 0.02,
        max_risk: float = 0.02
    ) -> float:
        """
        Kelly Criterion position sizing with volatility adjustment
        
        Formula:
        Kelly% = (Win_Rate × Avg_Win - Loss_Rate × Avg_Loss) / Avg_Win
        
        Adjusted for volatility:
        Position = Kelly% × (Target_Vol / Current_Vol) × Max_Risk
        """
        loss_rate = 1 - win_rate
        
        # Kelly fraction
        kelly_fraction = (win_rate * avg_win - loss_rate * avg_loss) / avg_win
        
        # Cap Kelly at 0.25 (quarter Kelly for safety)
        kelly_fraction = min(kelly_fraction, 0.25)
        
        # Volatility adjustment
        vol_adjustment = target_volatility / (current_volatility + 1e-10)
        vol_adjustment = np.clip(vol_adjustment, 0.5, 2.0)  # Limit adjustment
        
        # Final position size
        position_fraction = kelly_fraction * vol_adjustment * max_risk
        position_size = account_balance * position_fraction
        
        return max(0, position_size)  # Ensure non-negative

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

    def calculate_all_enhanced(self, ohlcv: pd.DataFrame) -> Dict[str, any]:
        """
        Calculate ALL indicators including enhanced ones
        Combines original 12 + enhanced scalping indicators
        
        Args:
            ohlcv: DataFrame with columns [timestamp, open, high, low, close, volume]
            
        Returns:
            Dictionary with all indicator results including enhanced ones
        """
        # First calculate original indicators
        basic_results = self.calculate_all(ohlcv)
        
        # Extract OHLCV arrays
        high = ohlcv['high'].values
        low = ohlcv['low'].values
        close = ohlcv['close'].values
        open_prices = ohlcv['open'].values
        volume = ohlcv['volume'].values
        
        # Calculate ATR
        atr = TechnicalIndicators.atr(high, low, close)
        
        # Initialize enhanced indicators calculator
        enhanced = EnhancedScalpingIndicators()
        
        # 1. Monte Carlo Simulation
        mc_result = enhanced.monte_carlo_price_simulation(close)
        
        # 2. Garman-Klass Volatility
        gk_vol = enhanced.garman_klass_volatility(high, low, close, open_prices)
        combined_vol = enhanced.combined_volatility_score(high, low, close, open_prices, atr)
        
        # 3. Z-Score Mean Reversion
        z_scores, z_signals = enhanced.z_score_indicator(close)
        
        # 4. Linear Regression Slope
        lr_slope = enhanced.linear_regression_slope(close)
        
        # 5. Bollinger Squeeze
        bb_width, squeeze_signal = enhanced.bollinger_squeeze_detector(close)
        
        # Combine all results
        combined_results = {
            # Basic indicators
            'basic_indicators': basic_results,
            
            # Enhanced indicators
            'enhanced_indicators': {
                # Monte Carlo
                'mc_probability_up': mc_result['probability_up'],
                'mc_expected_price': mc_result['expected_prices'][-1] if len(mc_result['expected_prices']) > 0 else close[-1],
                'mc_target_probabilities': mc_result['target_probabilities'],
                
                # Volatility
                'gk_volatility': gk_vol[-1] if len(gk_vol) > 0 else 0,
                'combined_volatility': combined_vol[-1] if len(combined_vol) > 0 else 0,
                
                # Mean Reversion
                'z_score': z_scores[-1] if len(z_scores) > 0 else 0,
                'z_oversold': bool(z_signals['oversold'][-1]) if len(z_scores) > 0 else False,
                'z_overbought': bool(z_signals['overbought'][-1]) if len(z_scores) > 0 else False,
                
                # Micro-trend
                'lr_slope': lr_slope[-1] if len(lr_slope) > 0 else 0,
                
                # Squeeze
                'bb_squeeze': bool(squeeze_signal[-1]) if len(squeeze_signal) > 0 else False,
                'bb_width': bb_width[-1] if len(bb_width) > 0 else 0,
            }
        }
        
        return combined_results

# Example usage and testing
if __name__ == "__main__":
    # Create sample data
    np.random.seed(42)
    prices = np.cumsum(np.random.randn(100)) + 100
    
    print("📊 TESTING TECHNICAL INDICATORS")
    print("=" * 50)
    
    # Test basic TechnicalIndicators
    print("\n1. BASIC INDICATORS:")
    rsi = TechnicalIndicators.rsi(prices, 14)
    print(f"   Latest RSI: {rsi[-1]:.2f}")
    
    macd, signal, hist = TechnicalIndicators.macd(prices)
    print(f"   Latest MACD: {macd[-1]:.4f}, Signal: {signal[-1]:.4f}, Histogram: {hist[-1]:.4f}")
    
    # Test with DataFrame
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='5T'),
        'open': prices,
        'high': prices + np.random.rand(100),
        'low': prices - np.random.rand(100),
        'close': prices,
        'volume': np.random.rand(100) * 1000
    })
    
    # Test IndicatorCalculator
    print("\n2. INDICATOR CALCULATOR:")
    calculator = IndicatorCalculator()
    indicators = calculator.calculate_all(df)
    
    print("   Basic Indicators:")
    for name, result in list(indicators.items())[:5]:  # Show first 5
        print(f"   {result.name}: {result.value:.4f}")
    
    # Test EnhancedScalpingIndicators
    print("\n3. ENHANCED SCALPING INDICATORS:")
    enhanced = EnhancedScalpingIndicators()
    
    # Monte Carlo
    mc = enhanced.monte_carlo_price_simulation(prices)
    print(f"   Probability UP: {mc['probability_up']:.2%}")
    print(f"   Target +2% probability: {mc['target_probabilities']['+2%']:.2%}")
    
    # Z-Score
    z_scores, signals = enhanced.z_score_indicator(prices)
    print(f"   Current Z-Score: {z_scores[-1]:.2f}")
    print(f"   Oversold: {signals['oversold'][-1]}")
    
    # Test combined enhanced calculation
    print("\n4. COMBINED ENHANCED CALCULATION:")
    combined = calculator.calculate_all_enhanced(df)
    
    enhanced_indicators = combined['enhanced_indicators']
    print(f"   MC Probability Up: {enhanced_indicators['mc_probability_up']:.2%}")
    print(f"   Z-Score: {enhanced_indicators['z_score']:.2f}")
    print(f"   GK Volatility: {enhanced_indicators['gk_volatility']:.4f}")
    print(f"   Linear Regression Slope: {enhanced_indicators['lr_slope']:.6f}")
    print(f"   Bollinger Squeeze: {enhanced_indicators['bb_squeeze']}")
    
    print("\n" + "=" * 50)
    print("✅ All indicators successfully integrated into one file!")
