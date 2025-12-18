"""
Benchmark Script: V1 vs V1+V2
Performance comparison for backtest data
"""

import sys
sys.path.append('..')

import pandas as pd
import numpy as np
from datetime import datetime
import time

from core.integrated_signal_manager import IntegratedSignalManager


def generate_realistic_market_data(periods=1000, trend='mixed'):
    """
    Generate realistic market data with different regimes
    
    trend: 'bullish', 'bearish', 'ranging', 'mixed'
    """
    np.random.seed(42)
    
    dates = pd.date_range(start='2024-01-01', periods=periods, freq='5min')
    base_price = 50000
    
    if trend == 'bullish':
        drift = 0.0003
        volatility = 0.015
    elif trend == 'bearish':
        drift = -0.0003
        volatility = 0.015
    elif trend == 'ranging':
        drift = 0.0
        volatility = 0.010
    else:  # mixed
        # Create different regime periods
        drift = np.where(
            np.arange(periods) < periods/3, 0.0003,
            np.where(np.arange(periods) < 2*periods/3, -0.0003, 0.0)
        )
        volatility = 0.015
    
    # Generate returns
    if isinstance(drift, np.ndarray):
        returns = np.random.normal(drift, volatility)
    else:
        returns = np.random.normal(drift, volatility, periods)
    
    prices = base_price * (1 + returns).cumprod()
    
    # Generate OHLCV
    data = {
        'timestamp': dates,
        'open': prices + np.random.uniform(-50, 50, periods),
        'high': prices + np.random.uniform(0, 150, periods),
        'low': prices - np.random.uniform(0, 150, periods),
        'close': prices,
        'volume': np.random.uniform(100, 1000, periods) * (1 + abs(returns) * 10)
    }
    
    df = pd.DataFrame(data)
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    df['current_price'] = df['close']
    
    return df


def simulate_trading(df, signal_manager, initial_balance=10000):
    """
    Simple backtest simulation
    Returns performance metrics
    """
    balance = initial_balance
    trades = []
    open_position = None
    
    # Walk through data
    for i in range(200, len(df), 12):  # Every hour (12 * 5min)
        df_slice = df.iloc[:i]
        
        # Generate signal
        signal = signal_manager.generate_signal(df_slice, 'BTC/USDT:USDT')
        
        current_price = signal['current_price']
        
        # If no position and signal says enter
        if open_position is None:
            if signal['action'] in ['ENTER_LONG', 'ENTER_SHORT']:
                if signal['confidence'] > 0.55:  # Minimum confidence threshold
                    open_position = {
                        'type': signal['action'],
                        'entry_price': current_price,
                        'stop_loss': signal['stop_loss'],
                        'take_profit': signal['take_profit'],
                        'size': (balance * 0.02) / abs(current_price - signal['stop_loss']),  # 2% risk
                        'entry_time': i
                    }
        
        # If position is open, check exit conditions
        elif open_position is not None:
            close_position = False
            exit_reason = ''
            
            if open_position['type'] == 'ENTER_LONG':
                if current_price <= open_position['stop_loss']:
                    close_position = True
                    exit_reason = 'stop_loss'
                elif current_price >= open_position['take_profit']:
                    close_position = True
                    exit_reason = 'take_profit'
            else:  # SHORT
                if current_price >= open_position['stop_loss']:
                    close_position = True
                    exit_reason = 'stop_loss'
                elif current_price <= open_position['take_profit']:
                    close_position = True
                    exit_reason = 'take_profit'
            
            if close_position:
                # Calculate P&L
                if open_position['type'] == 'ENTER_LONG':
                    pnl = (current_price - open_position['entry_price']) * open_position['size']
                else:
                    pnl = (open_position['entry_price'] - current_price) * open_position['size']
                
                balance += pnl
                
                trades.append({
                    'type': open_position['type'],
                    'entry_price': open_position['entry_price'],
                    'exit_price': current_price,
                    'pnl': pnl,
                    'exit_reason': exit_reason,
                    'duration': i - open_position['entry_time']
                })
                
                open_position = None
    
    # Calculate metrics
    if not trades:
        return {
            'total_trades': 0,
            'win_rate': 0,
            'total_return': 0,
            'profit_factor': 0,
            'avg_win': 0,
            'avg_loss': 0
        }
    
    winning_trades = [t for t in trades if t['pnl'] > 0]
    losing_trades = [t for t in trades if t['pnl'] <= 0]
    
    total_profit = sum(t['pnl'] for t in winning_trades)
    total_loss = abs(sum(t['pnl'] for t in losing_trades))
    
    return {
        'total_trades': len(trades),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': (len(winning_trades) / len(trades) * 100) if trades else 0,
        'total_return': ((balance - initial_balance) / initial_balance * 100),
        'final_balance': balance,
        'profit_factor': (total_profit / total_loss) if total_loss > 0 else 0,
        'avg_win': (total_profit / len(winning_trades)) if winning_trades else 0,
        'avg_loss': (total_loss / len(losing_trades)) if losing_trades else 0,
        'avg_duration': np.mean([t['duration'] for t in trades])
    }


