"""
API Performance Monitor
Tracks API call latency and reports to circuit breaker
"""

import time
import asyncio
from typing import Optional, Callable, Any
from functools import wraps
from datetime import datetime

from core.circuit_breaker import get_circuit_breaker, IssueType
from utils.logger import setup_logger

logger = setup_logger(__name__)


class APIMonitor:
    """
    Monitors API calls and reports performance to circuit breaker
    """
    
    def __init__(self):
        self.circuit_breaker = get_circuit_breaker()
        self.call_count = 0
        self.total_latency = 0.0
    
    def track_sync_call(self, api_name: str):
        """
        Decorator for synchronous API calls
        
        Usage:
            @api_monitor.track_sync_call('fetch_balance')
            def fetch_balance(self):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                error = None
                result = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    latency_ms = (time.time() - start_time) * 1000
                    self._record_call(api_name, latency_ms, error)
                
            return wrapper
        return decorator
    
    def track_async_call(self, api_name: str):
        """
        Decorator for async API calls
        
        Usage:
            @api_monitor.track_async_call('fetch_ohlcv')
            async def fetch_ohlcv(self, ...):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                error = None
                result = None
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    latency_ms = (time.time() - start_time) * 1000
                    self._record_call(api_name, latency_ms, error)
            
            return wrapper
        return decorator
    
    def _record_call(self, api_name: str, latency_ms: float, error: Optional[Exception]):
        """Record API call metrics"""
        self.call_count += 1
        self.total_latency += latency_ms
        
        # Report to circuit breaker
        self.circuit_breaker.report_api_latency(latency_ms)
        
        # Log slow calls
        if latency_ms > 1000:
            logger.warning(
                f"Slow API call: {api_name} took {latency_ms:.0f}ms"
            )
        
        # Log errors
        if error:
            logger.error(f"API call failed: {api_name} - {error}")
            self.circuit_breaker.report_order_failure({
                'api': api_name,
                'error': str(error),
                'latency_ms': latency_ms
            })
        else:
            # Success
            self.circuit_breaker.report_order_success()
    
    def get_average_latency(self) -> float:
        """Get average API latency"""
        if self.call_count == 0:
            return 0.0
        return self.total_latency / self.call_count
    
    def reset_stats(self):
        """Reset statistics"""
        self.call_count = 0
        self.total_latency = 0.0


# Global instance
api_monitor = APIMonitor()


# Export
__all__ = ['APIMonitor', 'api_monitor']
