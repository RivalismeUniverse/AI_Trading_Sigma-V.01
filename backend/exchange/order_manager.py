"""
Order management system.
Handles order lifecycle, tracking, and execution.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from backend.exchange.weex_client import WEEXClient
from backend.database.db_manager import DatabaseManager
from backend.utils.helpers import generate_trade_id

logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class OrderManager:
    """Manages order execution and tracking"""
    
    def __init__(
        self,
        exchange_client: WEEXClient,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize order manager
        
        Args:
            exchange_client: WEEX exchange client
            db_manager: Database manager (optional)
        """
        self.exchange = exchange_client
        self.db = db_manager
        
        # Order tracking
        self.active_orders: Dict[str, Dict[str, Any]] = {}
        self.order_history: List[Dict[str, Any]] = []
        
        logger.info("Order manager initialized")
    
    def create_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = 'market',
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        leverage: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create and execute order
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            quantity: Order quantity
            order_type: 'market' or 'limit'
            price: Limit price (for limit orders)
            stop_loss: Stop loss price
            take_profit: Take profit price
            leverage: Leverage amount
            metadata: Additional order metadata
            
        Returns:
            Order details if successful
        """
        try:
            # Generate internal order ID
            order_id = generate_trade_id(symbol)
            
            logger.info(f"Creating {order_type} {side} order: {quantity} {symbol} @ {leverage}x leverage")
            
            # Execute order based on type
            if order_type == 'market':
                exchange_order = self.exchange.create_market_order(
                    symbol=symbol,
                    side=side,
                    amount=quantity,
                    leverage=leverage
                )
            elif order_type == 'limit':
                exchange_order = self.exchange.create_limit_order(
                    symbol=symbol,
                    side=side,
                    amount=quantity,
                    price=price,
                    leverage=leverage
                )
            else:
                logger.error(f"Unsupported order type: {order_type}")
                return None
            
            if not exchange_order:
                logger.error("Failed to execute order on exchange")
                return None
            
            # Create order record
            order_data = {
                'order_id': order_id,
                'exchange_order_id': exchange_order.get('id'),
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
                'price': price or exchange_order.get('price'),
                'filled_quantity': exchange_order.get('filled', 0),
                'status': self._parse_exchange_status(exchange_order.get('status')),
                'leverage': leverage,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'created_at': datetime.utcnow(),
                'metadata': metadata or {}
            }
            
            # Track order
            self.active_orders[order_id] = order_data
            
            # Set stop loss and take profit if provided
            if stop_loss or take_profit:
                self._set_exit_orders(order_id, symbol, side, quantity, stop_loss, take_profit)
            
            logger.info(f"✅ Order created: {order_id} (Exchange: {exchange_order.get('id')})")
            
            return order_data
            
        except Exception as e:
            logger.error(f"❌ Error creating order: {e}", exc_info=True)
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an active order
        
        Args:
            order_id: Internal order ID
            
        Returns:
            True if cancelled successfully
        """
        try:
            if order_id not in self.active_orders:
                logger.warning(f"Order {order_id} not found in active orders")
                return False
            
            order = self.active_orders[order_id]
            exchange_order_id = order.get('exchange_order_id')
            
            if not exchange_order_id:
                logger.error("No exchange order ID found")
                return False
            
            # Cancel on exchange
            result = self.exchange.cancel_order(exchange_order_id, order['symbol'])
            
            if result:
                order['status'] = OrderStatus.CANCELLED.value
                order['cancelled_at'] = datetime.utcnow()
                
                # Move to history
                self.order_history.append(order)
                del self.active_orders[order_id]
                
                logger.info(f"✅ Order cancelled: {order_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order details
        
        Args:
            order_id: Internal order ID
            
        Returns:
            Order details if found
        """
        # Check active orders first
        if order_id in self.active_orders:
            return self.active_orders[order_id]
        
        # Check history
        for order in self.order_history:
            if order['order_id'] == order_id:
                return order
        
        return None
    
    def update_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Update order status from exchange
        
        Args:
            order_id: Internal order ID
            
        Returns:
            Updated order details
        """
        try:
            if order_id not in self.active_orders:
                return None
            
            order = self.active_orders[order_id]
            exchange_order_id = order.get('exchange_order_id')
            
            if not exchange_order_id:
                return order
            
            # Fetch from exchange
            exchange_order = self.exchange.fetch_order(exchange_order_id, order['symbol'])
            
            if exchange_order:
                # Update status
                order['status'] = self._parse_exchange_status(exchange_order.get('status'))
                order['filled_quantity'] = exchange_order.get('filled', 0)
                order['updated_at'] = datetime.utcnow()
                
                # If fully filled, move to history
                if order['status'] == OrderStatus.FILLED.value:
                    order['filled_at'] = datetime.utcnow()
                    self.order_history.append(order)
                    del self.active_orders[order_id]
                    logger.info(f"Order {order_id} fully filled")
                
                return order
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            return None
    
    def get_active_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all active orders
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of active orders
        """
        orders = list(self.active_orders.values())
        
        if symbol:
            orders = [o for o in orders if o['symbol'] == symbol]
        
        return orders
    
    def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get order history
        
        Args:
            symbol: Filter by symbol (optional)
            limit: Maximum number of orders to return
            
        Returns:
            List of historical orders
        """
        history = self.order_history[-limit:]
        
        if symbol:
            history = [o for o in history if o['symbol'] == symbol]
        
        return history
    
    def _set_exit_orders(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: float,
        stop_loss: Optional[float],
        take_profit: Optional[float]
    ):
        """Set stop loss and take profit orders"""
        try:
            # Determine exit side (opposite of entry)
            exit_side = 'sell' if side == 'buy' else 'buy'
            
            # Set stop loss
            if stop_loss:
                sl_order = self.exchange.create_stop_loss_order(
                    symbol=symbol,
                    side=exit_side,
                    amount=quantity,
                    stop_price=stop_loss
                )
                if sl_order:
                    logger.info(f"✅ Stop loss set at {stop_loss}")
            
            # Set take profit
            if take_profit:
                tp_order = self.exchange.create_take_profit_order(
                    symbol=symbol,
                    side=exit_side,
                    amount=quantity,
                    price=take_profit
                )
                if tp_order:
                    logger.info(f"✅ Take profit set at {take_profit}")
                    
        except Exception as e:
            logger.error(f"Error setting exit orders: {e}")
    
    def _parse_exchange_status(self, exchange_status: str) -> str:
        """Parse exchange order status to internal status"""
        status_map = {
            'open': OrderStatus.SUBMITTED.value,
            'closed': OrderStatus.FILLED.value,
            'canceled': OrderStatus.CANCELLED.value,
            'cancelled': OrderStatus.CANCELLED.value,
            'expired': OrderStatus.EXPIRED.value,
            'rejected': OrderStatus.REJECTED.value,
        }
        
        return status_map.get(exchange_status.lower(), OrderStatus.PENDING.value)
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """
        Cancel all active orders
        
        Args:
            symbol: Symbol to cancel (optional, cancels all if None)
            
        Returns:
            Number of orders cancelled
        """
        cancelled_count = 0
        
        orders_to_cancel = list(self.active_orders.keys())
        
        for order_id in orders_to_cancel:
            order = self.active_orders[order_id]
            
            # Filter by symbol if provided
            if symbol and order['symbol'] != symbol:
                continue
            
            if self.cancel_order(order_id):
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} orders")
        return cancelled_count
    
    def get_order_statistics(self) -> Dict[str, Any]:
        """Get order statistics"""
        filled_orders = [o for o in self.order_history if o['status'] == OrderStatus.FILLED.value]
        
        return {
            'total_orders': len(self.order_history) + len(self.active_orders),
            'active_orders': len(self.active_orders),
            'filled_orders': len(filled_orders),
            'cancelled_orders': len([o for o in self.order_history if o['status'] == OrderStatus.CANCELLED.value]),
            'fill_rate': (len(filled_orders) / len(self.order_history) * 100) if self.order_history else 0
        }

# Example usage
if __name__ == "__main__":
    from backend.config import settings
    
    # Initialize
    exchange = WEEXClient(
        api_key=settings.WEEX_API_KEY,
        api_secret=settings.WEEX_API_SECRET,
        testnet=True
    )
    
    order_manager = OrderManager(exchange)
    
    # Create market order
    order = order_manager.create_order(
        symbol='BTC/USDT:USDT',
        side='buy',
        quantity=0.01,
        leverage=10,
        stop_loss=49000,
        take_profit=51000
    )
    
    if order:
        print(f"✅ Order created: {order['order_id']}")
        
        # Get order details
        details = order_manager.get_order(order['order_id'])
        print(f"Order details: {details}")
        
        # Get statistics
        stats = order_manager.get_order_statistics()
        print(f"Statistics: {stats}")
