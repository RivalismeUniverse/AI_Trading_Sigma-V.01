"""
Backtesting engine for strategy validation.
Tests strategies on historical data to evaluate performance.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from backend.strategies.scalping_strategy import ScalpingStrategy
from backend.strategies.technical_indicators import IndicatorCalculator
from backend.core.signal_generator import SignalGenerator
from backend.utils.helpers import (
    calculate_position_size, calculate_pnl, calculate_sharpe_ratio,
    calculate_max_drawdown, calculate_win_rate
)

logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    Comprehensive backtesting engine for strategy validation.
    
    Features:
    - Historical data replay
    - Realistic order execution simulation
    - Commission and slippage modeling
    - Performance metrics calculation
    - Equity curve generation
    - Trade-by-trade analysis
    """
    
    def __init__(
        self,
        initial_balance: float = 10000,
        commission: float = 0.0005,  # 0.05%
        slippage: float = 0.0002,    # 0.02%
    ):
        """
        Initialize backtest engine
        
        Args:
            initial_balance: Starting capital
            commission: Trading commission (percentage)
            slippage: Slippage (percentage)
        """
        self.initial_balance = initial_balance
        self.commission = commission
        self.slippage = slippage
        
        # Components
        self.indicator_calculator = IndicatorCalculator()
        self.signal_generator = SignalGenerator()
        
        # State tracking
        self.balance = initial_balance
        self.equity = initial_balance
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[float] = [initial_balance]
        self.open_position: Optional[Dict[str, Any]] = None
        
        logger.info(f"Backtest engine initialized with ${initial_balance:,.2f}")
    
    def run(
        self,
        strategy: ScalpingStrategy,
        historical_data: pd.DataFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Run backtest on historical data
        
        Args:
            strategy: Trading strategy to test
            historical_data: OHLCV DataFrame
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            Comprehensive backtest results
        """
        logger.info(f"Starting backtest: {strategy.name}")
        
        # Filter data by date range
        if start_date:
            historical_data = historical_data[historical_data['timestamp'] >= start_date]
        if end_date:
            historical_data = historical_data[historical_data['timestamp'] <= end_date]
        
        if len(historical_data) < 200:
            raise ValueError("Insufficient historical data for backtest (need 200+ candles)")
        
        # Reset state
        self._reset_state()
        
        # Process each candle
        for i in range(200, len(historical_data)):
            # Get historical window for indicators
            window = historical_data.iloc[max(0, i-200):i]
            current_candle = historical_data.iloc[i]
            
            # Calculate indicators
            indicators = self.indicator_calculator.calculate_all(window)
            
            # Generate signal
            signal = strategy.generate_signal(window, indicators)
            
            # Process signal
            self._process_signal(
                signal,
                current_candle,
                indicators,
                strategy
            )
            
            # Update equity
            self._update_equity(current_candle)
        
        # Close any open position at end
        if self.open_position:
            last_candle = historical_data.iloc[-1]
            self._close_position(
                last_candle['close'],
                "Backtest end",
                last_candle['timestamp']
            )
        
        # Calculate results
        results = self._calculate_results(
            start_date=historical_data.iloc[0]['timestamp'],
            end_date=historical_data.iloc[-1]['timestamp']
        )
        
        logger.info(f"Backtest complete: {len(self.trades)} trades, "
                   f"Final balance: ${self.balance:,.2f}")
        
        return results
    
    def _process_signal(
        self,
        signal: Dict[str, Any],
        candle: pd.Series,
        indicators: Dict[str, Any],
        strategy: ScalpingStrategy
    ):
        """Process trading signal"""
        # Check for exit signal if position open
        if self.open_position:
            if self._should_exit(signal, candle):
                self._close_position(
                    candle['close'],
                    signal.get('reason', 'Signal exit'),
                    candle['timestamp']
                )
            return
        
        # Check for entry signal
        if signal['action'] in ['long', 'short']:
            self._open_position(
                signal,
                candle,
                strategy.leverage
            )
    
    def _open_position(
        self,
        signal: Dict[str, Any],
        candle: pd.Series,
        leverage: float
    ):
        """Open new position"""
        # Calculate entry price with slippage
        entry_price = candle['close'] * (1 + self.slippage)
        
        # Calculate position size
        position_size = calculate_position_size(
            balance=self.balance,
            risk_percent=0.02,  # 2% risk
            entry_price=entry_price,
            stop_loss=signal['stop_loss'],
            leverage=leverage
        )
        
        # Calculate commission
        trade_value = position_size * entry_price
        commission_cost = trade_value * self.commission
        
        # Check if we have enough balance
        if commission_cost > self.balance:
            logger.debug("Insufficient balance for commission")
            return
        
        # Deduct commission
        self.balance -= commission_cost
        
        # Create position
        self.open_position = {
            'side': signal['action'],
            'entry_price': entry_price,
            'entry_time': candle['timestamp'],
            'quantity': position_size,
            'leverage': leverage,
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'entry_reason': signal.get('reason', 'Signal'),
            'commission_paid': commission_cost
        }
        
        logger.debug(f"Opened {signal['action']} position: "
                    f"{position_size:.4f} @ ${entry_price:.2f}")
    
    def _close_position(
        self,
        exit_price: float,
        exit_reason: str,
        exit_time: datetime
    ):
        """Close open position"""
        if not self.open_position:
            return
        
        # Apply slippage
        exit_price = exit_price * (1 - self.slippage)
        
        # Calculate P&L
        pnl_data = calculate_pnl(
            side=self.open_position['side'],
            entry_price=self.open_position['entry_price'],
            exit_price=exit_price,
            quantity=self.open_position['quantity'],
            leverage=self.open_position['leverage']
        )
        
        # Calculate exit commission
        trade_value = self.open_position['quantity'] * exit_price
        exit_commission = trade_value * self.commission
        
        # Net P&L after commissions
        net_pnl = pnl_data['pnl'] - exit_commission - self.open_position['commission_paid']
        
        # Update balance
        self.balance += net_pnl
        
        # Record trade
        trade = {
            'entry_time': self.open_position['entry_time'],
            'exit_time': exit_time,
            'side': self.open_position['side'],
            'entry_price': self.open_position['entry_price'],
            'exit_price': exit_price,
            'quantity': self.open_position['quantity'],
            'leverage': self.open_position['leverage'],
            'pnl': net_pnl,
            'pnl_percent': (net_pnl / self.initial_balance) * 100,
            'return_on_equity': pnl_data['roi'],
            'entry_reason': self.open_position['entry_reason'],
            'exit_reason': exit_reason,
            'commission': self.open_position['commission_paid'] + exit_commission,
            'duration': (exit_time - self.open_position['entry_time']).total_seconds() / 60
        }
        
        self.trades.append(trade)
        
        logger.debug(f"Closed position: P&L ${net_pnl:.2f} ({trade['pnl_percent']:.2f}%)")
        
        # Clear position
        self.open_position = None
    
    def _should_exit(self, signal: Dict[str, Any], candle: pd.Series) -> bool:
        """Check if position should be exited"""
        if not self.open_position:
            return False
        
        current_price = candle['close']
        position = self.open_position
        
        # Check stop loss
        if position['side'] == 'long' and current_price <= position['stop_loss']:
            return True
        if position['side'] == 'short' and current_price >= position['stop_loss']:
            return True
        
        # Check take profit
        if position['side'] == 'long' and current_price >= position['take_profit']:
            return True
        if position['side'] == 'short' and current_price <= position['take_profit']:
            return True
        
        # Check exit signal
        if signal['action'] == 'close':
            return True
        
        return False
    
    def _update_equity(self, candle: pd.Series):
        """Update equity curve"""
        current_equity = self.balance
        
        # Add unrealized P&L if position open
        if self.open_position:
            pnl_data = calculate_pnl(
                side=self.open_position['side'],
                entry_price=self.open_position['entry_price'],
                exit_price=candle['close'],
                quantity=self.open_position['quantity'],
                leverage=self.open_position['leverage']
            )
            current_equity += pnl_data['pnl']
        
        self.equity = current_equity
        self.equity_curve.append(current_equity)
    
    def _reset_state(self):
        """Reset backtest state"""
        self.balance = self.initial_balance
        self.equity = self.initial_balance
        self.trades = []
        self.equity_curve = [self.initial_balance]
        self.open_position = None
    
    def _calculate_results(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate comprehensive backtest results"""
        if not self.trades:
            return {
                'success': False,
                'message': 'No trades executed'
            }
        
        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        losing_trades = len([t for t in self.trades if t['pnl'] <= 0])
        
        # P&L metrics
        total_pnl = sum(t['pnl'] for t in self.trades)
        total_return = (self.balance - self.initial_balance) / self.initial_balance * 100
        
        # Win rate
        win_rate_data = calculate_win_rate(self.trades)
        
        # Average win/loss
        winning_pnls = [t['pnl'] for t in self.trades if t['pnl'] > 0]
        losing_pnls = [t['pnl'] for t in self.trades if t['pnl'] <= 0]
        
        avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0
        avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0
        
        # Profit factor
        gross_profit = sum(winning_pnls) if winning_pnls else 0
        gross_loss = abs(sum(losing_pnls)) if losing_pnls else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Risk metrics
        returns = [t['pnl'] / self.initial_balance for t in self.trades]
        sharpe_ratio = calculate_sharpe_ratio(returns)
        max_dd = calculate_max_drawdown(self.equity_curve)
        
        # Time metrics
        duration_days = (end_date - start_date).days
        avg_trade_duration = sum(t['duration'] for t in self.trades) / total_trades
        
        # Commission analysis
        total_commission = sum(t['commission'] for t in self.trades)
        
        return {
            'success': True,
            'summary': {
                'initial_balance': self.initial_balance,
                'final_balance': self.balance,
                'total_pnl': total_pnl,
                'total_return': total_return,
                'duration_days': duration_days
            },
            'trade_metrics': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate_data['win_rate'],
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'largest_win': max(winning_pnls) if winning_pnls else 0,
                'largest_loss': min(losing_pnls) if losing_pnls else 0
            },
            'performance_metrics': {
                'profit_factor': profit_factor,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_dd['max_drawdown'],
                'max_drawdown_percent': max_dd['max_drawdown_percent'],
                'recovery_factor': total_pnl / max_dd['max_drawdown'] if max_dd['max_drawdown'] > 0 else 0
            },
            'efficiency_metrics': {
                'avg_trade_duration_minutes': avg_trade_duration,
                'trades_per_day': total_trades / duration_days if duration_days > 0 else 0,
                'total_commission': total_commission,
                'commission_percent': (total_commission / self.initial_balance) * 100
            },
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }
    
    def plot_results(self, results: Dict[str, Any]):
        """
        Plot backtest results (requires matplotlib)
        
        Args:
            results: Backtest results dictionary
        """
        try:
            import matplotlib.pyplot as plt
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # Equity curve
            axes[0, 0].plot(results['equity_curve'])
            axes[0, 0].set_title('Equity Curve')
            axes[0, 0].set_xlabel('Trade Number')
            axes[0, 0].set_ylabel('Equity ($)')
            axes[0, 0].grid(True)
            
            # P&L distribution
            pnls = [t['pnl'] for t in results['trades']]
            axes[0, 1].hist(pnls, bins=30, edgecolor='black')
            axes[0, 1].set_title('P&L Distribution')
            axes[0, 1].set_xlabel('P&L ($)')
            axes[0, 1].set_ylabel('Frequency')
            axes[0, 1].grid(True)
            
            # Win/Loss ratio
            labels = ['Winning', 'Losing']
            sizes = [
                results['trade_metrics']['winning_trades'],
                results['trade_metrics']['losing_trades']
            ]
            axes[1, 0].pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            axes[1, 0].set_title('Win/Loss Distribution')
            
            # Trade durations
            durations = [t['duration'] for t in results['trades']]
            axes[1, 1].hist(durations, bins=30, edgecolor='black')
            axes[1, 1].set_title('Trade Duration Distribution')
            axes[1, 1].set_xlabel('Duration (minutes)')
            axes[1, 1].set_ylabel('Frequency')
            axes[1, 1].grid(True)
            
            plt.tight_layout()
            plt.savefig('backtest_results.png')
            print("Results saved to backtest_results.png")
            
        except ImportError:
            logger.warning("Matplotlib not installed. Skipping plot generation.")

