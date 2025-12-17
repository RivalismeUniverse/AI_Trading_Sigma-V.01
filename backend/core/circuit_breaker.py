"""
Circuit Breaker System - Production Safety Layer
4-Level graduated circuit breaker for trading engine protection

Level 1: ALERT     - Warning, continue trading
Level 2: THROTTLE  - Reduce activity, cautious mode
Level 3: HALT      - Emergency stop, close positions
Level 4: SHUTDOWN  - Fatal error, kill engine

Integrated with notification system for real-time alerts

Author: AI Trading SIGMA
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
import asyncio

from utils.logger import setup_logger, compliance_logger
from utils.constants import TradeAction

logger = setup_logger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    ALERT = "alert"          # Level 1: Warning
    THROTTLE = "throttle"    # Level 2: Reduced operation
    HALT = "halt"            # Level 3: Emergency stop
    SHUTDOWN = "shutdown"    # Level 4: Fatal shutdown


class IssueType(str, Enum):
    """Types of issues that can trigger circuit breaker"""
    API_LATENCY = "api_latency"
    ORDER_FAILURE = "order_failure"
    SLIPPAGE = "slippage"
    EXCHANGE_ERROR = "exchange_error"
    NETWORK_ERROR = "network_error"
    DATABASE_ERROR = "database_error"
    BALANCE_MISMATCH = "balance_mismatch"
    UNEXPECTED_LOSS = "unexpected_loss"
    RATE_LIMIT = "rate_limit"
    MEMORY_ERROR = "memory_error"
    SECURITY_BREACH = "security_breach"


@dataclass
class CircuitConfig:
    """Configuration for circuit breaker thresholds"""
    
    # Alert thresholds (Level 1)
    alert_api_latency_ms: float = 500.0
    alert_slippage_pct: float = 0.1
    alert_consecutive_failures: int = 2
    
    # Throttle thresholds (Level 2)
    throttle_api_latency_ms: float = 1000.0
    throttle_slippage_pct: float = 0.3
    throttle_consecutive_failures: int = 3
    throttle_failure_rate: float = 0.3  # 30% failure rate
    
    # Halt thresholds (Level 3)
    halt_api_latency_ms: float = 3000.0
    halt_slippage_pct: float = 0.5
    halt_consecutive_failures: int = 5
    halt_loss_pct: float = 0.05  # 5% loss in short time
    
    # Shutdown triggers (Level 4)
    shutdown_consecutive_failures: int = 10
    shutdown_critical_errors: List[IssueType] = field(default_factory=lambda: [
        IssueType.MEMORY_ERROR,
        IssueType.SECURITY_BREACH
    ])
    
    # Recovery settings
    alert_cooldown_seconds: int = 60
    throttle_cooldown_seconds: int = 300  # 5 minutes
    halt_cooldown_seconds: int = 900      # 15 minutes
    
    # Monitoring window
    monitoring_window_seconds: int = 300  # 5 minutes


@dataclass
class IssueRecord:
    """Record of an issue"""
    timestamp: datetime
    issue_type: IssueType
    severity: CircuitState
    details: Dict
    resolved: bool = False


class CircuitBreaker:
    """
    Production-grade circuit breaker for trading engine
    Monitors system health and protects against failures
    """
    
    def __init__(self, config: Optional[CircuitConfig] = None):
        self.config = config or CircuitConfig()
        self.state = CircuitState.CLOSED
        self.issues: List[IssueRecord] = []
        
        # Metrics tracking
        self.api_latencies: List[float] = []
        self.order_failures: List[datetime] = []
        self.slippages: List[float] = []
        self.last_state_change = datetime.utcnow()
        
        # Consecutive failure counter
        self.consecutive_failures = 0
        self.last_success_time = datetime.utcnow()
        
        # Callbacks for notifications
        self.alert_callbacks: List[Callable] = []
        self.halt_callbacks: List[Callable] = []
        self.shutdown_callbacks: List[Callable] = []
        
        # Register default notification callback
        self._setup_notifications()
        
        # State flags
        self.is_shutting_down = False
        self.manual_override = False
        
        logger.info("Circuit breaker initialized with notification system")
    
    def _setup_notifications(self):
        """Setup notification callbacks"""
        from core.notification_system import notification_system, NotificationPriority
        
        async def send_alert_notification(issue: IssueRecord):
            await notification_system.send_alert(issue, NotificationPriority.WARNING)
        
        async def send_halt_notification(issue: IssueRecord):
            await notification_system.send_alert(issue, NotificationPriority.CRITICAL)
        
        async def send_shutdown_notification(issue: IssueRecord):
            await notification_system.send_alert(issue, NotificationPriority.EMERGENCY)
        
        self.register_alert_callback(lambda issue: asyncio.create_task(send_alert_notification(issue)))
        self.register_halt_callback(lambda issue: asyncio.create_task(send_halt_notification(issue)))
        self.register_shutdown_callback(lambda issue: asyncio.create_task(send_shutdown_notification(issue)))
    
    # ========================================================================
    # MAIN CHECK FUNCTION
    # ========================================================================
    
    def check_execution_allowed(self, action: TradeAction) -> tuple[bool, str]:
        """
        Check if trade execution is allowed
        
        Returns:
            (allowed: bool, reason: str)
        """
        
        # Always block if shutting down
        if self.is_shutting_down:
            return False, "system_shutdown"
        
        # Manual override check
        if self.manual_override:
            return False, "manual_override_active"
        
        # State-based checks
        if self.state == CircuitState.SHUTDOWN:
            return False, "circuit_shutdown"
        
        elif self.state == CircuitState.HALT:
            # Only allow closing positions
            if action in [TradeAction.EXIT_LONG, TradeAction.EXIT_SHORT]:
                return True, "exit_allowed_during_halt"
            return False, "circuit_halted"
        
        elif self.state == CircuitState.THROTTLE:
            # More restrictive - only high confidence trades
            return True, "throttled_mode_active"  # Engine should check confidence
        
        elif self.state == CircuitState.ALERT:
            # Warning mode - allow but log
            logger.warning("Trading in ALERT mode - exercise caution")
            return True, "alert_mode_active"
        
        else:  # CLOSED - normal operation
            return True, "normal_operation"
    
    # ========================================================================
    # ISSUE REPORTING
    # ========================================================================
    
    def report_api_latency(self, latency_ms: float):
        """Report API call latency"""
        self.api_latencies.append(latency_ms)
        
        # Keep only recent measurements
        self._cleanup_old_metrics()
        
        # Check thresholds
        avg_latency = sum(self.api_latencies[-10:]) / len(self.api_latencies[-10:])
        
        if avg_latency > self.config.halt_api_latency_ms:
            self._escalate_to_halt(IssueType.API_LATENCY, {
                'average_latency_ms': avg_latency,
                'threshold_ms': self.config.halt_api_latency_ms
            })
        elif avg_latency > self.config.throttle_api_latency_ms:
            self._escalate_to_throttle(IssueType.API_LATENCY, {
                'average_latency_ms': avg_latency
            })
        elif avg_latency > self.config.alert_api_latency_ms:
            self._escalate_to_alert(IssueType.API_LATENCY, {
                'average_latency_ms': avg_latency
            })
    
    def report_order_failure(self, error_details: Dict):
        """Report order execution failure"""
        self.order_failures.append(datetime.utcnow())
        self.consecutive_failures += 1
        
        self._cleanup_old_metrics()
        
        logger.error(f"Order failure #{self.consecutive_failures}: {error_details}")
        
        # Check consecutive failures
        if self.consecutive_failures >= self.config.shutdown_consecutive_failures:
            self._escalate_to_shutdown(IssueType.ORDER_FAILURE, {
                'consecutive_failures': self.consecutive_failures,
                'error': error_details
            })
        elif self.consecutive_failures >= self.config.halt_consecutive_failures:
            self._escalate_to_halt(IssueType.ORDER_FAILURE, {
                'consecutive_failures': self.consecutive_failures
            })
        elif self.consecutive_failures >= self.config.throttle_consecutive_failures:
            self._escalate_to_throttle(IssueType.ORDER_FAILURE, {
                'consecutive_failures': self.consecutive_failures
            })
        elif self.consecutive_failures >= self.config.alert_consecutive_failures:
            self._escalate_to_alert(IssueType.ORDER_FAILURE, {
                'consecutive_failures': self.consecutive_failures
            })
    
    def report_order_success(self):
        """Report successful order execution"""
        self.consecutive_failures = 0
        self.last_success_time = datetime.utcnow()
        
        # Try to recover from lower states
        if self.state in [CircuitState.ALERT, CircuitState.THROTTLE]:
            self._attempt_recovery()
    
    def report_slippage(self, expected_price: float, actual_price: float):
        """Report price slippage"""
        slippage_pct = abs(actual_price - expected_price) / expected_price
        self.slippages.append(slippage_pct)
        
        self._cleanup_old_metrics()
        
        if slippage_pct > self.config.halt_slippage_pct:
            self._escalate_to_halt(IssueType.SLIPPAGE, {
                'slippage_pct': slippage_pct * 100,
                'expected': expected_price,
                'actual': actual_price
            })
        elif slippage_pct > self.config.throttle_slippage_pct:
            self._escalate_to_throttle(IssueType.SLIPPAGE, {
                'slippage_pct': slippage_pct * 100
            })
        elif slippage_pct > self.config.alert_slippage_pct:
            self._escalate_to_alert(IssueType.SLIPPAGE, {
                'slippage_pct': slippage_pct * 100
            })
    
    def report_critical_error(self, issue_type: IssueType, details: Dict):
        """Report critical error that should trigger shutdown"""
        logger.critical(f"CRITICAL ERROR: {issue_type} - {details}")
        self._escalate_to_shutdown(issue_type, details)
    
    def report_unexpected_loss(self, loss_pct: float, details: Dict):
        """Report unexpected large loss"""
        if loss_pct > self.config.halt_loss_pct:
            self._escalate_to_halt(IssueType.UNEXPECTED_LOSS, {
                'loss_pct': loss_pct * 100,
                **details
            })
    
    # ========================================================================
    # STATE ESCALATION
    # ========================================================================
    
    def _escalate_to_alert(self, issue_type: IssueType, details: Dict):
        """Escalate to ALERT level"""
        if self.state in [CircuitState.CLOSED]:
            self._change_state(CircuitState.ALERT, issue_type, details)
    
    def _escalate_to_throttle(self, issue_type: IssueType, details: Dict):
        """Escalate to THROTTLE level"""
        if self.state in [CircuitState.CLOSED, CircuitState.ALERT]:
            self._change_state(CircuitState.THROTTLE, issue_type, details)
    
    def _escalate_to_halt(self, issue_type: IssueType, details: Dict):
        """Escalate to HALT level"""
        if self.state != CircuitState.SHUTDOWN:
            self._change_state(CircuitState.HALT, issue_type, details)
    
    def _escalate_to_shutdown(self, issue_type: IssueType, details: Dict):
        """Escalate to SHUTDOWN level"""
        self._change_state(CircuitState.SHUTDOWN, issue_type, details)
        self.is_shutting_down = True
    
    def _change_state(self, new_state: CircuitState, issue_type: IssueType, details: Dict):
        """Change circuit breaker state"""
        old_state = self.state
        self.state = new_state
        self.last_state_change = datetime.utcnow()
        
        # Record issue
        issue = IssueRecord(
            timestamp=datetime.utcnow(),
            issue_type=issue_type,
            severity=new_state,
            details=details
        )
        self.issues.append(issue)
        
        # Log state change
        logger.warning(
            f"Circuit breaker state change: {old_state} → {new_state} "
            f"(Reason: {issue_type}, Details: {details})"
        )
        
        # Log for compliance
        compliance_logger.log_safety_violation({
            'type': 'circuit_breaker_triggered',
            'old_state': old_state,
            'new_state': new_state,
            'issue_type': issue_type,
            'details': details
        })
        
        # Execute callbacks
        if new_state == CircuitState.ALERT:
            self._execute_callbacks(self.alert_callbacks, issue)
        elif new_state == CircuitState.HALT:
            self._execute_callbacks(self.halt_callbacks, issue)
        elif new_state == CircuitState.SHUTDOWN:
            self._execute_callbacks(self.shutdown_callbacks, issue)
    
    # ========================================================================
    # RECOVERY
    # ========================================================================
    
    def _attempt_recovery(self):
        """Attempt to recover from degraded state"""
        now = datetime.utcnow()
        time_in_state = (now - self.last_state_change).total_seconds()
        
        # Check if enough time has passed
        if self.state == CircuitState.ALERT:
            if time_in_state < self.config.alert_cooldown_seconds:
                return
        elif self.state == CircuitState.THROTTLE:
            if time_in_state < self.config.throttle_cooldown_seconds:
                return
        elif self.state == CircuitState.HALT:
            if time_in_state < self.config.halt_cooldown_seconds:
                return
        else:
            return  # Can't recover from SHUTDOWN
        
        # Check if metrics are healthy
        if self._check_health():
            self._recover_state()
    
    def _check_health(self) -> bool:
        """Check if system metrics are healthy"""
        # Check API latency
        if self.api_latencies:
            recent_latency = sum(self.api_latencies[-5:]) / len(self.api_latencies[-5:])
            if recent_latency > self.config.alert_api_latency_ms:
                return False
        
        # Check consecutive failures
        if self.consecutive_failures > 0:
            return False
        
        # Check recent slippage
        if self.slippages:
            recent_slippage = sum(self.slippages[-5:]) / len(self.slippages[-5:])
            if recent_slippage > self.config.alert_slippage_pct:
                return False
        
        return True
    
    def _recover_state(self):
        """Recover to previous state"""
        if self.state == CircuitState.ALERT:
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker recovered to CLOSED state")
        elif self.state == CircuitState.THROTTLE:
            self.state = CircuitState.ALERT
            logger.info("Circuit breaker recovered to ALERT state")
        elif self.state == CircuitState.HALT:
            self.state = CircuitState.THROTTLE
            logger.info("Circuit breaker recovered to THROTTLE state")
        
        self.last_state_change = datetime.utcnow()
    
    def force_recovery(self):
        """Manually force recovery (admin override)"""
        if self.state != CircuitState.SHUTDOWN:
            self.state = CircuitState.CLOSED
            self.consecutive_failures = 0
            logger.warning("Circuit breaker MANUALLY recovered to CLOSED state")
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def _cleanup_old_metrics(self):
        """Remove old metrics outside monitoring window"""
        cutoff = datetime.utcnow() - timedelta(
            seconds=self.config.monitoring_window_seconds
        )
        
        # Clean order failures
        self.order_failures = [
            f for f in self.order_failures if f > cutoff
        ]
        
        # Keep only recent latencies and slippages (last 50)
        if len(self.api_latencies) > 50:
            self.api_latencies = self.api_latencies[-50:]
        if len(self.slippages) > 50:
            self.slippages = self.slippages[-50:]
    
    def _execute_callbacks(self, callbacks: List[Callable], issue: IssueRecord):
        """Execute registered callbacks"""
        for callback in callbacks:
            try:
                callback(issue)
            except Exception as e:
                logger.error(f"Callback execution failed: {e}")
    
    def register_alert_callback(self, callback: Callable):
        """Register callback for alert events"""
        self.alert_callbacks.append(callback)
    
    def register_halt_callback(self, callback: Callable):
        """Register callback for halt events"""
        self.halt_callbacks.append(callback)
    
    def register_shutdown_callback(self, callback: Callable):
        """Register callback for shutdown events"""
        self.shutdown_callbacks.append(callback)
    
    # ========================================================================
    # STATUS & MONITORING
    # ========================================================================
    
    def get_status(self) -> Dict:
        """Get current circuit breaker status"""
        return {
            'state': self.state,
            'is_shutting_down': self.is_shutting_down,
            'consecutive_failures': self.consecutive_failures,
            'time_in_current_state': (
                datetime.utcnow() - self.last_state_change
            ).total_seconds(),
            'recent_issues': len([
                i for i in self.issues
                if i.timestamp > datetime.utcnow() - timedelta(minutes=5)
            ]),
            'metrics': {
                'avg_api_latency_ms': (
                    sum(self.api_latencies[-10:]) / len(self.api_latencies[-10:])
                    if self.api_latencies else 0
                ),
                'recent_failures': len(self.order_failures),
                'avg_slippage_pct': (
                    sum(self.slippages[-10:]) / len(self.slippages[-10:]) * 100
                    if self.slippages else 0
                )
            }
        }
    
    def get_recent_issues(self, minutes: int = 5) -> List[IssueRecord]:
        """Get recent issues"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [i for i in self.issues if i.timestamp > cutoff]
    
    def manual_override_enable(self, reason: str):
        """Manually disable trading"""
        self.manual_override = True
        logger.warning(f"Manual override ENABLED: {reason}")
    
    def manual_override_disable(self):
        """Manually re-enable trading"""
        self.manual_override = False
        logger.info("Manual override DISABLED")


# Singleton instance
_circuit_breaker_instance = None


def get_circuit_breaker() -> CircuitBreaker:
    """Get or create circuit breaker singleton"""
    global _circuit_breaker_instance
    if _circuit_breaker_instance is None:
        _circuit_breaker_instance = CircuitBreaker()
    return _circuit_breaker_instance


# Export
__all__ = [
    'CircuitBreaker',
    'CircuitState',
    'IssueType',
    'CircuitConfig',
    'get_circuit_breaker'
]
