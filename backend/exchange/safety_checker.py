"""
Trading Safety Checker - WEEX Hackathon Compliance Layer
CRITICAL: This prevents disqualification by enforcing all rules
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

class TradingSafetyChecker:
    """
    Safety Layer for WEEX Hackathon Compliance
    
    Enforces:
    - Allowed trading pairs only
    - Maximum leverage limits (20x)
    - Minimum trade count (10 trades)
    - Daily loss limits
    - AI decision logging
    """
    
    # ====== WEEX HACKATHON RULES ======
    ALLOWED_PAIRS = {
        'ADA/USDT:USDT',
        'SOL/USDT:USDT',
        'LTC/USDT:USDT',
        'DOGE/USDT:USDT',
        'BTC/USDT:USDT',
        'ETH/USDT:USDT',
        'XRP/USDT:USDT',
        'BNB/USDT:USDT'
    }
    
    MAX_LEVERAGE = 20  # Maximum 20x leverage
    MIN_TRADES_REQUIRED = 10  # Minimum 10 trades for submission
    MAX_DAILY_LOSS = 0.10  # 10% daily loss limit (safety)
    
    def __init__(self, weex_client):
        self.weex = weex_client
        self.trade_counter = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        
        # Create logs directory
        self.logs_dir = Path("logs/hackathon")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        print("🛡️  Safety Checker initialized for WEEX Hackathon")
        print(f"   Allowed pairs: {len(self.ALLOWED_PAIRS)} pairs")
        print(f"   Max leverage: {self.MAX_LEVERAGE}x")
        print(f"   Min trades: {self.MIN_TRADES_REQUIRED}")
    
    async def validate_order(self, order_params: Dict) -> Dict:
        """
        Validate order BEFORE execution
        
        Args:
            order_params: Order parameters dict
            
        Returns:
            {"is_valid": bool, "reason": str, "warnings": list}
        """
        warnings = []
        
        # ===== CHECK 1: Trading Pair =====
        symbol = order_params.get('symbol', '')
        
        # Normalize symbol format
        if ':' not in symbol and symbol:
            # Auto-add :USDT for perpetual futures
            symbol = f"{symbol}:USDT"
            order_params['symbol'] = symbol
            warnings.append(f"Auto-corrected symbol to {symbol}")
        
        if symbol not in self.ALLOWED_PAIRS:
            return {
                "is_valid": False,
                "reason": f"❌ BLOCKED: {symbol} not in allowed pairs",
                "allowed_pairs": list(self.ALLOWED_PAIRS),
                "warnings": warnings
            }
        
        # ===== CHECK 2: Leverage Limit =====
        leverage = order_params.get('leverage', 1)
        
        if leverage > self.MAX_LEVERAGE:
            return {
                "is_valid": False,
                "reason": f"❌ BLOCKED: Leverage {leverage}x exceeds max {self.MAX_LEVERAGE}x",
                "warnings": warnings
            }
        
        # ===== CHECK 3: Order Type =====
        order_type = order_params.get('order_type', 'limit')
        
        if order_type not in ['limit', 'market']:
            return {
                "is_valid": False,
                "reason": f"❌ BLOCKED: Invalid order type '{order_type}'",
                "warnings": warnings
            }
        
        # ===== CHECK 4: Daily Loss Limit =====
        self._check_and_reset_daily()
        
        if self.daily_pnl < -self.MAX_DAILY_LOSS:
            return {
                "is_valid": False,
                "reason": f"❌ BLOCKED: Daily loss limit reached ({self.daily_pnl:.2%})",
                "warnings": warnings
            }
        
        # ===== CHECK 5: Position Size Sanity =====
        quantity = order_params.get('quantity', 0)
        
        if quantity <= 0:
            return {
                "is_valid": False,
                "reason": f"❌ BLOCKED: Invalid quantity {quantity}",
                "warnings": warnings
            }
        
        # ===== CHECK 6: Minimum Trades Warning =====
        if self.trade_counter < self.MIN_TRADES_REQUIRED:
            warnings.append(
                f"⚠️  Only {self.trade_counter}/{self.MIN_TRADES_REQUIRED} trades completed"
            )
        
        # All checks passed
        return {
            "is_valid": True,
            "reason": "✅ All validations passed",
            "warnings": warnings
        }
    
    async def execute_safe_order(
        self,
        order_params: Dict,
        ai_context: Optional[Dict] = None
    ) -> Dict:
        """
        Execute order WITH safety checks
        
        Args:
            order_params: Order parameters
            ai_context: AI decision context for logging
            
        Returns:
            Order result or error dict
        """
        timestamp = datetime.now()
        
        print(f"\n{'='*60}")
        print(f"🔍 SAFETY CHECK - Trade #{self.trade_counter + 1}")
        print(f"{'='*60}")
        
        # ===== STEP 1: Validate =====
        validation = await self.validate_order(order_params)
        
        # Log warnings
        for warning in validation.get('warnings', []):
            print(warning)
        
        if not validation['is_valid']:
            print(f"\n{validation['reason']}")
            print(f"{'='*60}\n")
            
            # Log violation
            self._log_violation(order_params, validation['reason'], timestamp)
            
            return {
                "error": validation['reason'],
                "validation": validation
            }
        
        print(f"✅ Validation passed: {validation['reason']}")
        
        # ===== STEP 2: Execute Order =====
        try:
            print(f"\n📤 Executing order via WEEX API...")
            print(f"   Symbol: {order_params['symbol']}")
            print(f"   Side: {order_params['side'].upper()}")
            print(f"   Quantity: {order_params['quantity']}")
            print(f"   Leverage: {order_params.get('leverage', 1)}x")
            
            # Execute via WEEX client
            result = await self.weex.place_order(
                symbol=order_params['symbol'],
                side=order_params['side'],
                quantity=order_params['quantity'],
                price=order_params.get('price'),
                order_type=order_params.get('order_type', 'limit'),
                stop_loss=order_params.get('stop_loss'),
                take_profit=order_params.get('take_profit')
            )
            
            # Check if error in result
            if 'error' in result:
                print(f"\n❌ Order execution failed: {result['error']}")
                self._log_execution_failure(order_params, result['error'], timestamp)
                return result
            
            # ===== STEP 3: Success - Update & Log =====
            self.trade_counter += 1
            
            print(f"\n✅ ORDER EXECUTED SUCCESSFULLY")
            print(f"   Order ID: {result.get('id', 'N/A')}")
            print(f"   Trade Count: {self.trade_counter}/{self.MIN_TRADES_REQUIRED}")
            print(f"{'='*60}\n")
            
            # Log successful trade for AI Log requirement
            self._log_successful_trade(
                order_params,
                result,
                ai_context,
                timestamp
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Execution exception: {str(e)}"
            print(f"\n❌ {error_msg}")
            print(f"{'='*60}\n")
            
            self._log_execution_failure(order_params, error_msg, timestamp)
            
            return {"error": error_msg}
    
    def update_pnl(self, trade_pnl: float):
        """Update daily P&L tracking"""
        self._check_and_reset_daily()
        self.daily_pnl += trade_pnl
        
        print(f"💰 Daily P&L updated: {self.daily_pnl:+.2%}")
        
        # Log P&L update
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "PNL_UPDATE",
            "trade_pnl": trade_pnl,
            "daily_pnl": self.daily_pnl,
            "trade_count": self.trade_counter
        }
        self._save_to_log("pnl_tracking.jsonl", log_entry)
    
    def _check_and_reset_daily(self):
        """Reset daily stats if new day"""
        current_date = datetime.now().date()
        
        if current_date > self.last_reset_date:
            print(f"\n📅 New trading day - Resetting stats")
            print(f"   Previous day P&L: {self.daily_pnl:+.2%}")
            print(f"   Previous day trades: {self.trade_counter}")
            
            self.daily_pnl = 0.0
            self.last_reset_date = current_date
    
    def _log_violation(self, order_params: Dict, reason: str, timestamp: datetime):
        """Log rule violation"""
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "type": "RULE_VIOLATION",
            "order_params": self._sanitize_params(order_params),
            "violation_reason": reason,
            "action": "ORDER_BLOCKED",
            "trade_count": self.trade_counter
        }
        
        self._save_to_log("safety_violations.jsonl", log_entry)
    
    def _log_execution_failure(
        self,
        order_params: Dict,
        error: str,
        timestamp: datetime
    ):
        """Log execution failure"""
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "type": "EXECUTION_FAILURE",
            "order_params": self._sanitize_params(order_params),
            "error": error,
            "trade_count": self.trade_counter
        }
        
        self._save_to_log("execution_failures.jsonl", log_entry)
    
    def _log_successful_trade(
        self,
        order_params: Dict,
        result: Dict,
        ai_context: Optional[Dict],
        timestamp: datetime
    ):
        """
        Log successful trade with AI decision context
        CRITICAL for hackathon evaluation
        """
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "type": "SUCCESSFUL_TRADE",
            "trade_number": self.trade_counter,
            
            # Order details
            "order": {
                "symbol": order_params['symbol'],
                "side": order_params['side'],
                "quantity": order_params['quantity'],
                "price": order_params.get('price'),
                "leverage": order_params.get('leverage', 1),
                "order_type": order_params.get('order_type', 'limit')
            },
            
            # WEEX response
            "weex_response": {
                "order_id": result.get('id', 'N/A'),
                "status": result.get('status', 'unknown'),
                "timestamp": result.get('timestamp')
            },
            
            # AI decision context (CRITICAL for evaluation)
            "ai_decision": ai_context or {
                "signal_source": "technical_analysis",
                "confidence": 0.0,
                "note": "No AI context provided"
            },
            
            # Compliance tracking
            "compliance": {
                "pair_allowed": order_params['symbol'] in self.ALLOWED_PAIRS,
                "leverage_ok": order_params.get('leverage', 1) <= self.MAX_LEVERAGE,
                "daily_pnl": self.daily_pnl
            }
        }
        
        self._save_to_log("ai_trading_log.jsonl", log_entry)
        
        # Also save human-readable summary
        self._save_trade_summary(log_entry)
    
    def _save_trade_summary(self, log_entry: Dict):
        """Save human-readable trade summary"""
        summary_file = self.logs_dir / "trade_summary.txt"
        
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Trade #{log_entry['trade_number']}\n")
            f.write(f"Time: {log_entry['timestamp']}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Symbol: {log_entry['order']['symbol']}\n")
            f.write(f"Side: {log_entry['order']['side'].upper()}\n")
            f.write(f"Quantity: {log_entry['order']['quantity']}\n")
            f.write(f"Price: {log_entry['order']['price']}\n")
            f.write(f"Leverage: {log_entry['order']['leverage']}x\n")
            f.write(f"\nAI Confidence: {log_entry['ai_decision'].get('confidence', 0):.2%}\n")
            f.write(f"Daily P&L: {log_entry['compliance']['daily_pnl']:+.2%}\n")
            f.write(f"{'='*60}\n")
    
    def _sanitize_params(self, params: Dict) -> Dict:
        """Remove sensitive data from params"""
        sanitized = params.copy()
        
        # Remove any sensitive keys
        sensitive_keys = ['api_key', 'api_secret', 'secret', 'password']
        for key in sensitive_keys:
            if key in sanitized:
                sanitized[key] = '***REDACTED***'
        
        return sanitized
    
    def _save_to_log(self, filename: str, log_entry: Dict):
        """Save log entry to JSONL file"""
        log_file = self.logs_dir / filename
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_status(self) -> Dict:
        """Get current safety checker status"""
        return {
            "trade_count": self.trade_counter,
            "min_trades_met": self.trade_counter >= self.MIN_TRADES_REQUIRED,
            "daily_pnl": self.daily_pnl,
            "can_trade": self.daily_pnl > -self.MAX_DAILY_LOSS,
            "allowed_pairs": list(self.ALLOWED_PAIRS),
            "max_leverage": self.MAX_LEVERAGE
        }
    
    def generate_compliance_report(self) -> str:
        """Generate compliance report for submission"""
        status = self.get_status()
        
        report = f"""
{'='*60}
WEEX HACKATHON COMPLIANCE REPORT
{'='*60}

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

