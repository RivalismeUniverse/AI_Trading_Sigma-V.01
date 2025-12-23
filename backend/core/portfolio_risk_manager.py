"""
Portfolio Risk Manager - Correlation & Concentration Management
Prevents blow-ups from correlated positions and overconcentration
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PortfolioRiskManager:
    """
    Manages portfolio-level risk
    
    Features:
    - Real-time correlation calculation
    - Concentration limits
    - Sector/asset class exposure
    - Correlation-adjusted portfolio heat
    - Position limit enforcement
    """
    
    def __init__(self):
        # Concentration limits
        self.max_single_asset_pct = 0.40  # 40% max in one asset
        self.max_correlated_group_pct = 0.60  # 60% max in correlated assets
        self.max_sector_pct = 0.50  # 50% max in one sector
        
        # Correlation thresholds
        self.high_correlation_threshold = 0.7
        self.extreme_correlation_threshold = 0.85
        
        # Asset classifications
        self.asset_sectors = {
            'BTC/USDT:USDT': 'crypto_large_cap',
            'ETH/USDT:USDT': 'crypto_large_cap',
            'BNB/USDT:USDT': 'crypto_large_cap',
            'SOL/USDT:USDT': 'crypto_alt_l1',
            'ADA/USDT:USDT': 'crypto_alt_l1',
            'XRP/USDT:USDT': 'crypto_payment',
            'LTC/USDT:USDT': 'crypto_payment',
            'DOGE/USDT:USDT': 'crypto_meme'
        }
        
        # Known correlations (can be updated dynamically)
        self.correlation_matrix = {
            ('BTC/USDT:USDT', 'ETH/USDT:USDT'): 0.85,
            ('BTC/USDT:USDT', 'BNB/USDT:USDT'): 0.80,
            ('ETH/USDT:USDT', 'BNB/USDT:USDT'): 0.82,
            ('SOL/USDT:USDT', 'ADA/USDT:USDT'): 0.75,
            ('XRP/USDT:USDT', 'LTC/USDT:USDT'): 0.70,
        }
    
    def validate_new_position(
        self,
        new_symbol: str,
        new_size: float,
        new_entry_price: float,
        open_positions: List[Dict],
        balance: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if new position passes portfolio risk checks
        
        Returns:
            (is_valid, error_message)
        """
        # Calculate new position value
        new_position_value = new_size * new_entry_price
        
        # Check single asset concentration
        is_valid, error = self._check_single_asset_concentration(
            new_symbol, new_position_value, open_positions, balance
        )
        if not is_valid:
            return False, error
        
        # Check correlated group concentration
        is_valid, error = self._check_correlated_group_concentration(
            new_symbol, new_position_value, open_positions, balance
        )
        if not is_valid:
            return False, error
        
        # Check sector concentration
        is_valid, error = self._check_sector_concentration(
            new_symbol, new_position_value, open_positions, balance
        )
        if not is_valid:
            return False, error
        
        return True, None
    
    def _check_single_asset_concentration(
        self,
        new_symbol: str,
        new_value: float,
        open_positions: List[Dict],
        balance: float
    ) -> Tuple[bool, Optional[str]]:
        """Check if single asset concentration is within limits"""
        # Get current exposure to this symbol
        current_exposure = sum(
            p['position_size'] * p['entry_price']
            for p in open_positions
            if p.get('symbol') == new_symbol
        )
        
        total_exposure = current_exposure + new_value
        concentration_pct = (total_exposure / balance) * 100
        
        if concentration_pct > self.max_single_asset_pct * 100:
            return False, (
                f"Single asset concentration too high: {concentration_pct:.1f}% "
                f"(max {self.max_single_asset_pct * 100:.0f}%)"
            )
        
        return True, None
    
    def _check_correlated_group_concentration(
        self,
        new_symbol: str,
        new_value: float,
        open_positions: List[Dict],
        balance: float
    ) -> Tuple[bool, Optional[str]]:
        """Check if correlated group concentration is within limits"""
        # Find highly correlated symbols
        correlated_symbols = self._get_highly_correlated_symbols(new_symbol)
        
        # Calculate total exposure to correlated group
        correlated_exposure = new_value
        
        for position in open_positions:
            symbol = position.get('symbol')
            if symbol in correlated_symbols:
                position_value = position['position_size'] * position['entry_price']
                correlated_exposure += position_value
        
        concentration_pct = (correlated_exposure / balance) * 100
        
        if concentration_pct > self.max_correlated_group_pct * 100:
            return False, (
                f"Correlated group concentration too high: {concentration_pct:.1f}% "
                f"(max {self.max_correlated_group_pct * 100:.0f}%) "
                f"Correlated with: {correlated_symbols}"
            )
        
        return True, None
    
    def _check_sector_concentration(
        self,
        new_symbol: str,
        new_value: float,
        open_positions: List[Dict],
        balance: float
    ) -> Tuple[bool, Optional[str]]:
        """Check if sector concentration is within limits"""
        new_sector = self.asset_sectors.get(new_symbol, 'unknown')
        
        # Calculate total exposure to this sector
        sector_exposure = new_value
        
        for position in open_positions:
            symbol = position.get('symbol')
            if self.asset_sectors.get(symbol) == new_sector:
                position_value = position['position_size'] * position['entry_price']
                sector_exposure += position_value
        
        concentration_pct = (sector_exposure / balance) * 100
        
        if concentration_pct > self.max_sector_pct * 100:
            return False, (
                f"Sector '{new_sector}' concentration too high: {concentration_pct:.1f}% "
                f"(max {self.max_sector_pct * 100:.0f}%)"
            )
        
        return True, None
    
    def _get_highly_correlated_symbols(
        self,
        symbol: str,
        threshold: float = None
    ) -> List[str]:
        """Get list of symbols highly correlated with given symbol"""
        if threshold is None:
            threshold = self.high_correlation_threshold
        
        correlated = []
        
        for (sym1, sym2), corr in self.correlation_matrix.items():
            if corr >= threshold:
                if sym1 == symbol:
                    correlated.append(sym2)
                elif sym2 == symbol:
                    correlated.append(sym1)
        
        return correlated
    
    def calculate_correlation_adjusted_heat(
        self,
        open_positions: List[Dict],
        balance: float
    ) -> Dict:
        """
        Calculate portfolio heat adjusted for correlation
        
        Returns:
            {
                'simple_heat': float,
                'correlation_adjusted_heat': float,
                'heat_multiplier': float
            }
        """
        if not open_positions:
            return {
                'simple_heat': 0.0,
                'correlation_adjusted_heat': 0.0,
                'heat_multiplier': 1.0
            }
        
        # Simple heat (sum of individual risks)
        total_risk = 0.0
        for position in open_positions:
            entry_price = position.get('entry_price', 0)
            stop_loss = position.get('stop_loss', entry_price)
            size = position.get('position_size', 0)
            
            risk_per_unit = abs(entry_price - stop_loss)
            position_risk = risk_per_unit * size
            total_risk += position_risk
        
        simple_heat = (total_risk / balance) * 100 if balance > 0 else 0
        
        # Correlation adjustment
        heat_multiplier = self._calculate_correlation_multiplier(open_positions)
        correlation_adjusted_heat = simple_heat * heat_multiplier
        
        return {
            'simple_heat': simple_heat,
            'correlation_adjusted_heat': correlation_adjusted_heat,
            'heat_multiplier': heat_multiplier
        }
    
    def _calculate_correlation_multiplier(
        self,
        open_positions: List[Dict]
    ) -> float:
        """
        Calculate correlation multiplier for portfolio heat
        
        Higher correlation = higher multiplier (more risk)
        """
        if len(open_positions) <= 1:
            return 1.0
        
        symbols = [p.get('symbol') for p in open_positions]
        
        # Calculate average pairwise correlation
        correlations = []
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                corr = self._get_correlation(sym1, sym2)
                correlations.append(corr)
        
        if not correlations:
            return 1.0
        
        avg_correlation = np.mean(correlations)
        
        # Convert correlation to risk multiplier
        # 0.0 correlation = 1.0x (no adjustment)
        # 0.5 correlation = 1.25x
        # 0.8 correlation = 1.6x
        # 1.0 correlation = 2.0x (double risk)
        multiplier = 1.0 + avg_correlation
        
        logger.debug(f"Correlation multiplier: {multiplier:.2f} (avg_corr={avg_correlation:.2f})")
        
        return multiplier
    
    def _get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two symbols"""
        # Try both orders
        corr = self.correlation_matrix.get((symbol1, symbol2))
        if corr is None:
            corr = self.correlation_matrix.get((symbol2, symbol1))
        
        # Default to moderate correlation if not found
        return corr if corr is not None else 0.5
    
    def get_portfolio_exposure_breakdown(
        self,
        open_positions: List[Dict],
        balance: float
    ) -> Dict:
        """
        Get detailed portfolio exposure breakdown
        
        Returns comprehensive exposure analytics
        """
        if not open_positions:
            return {
                'total_positions': 0,
                'message': 'No open positions'
            }
        
        # By symbol
        symbol_exposure = {}
        for position in open_positions:
            symbol = position.get('symbol')
            value = position['position_size'] * position['entry_price']
            
            if symbol not in symbol_exposure:
                symbol_exposure[symbol] = 0
            symbol_exposure[symbol] += value
        
        # By sector
        sector_exposure = {}
        for symbol, value in symbol_exposure.items():
            sector = self.asset_sectors.get(symbol, 'unknown')
            if sector not in sector_exposure:
                sector_exposure[sector] = 0
            sector_exposure[sector] += value
        
        # By side
        long_exposure = sum(
            p['position_size'] * p['entry_price']
            for p in open_positions
            if p.get('side') == 'ENTER_LONG'
        )
        short_exposure = sum(
            p['position_size'] * p['entry_price']
            for p in open_positions
            if p.get('side') == 'ENTER_SHORT'
        )
        
        # Convert to percentages
        symbol_pct = {
            sym: (val / balance) * 100
            for sym, val in symbol_exposure.items()
        }
        sector_pct = {
            sec: (val / balance) * 100
            for sec, val in sector_exposure.items()
        }
        
        # Correlation metrics
        heat_metrics = self.calculate_correlation_adjusted_heat(open_positions, balance)
        
        return {
            'total_positions': len(open_positions),
            'total_exposure': sum(symbol_exposure.values()),
            'total_exposure_pct': (sum(symbol_exposure.values()) / balance) * 100,
            'symbol_exposure': symbol_exposure,
            'symbol_exposure_pct': symbol_pct,
            'sector_exposure': sector_exposure,
            'sector_exposure_pct': sector_pct,
            'long_exposure': long_exposure,
            'short_exposure': short_exposure,
            'long_exposure_pct': (long_exposure / balance) * 100 if balance > 0 else 0,
            'short_exposure_pct': (short_exposure / balance) * 100 if balance > 0 else 0,
            'net_exposure': long_exposure - short_exposure,
            'net_exposure_pct': ((long_exposure - short_exposure) / balance) * 100 if balance > 0 else 0,
            'correlation_metrics': heat_metrics
        }
    
    def should_hedge_portfolio(
        self,
        open_positions: List[Dict],
        balance: float,
        current_drawdown_pct: float
    ) -> Tuple[bool, str]:
        """
        Determine if portfolio should be hedged
        
        Returns:
            (should_hedge, reason)
        """
        exposure = self.get_portfolio_exposure_breakdown(open_positions, balance)
        
        # Hedge if highly concentrated
        if exposure['total_exposure_pct'] > 80:
            return True, f"high_exposure_{exposure['total_exposure_pct']:.0f}%"
        
        # Hedge if highly correlated and exposed
        corr_heat = exposure['correlation_metrics']['correlation_adjusted_heat']
        if corr_heat > 20:
            return True, f"high_correlation_risk_{corr_heat:.0f}%"
        
        # Hedge if in drawdown with exposure
        if current_drawdown_pct < -5 and exposure['total_exposure_pct'] > 40:
            return True, f"drawdown_{current_drawdown_pct:.1f}%_with_exposure"
        
        # Hedge if one-sided and heavily exposed
        net_exposure_abs = abs(exposure['net_exposure_pct'])
        if net_exposure_abs > 50:
            side = "long" if exposure['net_exposure_pct'] > 0 else "short"
            return True, f"one_sided_{side}_{net_exposure_abs:.0f}%"
        
        return False, "no_hedge_needed"


__all__ = ['PortfolioRiskManager']