def run_benchmark():
    """Run comprehensive benchmark"""
    
    print("=" * 100)
    print(" " * 30 + "AI TRADING SIGMA - SIGNAL BENCHMARK")
    print("=" * 100)
    
    # Test different market conditions
    market_conditions = ['bullish', 'bearish', 'ranging', 'mixed']
    
    results = {}
    
    for condition in market_conditions:
        print(f"\n{'='*100}")
        print(f"Testing Market Condition: {condition.upper()}")
        print(f"{'='*100}")
        
        # Generate data
        print(f"\nGenerating {condition} market data (1000 periods)...")
        df = generate_realistic_market_data(periods=1000, trend=condition)
        
        # Initialize signal managers
        v1_only = IntegratedSignalManager(use_v2_validation=False)
        v1_v2 = IntegratedSignalManager(use_v2_validation=True)
        
        # Benchmark V1 only
        print("\n[1/2] Running V1 Only backtest...")
        start = time.time()
        results_v1 = simulate_trading(df, v1_only)
        time_v1 = time.time() - start
        
        # Benchmark V1+V2
        print("[2/2] Running V1+V2 backtest...")
        start = time.time()
        results_v2 = simulate_trading(df, v1_v2)
        time_v2 = time.time() - start
        
        # Store results
        results[condition] = {
            'v1_only': results_v1,
            'v1_v2': results_v2,
            'time_v1': time_v1,
            'time_v2': time_v2
        }
        
        # Display comparison
        print(f"\n{'Metric':<25} {'V1 Only':<25} {'V1+V2':<25} {'Difference'}")
        print("-" * 100)
        
        metrics = [
            ('Total Trades', 'total_trades', ''),
            ('Winning Trades', 'winning_trades', ''),
            ('Win Rate', 'win_rate', '%'),
            ('Total Return', 'total_return', '%'),
            ('Final Balance', 'final_balance', '$'),
            ('Profit Factor', 'profit_factor', ''),
            ('Avg Win', 'avg_win', '$'),
            ('Avg Loss', 'avg_loss', '$'),
            ('Execution Time', None, 's')
        ]
        
        for label, key, unit in metrics:
            if key is None:
                v1_val = time_v1
                v2_val = time_v2
            else:
                v1_val = results_v1[key]
                v2_val = results_v2[key]
            
            diff = v2_val - v1_val
            
            if unit == '%':
                v1_str = f"{v1_val:.2f}%"
                v2_str = f"{v2_val:.2f}%"
                diff_str = f"{'+' if diff > 0 else ''}{diff:.2f}%"
            elif unit == '$':
                v1_str = f"${v1_val:,.2f}"
                v2_str = f"${v2_val:,.2f}"
                diff_str = f"{'+' if diff > 0 else ''}${diff:,.2f}"
            elif unit == 's':
                v1_str = f"{v1_val:.2f}s"
                v2_str = f"{v2_val:.2f}s"
                diff_str = f"{'+' if diff > 0 else ''}{diff:.2f}s"
            else:
                v1_str = f"{v1_val:.0f}"
                v2_str = f"{v2_val:.0f}"
                diff_str = f"{'+' if diff > 0 else ''}{diff:.0f}"
            
            # Highlight better performer
            if key in ['win_rate', 'total_return', 'profit_factor']:
                winner = '✅' if v2_val > v1_val else ('🟡' if v2_val == v1_val else '❌')
            else:
                winner = '  '
            
            print(f"{label:<25} {v1_str:<25} {v2_str:<25} {diff_str} {winner}")
    
    # Overall summary
    print("\n" + "=" * 100)
    print(" " * 35 + "OVERALL SUMMARY")
    print("=" * 100)
    
    print(f"\n{'Market Condition':<20} {'V1 Win Rate':<20} {'V1+V2 Win Rate':<20} {'Improvement'}")
    print("-" * 100)
    
    for condition in market_conditions:
        v1_wr = results[condition]['v1_only']['win_rate']
        v2_wr = results[condition]['v1_v2']['win_rate']
        diff = v2_wr - v1_wr
        
        print(f"{condition.capitalize():<20} {v1_wr:>6.2f}%{'':<13} {v2_wr:>6.2f}%{'':<13} {'+' if diff > 0 else ''}{diff:>6.2f}%")
    
    # Calculate averages
    avg_v1_wr = np.mean([results[c]['v1_only']['win_rate'] for c in market_conditions])
    avg_v2_wr = np.mean([results[c]['v1_v2']['win_rate'] for c in market_conditions])
    
    print("-" * 100)
    print(f"{'AVERAGE':<20} {avg_v1_wr:>6.2f}%{'':<13} {avg_v2_wr:>6.2f}%{'':<13} {'+' if avg_v2_wr > avg_v1_wr else ''}{avg_v2_wr - avg_v1_wr:>6.2f}%")
    
    # Conclusion
    print("\n" + "=" * 100)
    print("CONCLUSION")
    print("=" * 100)
    
    if avg_v2_wr > avg_v1_wr:
        print("✅ V1+V2 (Full System) performs BETTER on average")
        print(f"   - Higher win rate: {avg_v2_wr:.2f}% vs {avg_v1_wr:.2f}%")
        print(f"   - Better filtering of weak signals")
        print(f"   - Recommended for conservative trading")
    elif avg_v2_wr < avg_v1_wr:
        print("✅ V1 Only performs BETTER on average")
        print(f"   - Higher win rate: {avg_v1_wr:.2f}% vs {avg_v2_wr:.2f}%")
        print(f"   - More aggressive signal generation")
        print(f"   - Recommended for active trading")
    else:
        print("🟡 Both systems perform EQUALLY well")
        print(f"   - Use V1+V2 for better explainability")
    
    print("\n" + "=" * 100)
    print("Benchmark complete! ✅")
    print("=" * 100)


if __name__ == '__main__':
    run_benchmark()
