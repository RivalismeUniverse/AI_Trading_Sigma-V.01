"""
Scalping Strategy Implementation
9-Phase Technical Analysis System
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class ScalpingStrategy:
    """
    Complete scalping strategy with 9-phase technical analysis
    """
    
    def __init__(self):
        # Default configuration
        self.config = {
            'timeframe': '5m',
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'ema_fast': 8,
            'ema_slow': 21,
            'atr_period': 14,
            'volume_threshold': 1.2,
            'min_probability': 0.65,
            'stop_loss_atr_multiplier': 1.5,
            'take_profit_atr_multiplier': 2.0,
            'max_holding_minutes': 30
        }
        
        print("✅ Scalping strategy initialized")
    
    def configure(self, config: Dict):
        """Update strategy configuration"""
        self.config.update(config)
        print(f"🔧 Strategy configured: {config.get('strategy_name', 'Custom')}")
    
    async def analyze(self, market_data: pd.DataFrame) -> List[Dict]:
        """
        Complete 9-phase analysis
        
        Args:
            market_data: OHLCV DataFrame
            
        Returns:
            List of trading signals
        """
        if market_data.empty or len(market_data) < 50:
            print("⚠️ Insufficient data for analysis")
            return []
        
        signals = []
        
        try:
            # Phase 1: Calculate indicators
            df = self._calculate_indicators(market_data)
            
            # Phase 2: Momentum analysis
            momentum = self._calculate_momentum(df)
            
            # Phase 3: Volatility check
            volatility = self._calculate_volatility(df)
            
            # Phase 4: Support/Resistance
            sr_levels = self._identify_support_resistance(df)
            
            # Phase 5: Volume confirmation
            volume_ok = self._check_volume(df)
            
            # Phase 6: Entry conditions
            if self._check_entry_conditions(df, momentum, volatility, volume_ok):
                signal = self._generate_signal(df, sr_levels, momentum)
                signals.append(signal)
                
                print(f"🎯 Signal generated: {signal['action']} @ ${signal['entry_price']:.2f}")
            
            return signals
            
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return []
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        df = df.copy()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.config['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.config['rsi_period']).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # EMA
        df['ema_fast'] = df['close'].ewm(span=self.config['ema_fast']).mean()
        df['ema_slow'] = df['close'].ewm(span=self.config['ema_slow']).mean()
        
        # ATR (if not already calculated)
        if 'atr' not in df.columns:
            df['tr'] = df[['high', 'low']].apply(
                lambda x: x['high'] - x['low'], axis=1
            )
            df['atr'] = df['tr'].rolling(window=self.config['atr_period']).mean()
        
        # Volume MA
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        
        return df
    
    def _calculate_momentum(self, df: pd.DataFrame) -> float:
        """Calculate momentum score (-1 to 1)"""
        current_rsi = df['rsi'].iloc[-1]
        ema_diff = df['ema_fast'].iloc[-1] - df['ema_slow'].iloc[-1]
        
        # RSI component
        rsi_score = (current_rsi - 50) / 50  # Normalize to -1 to 1
        
        # EMA component
        ema_score = 1 if ema_diff > 0 else -1
        
        # Combined momentum
        momentum = (rsi_score + ema_score) / 2
        
        return momentum
    
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """Calculate normalized volatility"""
        current_atr = df['atr'].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        normalized_volatility = current_atr / current_price
        
        return normalized_volatility
    
    def _identify_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Identify key support and resistance levels"""
        recent_high = df['high'].rolling(window=20).max().iloc[-1]
        recent_low = df['low'].rolling(window=20).min().iloc[-1]
        current_close = df['close'].iloc[-1]
        
        pivot = (recent_high + recent_low + current_close) / 3
        
        return {
            'resistance': recent_high,
            'support': recent_low,
            'pivot': pivot
        }
    
    def _check_volume(self, df: pd.DataFrame) -> bool:
        """Check volume confirmation"""
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume_ma'].iloc[-1]
        
        threshold = self.config['volume_threshold']
        
        return current_volume > (avg_volume * threshold)
    
    def _check_entry_conditions(
        self,
        df: pd.DataFrame,
        momentum: float,
        volatility: float,
        volume_ok: bool
    ) -> bool:
        """Check if all entry conditions are met"""
        
        # Momentum check
        if abs(momentum) < 0.3:
            return False
        
        # Volatility check (not too high, not too low)
        if volatility < 0.003 or volatility > 0.02:
            return False
        
        # Volume check
        if not volume_ok:
            return False
        
        # RSI check
        current_rsi = df['rsi'].iloc[-1]
        if momentum > 0:  # Bullish
            if current_rsi > self.config['rsi_overbought']:
                return False
        else:  # Bearish
            if current_rsi < self.config['rsi_oversold']:
                return False
        
        return True
    
    def _generate_signal(
        self,
        df: pd.DataFrame,
        sr_levels: Dict,
        momentum: float
    ) -> Dict:
        """Generate trading signal"""
        
        current_price = df['close'].iloc[-1]
        current_atr = df['atr'].iloc[-1]
        
        # Determine direction
        direction = 'BUY' if momentum > 0 else 'SELL'
        
        # Calculate entry, stop, and targets
        if direction == 'BUY':
            entry = current_price
            stop_loss = entry - (current_atr * self.config['stop_loss_atr_multiplier'])
            take_profit = entry + (current_atr * self.config['take_profit_atr_multiplier'])
        else:
            entry = current_price
            stop_loss = entry + (current_atr * self.config['stop_loss_atr_multiplier'])
            take_profit = entry - (current_atr * self.config['take_profit_atr_multiplier'])
        
        # Calculate position size (simple 2% risk)
        risk_amount = 0.02  # 2% of account
        stop_distance = abs(entry - stop_loss)
        position_size = risk_amount / (stop_distance / entry) if stop_distance > 0 else 0.001
        
        # Calculate confidence based on multiple factors
        rsi = df['rsi'].iloc[-1]
        rsi_confidence = 1 - abs(rsi - 50) / 50  # Closer to extreme = higher confidence
        momentum_confidence = abs(momentum)
        
        confidence = (rsi_confidence + momentum_confidence) / 2
        
        return {
            'action': direction,
            'symbol': 'BTC/USDT',
            'entry_price': entry,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': min(position_size, 0.05),  # Cap at 5%
            'confidence': confidence,
            'risk_reward': abs((take_profit - entry) / (entry - stop_loss)) if direction == 'BUY' else abs((entry - take_profit) / (stop_loss - entry)),
            'max_holding_time': f"{self.config['max_holding_minutes']} minutes",
            'reasoning': f"{'Bullish' if direction == 'BUY' else 'Bearish'} momentum ({momentum:.2f}), RSI: {rsi:.1f}",
            'atr': current_atr
        }
    
    async def backtest(
        self,
        historical_data: pd.DataFrame,
        config: Dict
    ) -> Dict:
        """
        Backtest strategy on historical data
        
        Args:
            historical_data: Historical OHLCV data
            config: Strategy configuration
            
        Returns:
            Performance metrics
        """
        self.configure(config)
        
        print(f"📊 Running backtest on {len(historical_data)} candles...")
        
        trades = []
        
        # Sliding window backtest
        for i in range(100, len(historical_data) - 50):
            window = historical_data.iloc[i-100:i]
            
            signals = await self.analyze(window)
            
            if signals:
                # Simulate trade execution
                signal = signals[0]
                future_data = historical_data.iloc[i:i+50]
                
                trade_result = self._simulate_trade(signal, future_data)
                trades.append(trade_result)
        
        # Calculate metrics
        if not trades:
            print("⚠️ No trades in backtest")
            return self._empty_backtest_results()
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        win_rate = winning_trades / total_trades
        
        total_pnl = sum(t['pnl'] for t in trades)
        avg_win = np.mean([t['pnl'] for t in trades if t['pnl'] > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([t['pnl'] for t in trades if t['pnl'] < 0]) if (total_trades - winning_trades) > 0 else 0
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        results = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': self._calculate_sharpe(trades),
            'max_drawdown': self._calculate_max_drawdown(trades)
        }
        
        print(f"\n✅ Backtest Complete:")
        print(f"   Trades: {total_trades}")
        print(f"   Win Rate: {win_rate*100:.1f}%")
        print(f"   Total P&L: {total_pnl*100:+.2f}%")
        print(f"   Profit Factor: {profit_factor:.2f}")
        
        return results
    
    def _simulate_trade(self, signal: Dict, future_data: pd.DataFrame) -> Dict:
        """Simulate a single trade"""
        entry = signal['entry_price']
        stop_loss = signal['stop_loss']
        take_profit = signal['take_profit']
        direction = signal['action']
        
        for idx, row in future_data.iterrows():
            if direction == 'BUY':
                if row['low'] <= stop_loss:
                    pnl = (stop_loss - entry) / entry
                    return {'pnl': pnl, 'exit': 'stop_loss'}
                elif row['high'] >= take_profit:
                    pnl = (take_profit - entry) / entry
                    return {'pnl': pnl, 'exit': 'take_profit'}
            else:  # SELL
                if row['high'] >= stop_loss:
                    pnl = (entry - stop_loss) / entry
                    return {'pnl': pnl, 'exit': 'stop_loss'}
                elif row['low'] <= take_profit:
                    pnl = (entry - take_profit) / entry
                    return {'pnl': pnl, 'exit': 'take_profit'}
        
        # Time exit
        exit_price = future_data['close'].iloc[-1]
        if direction == 'BUY':
            pnl = (exit_price - entry) / entry
        else:
            pnl = (entry - exit_price) / entry
        
        return {'pnl': pnl, 'exit': 'time'}
    
    def _calculate_sharpe(self, trades: List[Dict]) -> float:
        """Calculate Sharpe ratio"""
        returns = [t['pnl'] for t in trades]
        if len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        sharpe = (mean_return / std_return) * np.sqrt(252)  # Annualized
        return sharpe
    
    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """Calculate maximum drawdown"""
        cumulative = np.cumsum([t['pnl'] for t in trades])
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        
        max_dd = np.min(drawdown) if len(drawdown) > 0 else 0.0
        return max_dd
    
    def _empty_backtest_results(self) -> Dict:
        """Return empty backtest results"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0
        }


# Test code
if __name__ == "__main__":
    import asyncio
    from datetime import datetime, timedelta
    
    async def test():
        # Initialize strategy
        strategy = ScalpingStrategy()
        
        # Generate test data
        print("\n" + "="*50)
        print("Generating test market data...")
        print("="*50)
        
        dates = pd.date_range(
            end=datetime.now(),
            periods=500,
            freq='5min'
        )
        
        np.random.seed(42)
        base_price = 45000
        returns = np.random.normal(0, 0.002, 500)
        prices = base_price * (1 + returns).cumprod()
        
        test_data = pd.DataFrame({
            'open': prices,
            'high': prices * (1 + np.random.uniform(0, 0.005, 500)),
            'low': prices * (1 - np.random.uniform(0, 0.005, 500)),
            'close': prices * (1 + np.random.normal(0, 0.001, 500)),
            'volume': np.random.uniform(100, 1000, 500)
        }, index=dates)
        
        # Test analysis
        print("\n" + "="*50)
        print("TEST 1: Signal Generation")
        print("="*50)
        
        signals = await strategy.analyze(test_data)
        
        if signals:
            for signal in signals:
                print(f"\n📊 Signal Details:")
                for key, value in signal.items():
                    print(f"   {key}: {value}")
        else:
            print("No signals generated (market conditions not met)")
        
        # Test backtest
        print("\n" + "="*50)
        print("TEST 2: Backtest")
        print("="*50)
        
        results = await strategy.backtest(test_data, strategy.config)
        
        print("\n✅ All tests completed!")
    
    asyncio.run(test())
