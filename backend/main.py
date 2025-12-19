"""
AI Trading SIGMA - FastAPI Main Application
Main entry point for the backend API server
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import settings, validate_exchange_config, validate_aws_config
from core.hybrid_engine import HybridTradingEngine
from core.circuit_breaker import get_circuit_breaker
from core.notification_system import notification_system
from ai.bedrock_client import BedrockClient
from database.db_manager import DatabaseManager
from utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

# Global instances
trading_engine: Optional[HybridTradingEngine] = None
db_manager: DatabaseManager = DatabaseManager()
bedrock_client: Optional[BedrockClient] = None
circuit_breaker = get_circuit_breaker()
websocket_clients: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("Starting AI Trading SIGMA...")
    
    try:
        # Validate configurations
        validate_exchange_config()
        validate_aws_config()
        
        # Initialize database
        db_manager.create_tables()
        logger.info("Database initialized")
        
        # Initialize Bedrock client
        global bedrock_client
        bedrock_client = BedrockClient()
        logger.info("AWS Bedrock client initialized")
        
        # Initialize trading engine
        global trading_engine
        trading_engine = HybridTradingEngine()
        logger.info("Trading engine initialized")
        
        logger.info(f"AI Trading SIGMA started on {settings.HOST}:{settings.PORT}")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Trading SIGMA...")
    if trading_engine and trading_engine.is_running:
        await trading_engine.stop()
    logger.info("AI Trading SIGMA shut down successfully")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous AI-Powered Scalping Bot with Probability-Based Decision Making",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket manager
async def broadcast_message(message: dict):
    """Broadcast message to all connected WebSocket clients"""
    disconnected_clients = []
    for client in websocket_clients:
        try:
            await client.send_json(message)
        except Exception:
            disconnected_clients.append(client)
    
    # Remove disconnected clients
    for client in disconnected_clients:
        websocket_clients.remove(client)


# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================

@app.websocket("/ws/live-feed")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_clients.append(websocket)
    logger.info("WebSocket client connected")
    
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            # Echo back for now
            await websocket.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)
        logger.info("WebSocket client disconnected")


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "exchange": settings.EXCHANGE
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "engine_running": trading_engine.is_running if trading_engine else False,
        "exchange": settings.EXCHANGE,
        "database": "connected"
    }


# ============================================================================
# AI CHAT ENDPOINTS
# ============================================================================

@app.post("/api/chat")
async def chat(request: dict):
    """Chat with AI assistant"""
    try:
        user_message = request.get("message", "")
        conversation_history = request.get("history", [])
        
        if not bedrock_client:
            raise HTTPException(status_code=500, detail="Bedrock client not initialized")
        
        response = await bedrock_client.chat(user_message, conversation_history)
        
        return {
            "success": True,
            "response": response,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STRATEGY ENDPOINTS
# ============================================================================

@app.post("/api/strategy/create")
async def create_strategy(request: dict):
    """Generate trading strategy from natural language"""
    try:
        prompt = request.get("prompt", "")
        
        if not bedrock_client:
            raise HTTPException(status_code=500, detail="Bedrock client not initialized")
        
        strategy = await bedrock_client.generate_strategy(prompt)
        
        # Save strategy to database
        strategy_id = db_manager.save_strategy(strategy)
        
        return {
            "success": True,
            "strategy_id": strategy_id,
            "strategy": strategy
        }
    except Exception as e:
        logger.error(f"Strategy creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategy/apply")
async def apply_strategy(request: dict):
    """Apply strategy to trading engine"""
    try:
        strategy_id = request.get("strategy_id")
        
        if not trading_engine:
            raise HTTPException(status_code=500, detail="Trading engine not initialized")
        
        strategy = db_manager.get_strategy(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        await trading_engine.apply_strategy(strategy)
        
        return {
            "success": True,
            "message": "Strategy applied successfully"
        }
    except Exception as e:
        logger.error(f"Strategy application error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategy/list")
async def list_strategies():
    """List all saved strategies"""
    try:
        strategies = db_manager.get_all_strategies()
        return {
            "success": True,
            "strategies": strategies
        }
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategy/active")
async def get_active_strategy():
    """Get currently active strategy"""
    try:
        if not trading_engine:
            raise HTTPException(status_code=500, detail="Trading engine not initialized")
        
        strategy = trading_engine.get_active_strategy()
        return {
            "success": True,
            "strategy": strategy
        }
    except Exception as e:
        logger.error(f"Error getting active strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TRADING CONTROL ENDPOINTS
# ============================================================================

@app.post("/api/trading/start")
async def start_trading(background_tasks: BackgroundTasks):
    """Start autonomous trading"""
    try:
        if not trading_engine:
            raise HTTPException(status_code=500, detail="Trading engine not initialized")
        
        if trading_engine.is_running:
            return {
                "success": False,
                "message": "Trading is already running"
            }
        
        # Start trading in background
        background_tasks.add_task(trading_engine.start)
        
        return {
            "success": True,
            "message": "Trading started successfully"
        }
    except Exception as e:
        logger.error(f"Error starting trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trading/stop")
async def stop_trading():
    """Stop autonomous trading"""
    try:
        if not trading_engine:
            raise HTTPException(status_code=500, detail="Trading engine not initialized")
        
        if not trading_engine.is_running:
            return {
                "success": False,
                "message": "Trading is not running"
            }
        
        await trading_engine.stop()
        
        return {
            "success": True,
            "message": "Trading stopped successfully"
        }
    except Exception as e:
        logger.error(f"Error stopping trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trading/status")
async def get_trading_status():
    """Get current trading status"""
    try:
        if not trading_engine:
            raise HTTPException(status_code=500, detail="Trading engine not initialized")
        
        status = await trading_engine.get_status()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"Error getting trading status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PERFORMANCE ENDPOINTS
# ============================================================================

@app.get("/api/performance")
async def get_performance():
    """Get current performance metrics"""
    try:
        metrics = db_manager.get_performance_metrics()
        return {
            "success": True,
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance/history")
async def get_performance_history(days: int = 7):
    """Get historical performance"""
    try:
        history = db_manager.get_performance_history(days)
        return {
            "success": True,
            "history": history
        }
    except Exception as e:
        logger.error(f"Error getting performance history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TRADE ENDPOINTS
# ============================================================================

@app.get("/api/trades")
async def get_trades(limit: int = 50, offset: int = 0):
    """Get trade history"""
    try:
        trades = db_manager.get_trades(limit, offset)
        return {
            "success": True,
            "trades": trades,
            "total": len(trades)
        }
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades/open")
async def get_open_positions():
    """Get currently open positions"""
    try:
        if not trading_engine:
            raise HTTPException(status_code=500, detail="Trading engine not initialized")
        
        positions = await trading_engine.get_open_positions()
        return {
            "success": True,
            "positions": positions
        }
    except Exception as e:
        logger.error(f"Error getting open positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMPLIANCE ENDPOINTS
# ============================================================================

@app.get("/api/compliance/report")
async def generate_compliance_report():
    """Generate hackathon compliance report"""
    try:
        report = db_manager.generate_compliance_report()
        return {
            "success": True,
            "report": report
        }
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CIRCUIT BREAKER ENDPOINTS
# ============================================================================

@app.get("/api/circuit-breaker/status")
async def get_circuit_breaker_status():
    """Get circuit breaker status"""
    try:
        status = circuit_breaker.get_status()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/circuit-breaker/issues")
async def get_circuit_breaker_issues(minutes: int = 5):
    """Get recent circuit breaker issues"""
    try:
        issues = circuit_breaker.get_recent_issues(minutes)
        return {
            "success": True,
            "issues": [
                {
                    "timestamp": issue.timestamp.isoformat(),
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "details": issue.details,
                    "resolved": issue.resolved
                }
                for issue in issues
            ]
        }
    except Exception as e:
        logger.error(f"Error getting issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/circuit-breaker/recover")
async def force_circuit_breaker_recovery():
    """Force circuit breaker recovery (admin only)"""
    try:
        circuit_breaker.force_recovery()
        return {
            "success": True,
            "message": "Circuit breaker manually recovered"
        }
    except Exception as e:
        logger.error(f"Error forcing recovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/circuit-breaker/override")
async def toggle_manual_override(request: dict):
    """Toggle manual override"""
    try:
        enabled = request.get("enabled", False)
        reason = request.get("reason", "Manual override")
        
        if enabled:
            circuit_breaker.manual_override_enable(reason)
        else:
            circuit_breaker.manual_override_disable()
        
        return {
            "success": True,
            "override_enabled": enabled,
            "reason": reason
        }
    except Exception as e:
        logger.error(f"Error toggling override: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NOTIFICATION ENDPOINTS
# ============================================================================

@app.get("/api/notifications")
async def get_notifications(limit: int = 20):
    """Get recent notifications"""
    try:
        notifications = notification_system.get_dashboard_notifications(limit)
        return {
            "success": True,
            "notifications": notifications
        }
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """Mark notification as read"""
    try:
        notification_system.mark_notification_read(notification_id)
        return {
            "success": True,
            "message": "Notification marked as read"
        }
    except Exception as e:
        logger.error(f"Error marking notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/notifications")
async def clear_notifications():
    """Clear all notifications"""
    try:
        notification_system.clear_dashboard_notifications()
        return {
            "success": True,
            "message": "All notifications cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BALANCE & ACCOUNT ENDPOINTS
# ============================================================================

@app.get("/api/balance")
async def get_balance():
    """Get current account balance"""
    try:
        if not trading_engine:
            raise HTTPException(status_code=500, detail="Trading engine not initialized")
        
        balance = await trading_engine.get_balance()
        return {
            "success": True,
            "balance": balance
        }
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error"
        }
    )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
