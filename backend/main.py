"""
AI Trading SIGMA - Main FastAPI Application
Entry point for the autonomous trading system
"""
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from core.hybrid_engine import HybridTradingEngine
from exchange.exchange_client import ExchangeClient
from ai.bedrock_client import BedrockClient
from database.db_manager import DatabaseManager
from utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

# Global instances
trading_engine = None
exchange_client = None
ai_client = None
db_manager = None
websocket_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for FastAPI application
    Handles startup and shutdown events
    """
    global trading_engine, exchange_client, ai_client, db_manager
    
    # Startup
    logger.info(f"🚀 Starting {settings.app_name}")
    logger.info(f"Exchange: {settings.exchange_to_use}")
    logger.info(f"Testnet: {settings.is_testnet}")
    
    try:
        # Initialize database
        logger.info("📦 Initializing database...")
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        # Initialize AI client
        logger.info("🤖 Initializing AI client...")
        ai_client = BedrockClient()
        
        # Initialize exchange client
        logger.info("💱 Initializing exchange client...")
        exchange_client = ExchangeClient()
        await exchange_client.initialize()
        
        # Initialize trading engine
        logger.info("⚡ Initializing trading engine...")
        trading_engine = HybridTradingEngine(
            exchange_client=exchange_client,
            ai_client=ai_client,
            db_manager=db_manager
        )
        
        logger.info("✅ All systems initialized successfully!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise
    
    finally:
        # Shutdown
        logger.info("🛑 Shutting down...")
        if trading_engine:
            await trading_engine.stop()
        logger.info("👋 Goodbye!")


# Create FastAPI app
app = FastAPI(
    title="AI Trading SIGMA API",
    description="Autonomous AI-Powered Scalping Bot",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")


websocket_manager = ConnectionManager()


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


# Health check
@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "exchange": settings.exchange_to_use,
        "testnet": settings.is_testnet
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "app": "healthy",
        "database": "unknown",
        "exchange": "unknown",
        "ai": "unknown",
        "trading_engine": "unknown"
    }
    
    try:
        if db_manager:
            status["database"] = "healthy"
        
        if exchange_client:
            status["exchange"] = "healthy"
        
        if ai_client:
            status["ai"] = "healthy"
        
        if trading_engine:
            status["trading_engine"] = "running" if trading_engine.is_running else "stopped"
        
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Trading endpoints
@app.post("/api/trading/start")
async def start_trading():
    """Start autonomous trading"""
    try:
        if not trading_engine:
            raise HTTPException(status_code=500, detail="Trading engine not initialized")
        
        await trading_engine.start()
        
        # Broadcast status update
        await websocket_manager.broadcast({
            "type": "status_update",
            "data": {
                "is_running": True,
                "message": "Trading started"
            }
        })
        
        return {"message": "Trading started successfully", "is_running": True}
    except Exception as e:
        logger.error(f"Failed to start trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trading/stop")
async def stop_trading():
    """Stop autonomous trading"""
    try:
        if not trading_engine:
            raise HTTPException(status_code=500, detail="Trading engine not initialized")
        
        await trading_engine.stop()
        
        # Broadcast status update
        await websocket_manager.broadcast({
            "type": "status_update",
            "data": {
                "is_running": False,
                "message": "Trading stopped"
            }
        })
        
        return {"message": "Trading stopped successfully", "is_running": False}
    except Exception as e:
        logger.error(f"Failed to stop trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trading/status")
async def get_trading_status():
    """Get current trading status"""
    try:
        if not trading_engine:
            return {"is_running": False, "message": "Engine not initialized"}
        
        return {
            "is_running": trading_engine.is_running,
            "active_strategy": trading_engine.active_strategy_name,
            "performance": await trading_engine.get_performance_metrics()
        }
    except Exception as e:
        logger.error(f"Failed to get trading status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI Chat endpoint
@app.post("/api/chat")
async def chat_with_ai(message: dict):
    """Chat with AI assistant"""
    try:
        if not ai_client:
            raise HTTPException(status_code=500, detail="AI client not initialized")
        
        user_message = message.get("message", "")
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        response = await ai_client.chat(user_message)
        
        return {
            "message": user_message,
            "response": response,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"AI chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Strategy endpoints
@app.get("/api/strategies")
async def list_strategies():
    """List available trading strategies"""
    try:
        if not trading_engine:
            return {"strategies": []}
        
        strategies = trading_engine.get_available_strategies()
        return {"strategies": strategies}
    except Exception as e:
        logger.error(f"Failed to list strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategies/apply")
async def apply_strategy(strategy_config: dict):
    """Apply a trading strategy"""
    try:
        if not trading_engine:
            raise HTTPException(status_code=500, detail="Trading engine not initialized")
        
        strategy_name = strategy_config.get("name")
        if not strategy_name:
            raise HTTPException(status_code=400, detail="Strategy name is required")
        
        await trading_engine.apply_strategy(strategy_name, strategy_config)
        
        return {
            "message": f"Strategy '{strategy_name}' applied successfully",
            "strategy": strategy_name
        }
    except Exception as e:
        logger.error(f"Failed to apply strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Performance endpoints
@app.get("/api/performance")
async def get_performance():
    """Get current performance metrics"""
    try:
        if not trading_engine:
            return {"error": "Trading engine not initialized"}
        
        metrics = await trading_engine.get_performance_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades")
async def get_trade_history(limit: int = 50):
    """Get trade history"""
    try:
        if not db_manager:
            return {"trades": []}
        
        trades = await db_manager.get_trades(limit=limit)
        return {"trades": trades}
    except Exception as e:
        logger.error(f"Failed to get trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
        )
