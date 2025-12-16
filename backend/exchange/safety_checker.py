"""
Safety Checker - Hackathon Compliance Enforcement
Multi-layer validation system for all trading operations
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from config import settings
from utils.constants import ALLOWED_SYMBOLS, MAX_ALLOWED_LEVERAGE
from utils.logger import setup_logger, compliance_logger

logger = setup_logger(__name__)


class SafetyChecker:
    """
    Military-grade safety system for hackathon compliance
    Every trade passes through 5 validation layers
    """
    
    def __init__(self):
        self.allowed_symbols = ALLOWED_SYMBOLS
        self.max_leverage = MAX_ALLOWED_LEVERAGE
        self.daily_trades = []
        self.daily_pnl = 0.0
        self.violations = []
    
    def validate_trade(
        self,
        symbol: str,
        side: str,
        amount: float,
        leverage: int,
        price: float,
        account_balance: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Master validation function - all checks in one place
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            amount: Position size
            leverage: Leverage used
            price: Current price
            account_balance: Current account balance
            
        Returns:
            (is_valid, error_message)
        """
        
        # Layer 1: Symbol Validation
        valid, error = self._check_symbol(symbol)
        if not valid:
            self._log_violation("symbol_check", symbol, error)
            return False, error
        
        # Layer 2: Leverage Check
        valid, error = self._check_leverage(leverage)
        if not valid:
            self._log_violation("leverage_check", symbol, error)
            return False, error
        
        # Layer 3: Position Size Check
        valid, error = self._check_position_size(amount, price, account_balance)
        if not valid:
            self._log_violation("position_size_check", symbol, error)
            return False, error
        
        # Layer 4: Risk Management Check
        valid, error = self._check_risk_limits(amount, price, account_balance, leverage)
        if not valid:
            self._log_violation("risk_check", symbol, error)
            return False, error
        
        # Layer 5: Daily Loss Limit Check
        valid, error = self._check_daily_loss_limit(account_balance)
        if not valid:
            self._log_violation("daily_loss_check", symbol, error)
            return False, error
        
        # All checks passed
        logger.info(f"✅ Trade validated: {side} {amount} {symbol} @ {leverage}x")
        return True, None
    
    def _check_symbol(self, symbol: str) -> Tuple[bool, Optional[str]]:
        """Layer 1: Validate symbol is in allowed list"""
        if symbol not in self.allowed_symbols:
            error = f"Symbol {symbol} not in allowed list. Must be one of: {self.allowed_symbols}"
            logger.warning(error)
            return False, error
        return True, None
    
    def _check_leverage(self, leverage: int) -> Tuple[bool, Optional[str]]:
        """Layer 2: Validate leverage doesn't exceed maximum"""
        if leverage > self.max_leverage:
            error = f"Leverage {leverage}x exceeds maximum allowed {self.max_leverage}x"
            logger.warning(error)
            return False, error
        return True, None
    
    def _check_position_size(
        self,
        amount: float,
        price: float,
        account_balance: float
    ) -> Tuple[bool, Optional[str]]:
        """Layer 3: Validate position size is reasonable"""
        position_value = amount * price
        max_position_value = account_balance * 0.1  # 10% max per position
        
        if position_value > max_position_value:
            error = f"Position size too large: ${position_value:.2f} > ${max_position_value:.2f} (10% of balance)"
            logger.warning(error)
            return False, error
        
        if amount <= 0:
            error = f"Invalid position size: {amount}"
            logger.warning(error)
            return False, error
        
        return True, None
    
    def _check_risk_limits(
        self,
        amount: float,
        price: float,
        account_balance: float,
        leverage: int
    ) -> Tuple[bool, Optional[str]]:
        """Layer 4: Validate risk per trade"""
        position_value = amount * price
        leveraged_value = position_value * leverage
        
        # Check if we have enough balance
        required_margin = position_value / leverage
        if required_margin > account_balance:
            error = f"Insufficient balance: required ${required_margin:.2f}, available ${account_balance:.2f}"
            logger.warning(error)
            return False, error
        
        # Check max risk per trade (default 2%)
        max_risk = account_balance * settings.MAX_RISK_PER_TRADE
        if position_value > max_risk * 10:  # Conservative check
            error = f"Position risk too high"
            logger.warning(error)
            return False, error
        
        return True, None
    
    def _check_daily_loss_limit(self, account_balance: float) -> Tuple[bool, Optional[str]]:
        """Layer 5: Check daily loss limit"""
        # Clean up old trades (older than 24 hours)
        self._cleanup_daily_trades()
        
        # Calculate daily P&L
        daily_loss = abs(min(self.daily_pnl, 0))
        max_daily_loss = account_balance * settings.MAX_DAILY_LOSS
        
        if daily_loss >= max_daily_loss:
            error = f"Daily loss limit reached: ${daily_loss:.2f} >= ${max_daily_loss:.2f} ({settings.MAX_DAILY_LOSS*100}%)"
            logger.warning(error)
            return False, error
        
        return True, None
    
    def record_trade(self, trade_data: Dict):
        """Record trade for daily tracking"""
        trade_data['timestamp'] = datetime.utcnow()
        self.daily_trades.append(trade_data)
        
        # Update daily P&L
        if 'pnl' in trade_data:
            self.daily_pnl += trade_data['pnl']
    
    def _cleanup_daily_trades(self):
        """Remove trades older than 24 hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Recalculate daily P&L
        self.daily_pnl = 0.0
        new_trades = []
        
        for trade in self.daily_trades:
            if trade['timestamp'] > cutoff_time:
                new_trades.append(trade)
                if 'pnl' in trade:
                    self.daily_pnl += trade['pnl']
        
        self.daily_trades = new_trades
    
    def _log_violation(self, check_type: str, symbol: str, reason: str):
        """Log safety violation for compliance"""
        violation = {
            "check_type": check_type,
            "symbol": symbol,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.violations.append(violation)
        compliance_logger.log_safety_violation(violation)
        
        logger.error(f"❌ Safety violation: {check_type} - {reason}")
    
    def get_daily_stats(self) -> Dict:
        """Get daily trading statistics"""
        self._cleanup_daily_trades()
        
        return {
            "total_trades": len(self.daily_trades),
            "daily_pnl": self.daily_pnl,
            "violations": len(self.violations),
            "last_reset": (datetime.utcnow() - timedelta(hours=24)).isoformat()
        }
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at midnight UTC)"""
        logger.info("Resetting daily statistics")
        self.daily_trades = []
        self.daily_pnl = 0.0
    
    def validate_strategy_parameters(self, strategy: Dict) -> Tuple[bool, Optional[str]]:
        """Validate strategy parameters before applying"""
        
        # Check leverage
        leverage = strategy.get('leverage', 1)
        if leverage > self.max_leverage:
            return False, f"Strategy leverage {leverage}x exceeds maximum {self.max_leverage}x"
        
        # Check symbols
        symbols = strategy.get('symbols', [])
        for symbol in symbols:
            if symbol not in self.allowed_symbols:
                return False, f"Strategy contains invalid symbol: {symbol}"
        
        # Check risk parameters
        risk_per_trade = strategy.get('risk_per_trade', 0)
        if risk_per_trade > settings.MAX_RISK_PER_TRADE:
            return False, f"Strategy risk per trade {risk_per_trade} exceeds maximum {settings.MAX_RISK_PER_TRADE}"
        
        return True, None
    
    def get_compliance_report(self) -> Dict:
        """Generate compliance report for hackathon"""
        self._cleanup_daily_trades()
        
        return {
            "allowed_symbols": self.allowed_symbols,
            "max_leverage": self.max_leverage,
            "total_trades": len(self.daily_trades),
            "total_violations": len(self.violations),
            "daily_pnl": self.daily_pnl,
            "compliance_rate": (1 - len(self.violations) / max(len(self.daily_trades), 1)) * 100,
            "violations": self.violations[-10:],  # Last 10 violations
            "generated_at": datetime.utcnow().isoformat()
        }


# Singleton instance
_safety_checker_instance = None


def get_safety_checker() -> SafetyChecker:
    """Get or create safety checker singleton"""
    global _safety_checker_instance
    if _safety_checker_instance is None:
        _safety_checker_instance = SafetyChecker()
    return _safety_checker_instance


# Export
__all__ = ['SafetyChecker', 'get_safety_checker']
