"""
Logging Utility for AI Trading SIGMA
Provides structured logging with file and console output
"""

import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from logging.handlers import RotatingFileHandler


def setup_logger(name: str, log_file: str = None, level: str = "INFO") -> logging.Logger:
    """
    Setup logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Log file path (optional)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file provided)
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


class ComplianceLogger:
    """
    Special logger for hackathon compliance tracking
    Logs all AI decisions in JSONL format
    """
    
    def __init__(self, log_dir: str = "logs/hackathon"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log files
        self.ai_log = self.log_dir / "ai_trading_log.jsonl"
        self.safety_log = self.log_dir / "safety_violations.jsonl"
        self.execution_log = self.log_dir / "execution_failures.jsonl"
        self.pnl_log = self.log_dir / "pnl_tracking.jsonl"
        self.summary_log = self.log_dir / "trade_summary.txt"
    
    def log_ai_decision(self, decision: Dict[str, Any]):
        """Log AI trading decision"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "ai_decision",
            **decision
        }
        self._append_jsonl(self.ai_log, entry)
    
    def log_safety_violation(self, violation: Dict[str, Any]):
        """Log safety rule violation"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "safety_violation",
            **violation
        }
        self._append_jsonl(self.safety_log, entry)
    
    def log_execution_failure(self, failure: Dict[str, Any]):
        """Log trade execution failure"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "execution_failure",
            **failure
        }
        self._append_jsonl(self.execution_log, entry)
    
    def log_pnl(self, pnl_data: Dict[str, Any]):
        """Log P&L data"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "pnl",
            **pnl_data
        }
        self._append_jsonl(self.pnl_log, entry)
    
    def update_summary(self, summary: str):
        """Update human-readable summary"""
        with open(self.summary_log, 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Updated: {datetime.utcnow().isoformat()}\n")
            f.write(f"{'='*80}\n")
            f.write(summary)
            f.write(f"\n{'='*80}\n\n")
    
    def _append_jsonl(self, file_path: Path, data: Dict[str, Any]):
        """Append JSON line to file"""
        with open(file_path, 'a') as f:
            f.write(json.dumps(data) + '\n')
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compliance statistics"""
        stats = {
            "total_decisions": self._count_lines(self.ai_log),
            "safety_violations": self._count_lines(self.safety_log),
            "execution_failures": self._count_lines(self.execution_log),
            "pnl_entries": self._count_lines(self.pnl_log)
        }
        return stats
    
    def _count_lines(self, file_path: Path) -> int:
        """Count lines in file"""
        if not file_path.exists():
            return 0
        with open(file_path, 'r') as f:
            return sum(1 for _ in f)


# Global compliance logger instance
compliance_logger = ComplianceLogger()


def log_trade_decision(
    symbol: str,
    action: str,
    price: float,
    indicators: Dict[str, float],
    reasoning: str,
    confidence: float,
    position_size: float = None,
    risk_reward: float = None
):
    """
    Convenience function to log trade decision
    
    Args:
        symbol: Trading pair
        action: ENTER_LONG, ENTER_SHORT, EXIT, WAIT
        price: Current price
        indicators: Dictionary of indicator values
        reasoning: Human-readable reasoning
        confidence: Confidence score (0-1)
        position_size: Position size (optional)
        risk_reward: Risk/reward ratio (optional)
    """
    decision = {
        "symbol": symbol,
        "action": action,
        "price": price,
        "indicators": indicators,
        "reasoning": reasoning,
        "confidence": confidence,
    }
    
    if position_size is not None:
        decision["position_size"] = position_size
    if risk_reward is not None:
        decision["risk_reward"] = risk_reward
    
    compliance_logger.log_ai_decision(decision)


# Export
__all__ = [
    'setup_logger',
    'ComplianceLogger',
    'compliance_logger',
    'log_trade_decision'
        ]
