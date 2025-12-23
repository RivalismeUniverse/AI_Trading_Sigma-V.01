"""
Strategy Monitor - Performance Degradation Detection
Detects when strategy stops working BEFORE disaster strikes
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class DegradationReport:
    """Report of strategy degradation metrics"""
    is_degraded: bool
    severity: str  # 'none', 'minor', 'moderate', 'severe', 'critical'
    issues: List[str]
    metrics: Dict
    recommendation: str


class StrategyMonitor:
    """
    Monitors strategy performance for degradation
    
    Detects:
    - Win rate collapse
    - Sharpe ratio degradation
    - Expectancy turning negative
    - Maximum consecutive losses
    - Regime mismatch
    """
    
    def __init__(self):
        # Thresholds for degradation
        self.min_win_rate = 0.45  # Below 45% is concern
        self.critical_win_rate = 0.35  # Below 35% is critical
        
        self.min_sharpe = 0.5  # Below 0.5 is concern
        self.critical_sharpe = 0.0  # Below 0 is critical
        
        self.max_consecutive_losses = 7
        self.critical_consecutive_losses = 10
        
        self.min_sample_size = 20  # Need at least 20 trades to evaluate
    
    def check_degradation(
        self,
        recent_trades: List[Dict],
        timeframe_minutes: int = 60
    ) -> DegradationReport:
        """
        Check if strategy is degrading
        
        Args:
            recent_trades: Recent closed trades
            timeframe_minutes: Timeframe to analyze
            
        Returns:
            DegradationReport with findings
        """
        if len(recent_trades) < self.min_sample_size:
            return DegradationReport(
                is_degraded=False,
                severity='none',
                issues=[],
                metrics={},
                recommendation=f"Insufficient data ({len(recent_trades)} < {self.min_sample_size} trades)"
            )
        
        # Filter trades by timeframe
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeframe_minutes)
        trades_in_window = [
            t for t in recent_trades
            if t.get('exit_time') and 
            (isinstance(t['exit_time'], datetime) and t['exit_time'] > cutoff_time or
             isinstance(t['exit_time'], str) and datetime.fromisoformat(t['exit_time'].replace('Z', '+00:00')) > cutoff_time)
        ]
        
        if len(trades_in_window) < self.min_sample_size:
            trades_to_analyze = recent_trades[-self.min_sample_size:]
        else:
            trades_to_analyze = trades_in_window
        
        # Analyze metrics
        issues = []
        metrics = {}
        
        # 1. Win Rate Check
        win_rate_issue = self._check_win_rate(trades_to_analyze, metrics)
        if win_rate_issue:
            issues.append(win_rate_issue)
        
        # 2. Sharpe Ratio Check
        sharpe_issue = self._check_sharpe_ratio(trades_to_analyze, metrics)
        if sharpe_issue:
            issues.append(sharpe_issue)
        
        # 3. Expectancy Check
        expectancy_issue = self._check_expectancy(trades_to_analyze, metrics)
        if expectancy_issue:
            issues.append(expectancy_issue)
        
        # 4. Consecutive Losses Check
        consec_issue = self._check_consecutive_losses(recent_trades, metrics)
        if consec_issue:
            issues.append(consec_issue)
        
        # 5. Drawdown Check
        drawdown_issue = self._check_drawdown(trades_to_analyze, metrics)
        if drawdown_issue:
            issues.append(drawdown_issue)
        
        # Determine severity
        severity = self._determine_severity(issues, metrics)
        is_degraded = severity not in ['none', 'minor']
        
        # Generate recommendation
        recommendation = self._generate_recommendation(severity, issues)
        
        report = DegradationReport(
            is_degraded=is_degraded,
            severity=severity,
            issues=issues,
            metrics=metrics,
            recommendation=recommendation
        )
        
        if is_degraded:
            logger.warning(f"Strategy degradation detected: {severity} - {issues}")
        
        return report
    
    def _check_win_rate(self, trades: List[Dict], metrics: Dict) -> Optional[str]:
        """Check if win rate is degrading"""
        winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
        win_rate = winning_trades / len(trades) if trades else 0
        
        metrics['win_rate'] = win_rate
        metrics['winning_trades'] = winning_trades
        metrics['total_trades'] = len(trades)
        
        if win_rate < self.critical_win_rate:
            return f"critical_win_rate_{win_rate:.1%}_below_{self.critical_win_rate:.0%}"
        elif win_rate < self.min_win_rate:
            return f"low_win_rate_{win_rate:.1%}_below_{self.min_win_rate:.0%}"
        
        return None
    
    def _check_sharpe_ratio(self, trades: List[Dict], metrics: Dict) -> Optional[str]:
        """Check if Sharpe ratio is degrading"""
        pnls = [t.get('pnl', 0) for t in trades if 'pnl' in t]
        
        if len(pnls) < 5:
            return None
        
        returns = np.array(pnls)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            sharpe = 0
        else:
            sharpe = (mean_return / std_return) * np.sqrt(252)  # Annualized
        
        metrics['sharpe_ratio'] = sharpe
        metrics['mean_return'] = mean_return
        metrics['std_return'] = std_return
        
        if sharpe < self.critical_sharpe:
            return f"critical_sharpe_{sharpe:.2f}_negative"
        elif sharpe < self.min_sharpe:
            return f"low_sharpe_{sharpe:.2f}_below_{self.min_sharpe:.1f}"
        
        return None
    
    def _check_expectancy(self, trades: List[Dict], metrics: Dict) -> Optional[str]:
        """Check if expectancy is negative"""
        pnls = [t.get('pnl', 0) for t in trades if 'pnl' in t]
        
        if not pnls:
            return None
        
        winning_pnls = [p for p in pnls if p > 0]
        losing_pnls = [p for p in pnls if p < 0]
        
        win_rate = len(winning_pnls) / len(pnls) if pnls else 0
        avg_win = np.mean(winning_pnls) if winning_pnls else 0
        avg_loss = abs(np.mean(losing_pnls)) if losing_pnls else 0
        
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        metrics['expectancy'] = expectancy
        metrics['avg_win'] = avg_win
        metrics['avg_loss'] = avg_loss
        
        if expectancy < -10:
            return f"negative_expectancy_{expectancy:.2f}_critical"
        elif expectancy < 0:
            return f"negative_expectancy_{expectancy:.2f}"
        
        return None
    
    def _check_consecutive_losses(self, trades: List[Dict], metrics: Dict) -> Optional[str]:
        """Check for consecutive losses"""
        # Sort by exit time (most recent last)
        sorted_trades = sorted(
            trades,
            key=lambda t: t.get('exit_time', datetime.min) if isinstance(t.get('exit_time'), datetime) 
            else datetime.fromisoformat(t.get('exit_time', '2000-01-01').replace('Z', '+00:00'))
        )
        
        # Count consecutive losses from end
        consecutive_losses = 0
        for trade in reversed(sorted_trades):
            if trade.get('pnl', 0) < 0:
                consecutive_losses += 1
            else:
                break
        
        metrics['consecutive_losses'] = consecutive_losses
        
        if consecutive_losses >= self.critical_consecutive_losses:
            return f"critical_consecutive_losses_{consecutive_losses}"
        elif consecutive_losses >= self.max_consecutive_losses:
            return f"high_consecutive_losses_{consecutive_losses}"
        
        return None
    
    def _check_drawdown(self, trades: List[Dict], metrics: Dict) -> Optional[str]:
        """Check current drawdown"""
        pnls = [t.get('pnl', 0) for t in trades if 'pnl' in t]
        
        if not pnls:
            return None
        
        cumulative = np.cumsum(pnls)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        
        current_drawdown = drawdown[-1] if len(drawdown) > 0 else 0
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        
        # Calculate as percentage of peak
        peak = running_max[-1] if len(running_max) > 0 else 0
        current_dd_pct = (current_drawdown / peak * 100) if peak > 0 else 0
        max_dd_pct = (max_drawdown / peak * 100) if peak > 0 else 0
        
        metrics['current_drawdown'] = current_drawdown
        metrics['current_drawdown_pct'] = current_dd_pct
        metrics['max_drawdown'] = max_drawdown
        metrics['max_drawdown_pct'] = max_dd_pct
        
        if current_dd_pct < -15:
            return f"critical_drawdown_{current_dd_pct:.1f}%"
        elif current_dd_pct < -8:
            return f"high_drawdown_{current_dd_pct:.1f}%"
        
        return None
    
    def _determine_severity(self, issues: List[str], metrics: Dict) -> str:
        """Determine overall severity level"""
        if not issues:
            return 'none'
        
        # Count critical issues
        critical_count = sum(1 for issue in issues if 'critical' in issue)
        
        if critical_count >= 2:
            return 'critical'
        elif critical_count == 1:
            return 'severe'
        elif len(issues) >= 3:
            return 'moderate'
        else:
            return 'minor'
    
    def _generate_recommendation(self, severity: str, issues: List[str]) -> str:
        """Generate action recommendation"""
        recommendations = {
            'none': "Strategy performing normally. Continue monitoring.",
            'minor': "Minor performance issues detected. Monitor closely and consider parameter adjustment.",
            'moderate': "Moderate degradation detected. Reduce position sizes by 50% and review strategy logic.",
            'severe': "Severe degradation detected. HALT new entries. Close positions at favorable prices. Review strategy immediately.",
            'critical': "CRITICAL degradation. EMERGENCY HALT. Close all positions. Strategy requires complete overhaul."
        }
        
        return recommendations.get(severity, "Unknown severity level")
    
    def detect_regime_mismatch(
        self,
        recent_trades: List[Dict],
        current_regime: str,
        strategy_preferred_regime: str
    ) -> Dict:
        """
        Detect if strategy is being used in wrong regime
        
        Args:
            recent_trades: Recent trades
            current_regime: Current market regime
            strategy_preferred_regime: Strategy's optimal regime
            
        Returns:
            {
                'is_mismatch': bool,
                'performance_in_regime': float,
                'recommendation': str
            }
        """
        # Filter trades in current regime (simplified - would need regime history)
        # For now, use recent trades as proxy
        recent_pnls = [t.get('pnl', 0) for t in recent_trades[-10:] if 'pnl' in t]
        
        if not recent_pnls:
            return {
                'is_mismatch': False,
                'performance_in_regime': 0,
                'recommendation': 'insufficient_data'
            }
        
        avg_pnl = np.mean(recent_pnls)
        win_rate = sum(1 for p in recent_pnls if p > 0) / len(recent_pnls)
        
        # Check if performance is poor AND regime doesn't match
        is_mismatch = (
            avg_pnl < 0 and 
            win_rate < 0.4 and 
            current_regime != strategy_preferred_regime
        )
        
        if is_mismatch:
            recommendation = (
                f"Strategy optimized for {strategy_preferred_regime} but market is {current_regime}. "
                f"Consider pausing or switching strategy."
            )
        else:
            recommendation = "Regime match acceptable"
        
        return {
            'is_mismatch': is_mismatch,
            'current_regime': current_regime,
            'preferred_regime': strategy_preferred_regime,
            'performance_in_regime': avg_pnl,
            'win_rate_in_regime': win_rate,
            'recommendation': recommendation
        }


__all__ = ['StrategyMonitor', 'DegradationReport']