# Example usage
if __name__ == "__main__":
    from backend.exchange.weex_client import WEEXClient
    
    # Initialize components
    client = WEEXClient(testnet=True)
    backtest = BacktestEngine(initial_balance=10000)
    
    # Fetch historical data
    historical_data = client.fetch_ohlcv('BTC/USDT:USDT', '5m', limit=1000)
    
    if historical_data:
        df = pd.DataFrame(
            historical_data,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Create strategy
        strategy = ScalpingStrategy(
            name="Test Strategy",
            symbol='BTC/USDT:USDT',
            timeframe='5m'
        )
        
        # Run backtest
        results = backtest.run(strategy, df)
        
        # Print results
        print("\n" + "="*60)
        print("BACKTEST RESULTS")
        print("="*60)
        print(f"Total Trades: {results['trade_metrics']['total_trades']}")
        print(f"Win Rate: {results['trade_metrics']['win_rate']:.2f}%")
        print(f"Total Return: {results['summary']['total_return']:.2f}%")
        print(f"Profit Factor: {results['performance_metrics']['profit_factor']:.2f}")
        print(f"Sharpe Ratio: {results['performance_metrics']['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {results['performance_metrics']['max_drawdown_percent']:.2f}%")
        print("="*60)
        
        # Plot results
        backtest.plot_results(results)