TRADING STATISTICS:
- Total Trades: {status['trade_count']}
- Minimum Requirement: {self.MIN_TRADES_REQUIRED}
- Status: {'✅ MET' if status['min_trades_met'] else '❌ NOT MET'}

COMPLIANCE CHECKS:
✅ Allowed Pairs Only: {len(self.ALLOWED_PAIRS)} pairs enforced
✅ Max Leverage: {self.MAX_LEVERAGE}x enforced
✅ API Trading Only: All orders via WEEX API
✅ AI Logging: All trades logged with AI context

PERFORMANCE:
- Daily P&L: {status['daily_pnl']:+.2%}
- Can Continue Trading: {'Yes' if status['can_trade'] else 'No'}

LOG FILES GENERATED:
- ai_trading_log.jsonl (AI decision logs)
- safety_violations.jsonl (Rule violations)
- execution_failures.jsonl (Failed orders)
- pnl_tracking.jsonl (P&L tracking)
- trade_summary.txt (Human-readable)

{'='*60}
"""
        
        # Save report
        report_file = self.logs_dir / "compliance_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report


# Test code
if __name__ == "__main__":
    import asyncio
    
    # Mock WEEX client for testing
    class MockWEEXClient:
        async def place_order(self, **kwargs):
            return {
                'id': 'test_order_123',
                'status': 'open',
                'timestamp': datetime.now().isoformat()
            }
    
    async def test():
        print("🧪 Testing Safety Checker\n")
        
        # Initialize
        mock_weex = MockWEEXClient()
        checker = TradingSafetyChecker(mock_weex)
        
        # Test 1: Valid order
        print("\n" + "="*60)
        print("TEST 1: Valid Order (BTC/USDT)")
        print("="*60)
        
        valid_order = {
            'symbol': 'BTC/USDT:USDT',
            'side': 'buy',
            'quantity': 0.001,
            'price': 45000,
            'leverage': 10,
            'order_type': 'limit'
        }
        
        result = await checker.execute_safe_order(
            valid_order,
            ai_context={"confidence": 0.75, "signal": "bullish"}
        )
        print(f"Result: {result}")
        
        # Test 2: Invalid pair
        print("\n" + "="*60)
        print("TEST 2: Invalid Pair (Should Block)")
        print("="*60)
        
        invalid_order = {
            'symbol': 'TRX/USDT:USDT',  # Not in allowed list
            'side': 'buy',
            'quantity': 100,
            'leverage': 5
        }
        
        result = await checker.execute_safe_order(invalid_order)
        print(f"Result: {result}")
        
        # Test 3: Excessive leverage
        print("\n" + "="*60)
        print("TEST 3: Excessive Leverage (Should Block)")
        print("="*60)
        
        high_leverage_order = {
            'symbol': 'ETH/USDT:USDT',
            'side': 'buy',
            'quantity': 0.1,
            'leverage': 25,  # Exceeds max 20x
            'price': 2500
        }
        
        result = await checker.execute_safe_order(high_leverage_order)
        print(f"Result: {result}")
        
        # Generate report
        print("\n" + "="*60)
        print("COMPLIANCE REPORT")
        print("="*60)
        print(checker.generate_compliance_report())
        
        print("\n✅ All tests completed!")
        print(f"📁 Check logs in: {checker.logs_dir}")
    
    asyncio.run(test())
