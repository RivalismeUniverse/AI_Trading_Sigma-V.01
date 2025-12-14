"""
AI TRADING SIGMA - FastAPI Server (COMPLETE)
Main API server with all endpoints and WebSocket support.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Internal imports
from backend.config import settings
from backend.core.hybrid_engine import HybridTradingEngine
from backend.ai.bedrock_client import BedrockClient
from backend.ai.prompt_processor import PromptProcessor
from backend.exchange.weex_client import WEEXClient
from backend.exchange.safety_checker import SafetyChecker
from backend.database.db_manager import DatabaseManager
from backend.utils.logger import setup_logger
from backend.utils.validators import validate_order_params, ValidationError

# Setup logging
logger = setup_logger('api')

# Global instances
trading_engine: Optional[HybridTradingEngine] = None
ai_client: Optional[BedrockClient] = None
prompt_processor: Optional[PromptProcessor] = None
db_manager: Optional[DatabaseManager] = None
ws_connections: List[WebSocket] = []

# ===== LIFESPAN MANAGEMENT =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global trading_engine, ai_client, prompt_processor, db_manager
    
    logger.info("🚀 Starting AI TRADING SIGMA API...")
    
    # Initialize components
    ai_client = BedrockClient()
    prompt_processor = PromptProcessor(ai_client)
    db_manager = DatabaseManager(settings.DATABASE_URL)
    
    # Initialize trading engine but don't start it yet
    trading_engine = HybridTradingEngine(
        ai_client=ai_client,
        db_manager=db_manager
    )
    
    logger.info("✅ All components initialized")
    
    yield
    
    # Cleanup on shutdown
    logger.info("🛑 Shutting down...")
    if trading_engine and trading_engine.is_running:
        await trading_engine.stop()
    
    logger.info("✅ Shutdown complete")

# ===== FastAPI APP =====

app = FastAPI(
    title="AI TRADING SIGMA API",
    description="Autonomous trading bot with AI-powered strategy generation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== PYDANTIC MODELS =====

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    context: Optional[Dict[str, Any]] = None
    timestamp: str

class StrategyCreateRequest(BaseModel):
    user_prompt: str = Field(..., description="Natural language strategy description")

class StrategyApplyRequest(BaseModel):
    strategy_config: Dict[str, Any] = Field(..., description="Strategy configuration")

class TradingControlRequest(BaseModel):
    action: str = Field(..., description="'start' or 'stop'")

class OrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: float
    type: str = 'market'
    price: Optional[float] = None
    leverage: float = 1.0

# ===== WEBSOCKET MANAGER =====

class WebSocketManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        self.connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Add new WebSocket connection"""
        await websocket.accept()
        self.connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.connections:
            self.connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining: {len(self.connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        disconnected = []
        
        for connection in self.connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_to(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            self.disconnect(websocket)

ws_manager = WebSocketManager()

# ===== BACKGROUND TASKS =====

async def broadcast_status_updates():
    """Background task to broadcast status updates"""
    while True:
        try:
            if trading_engine:
                status = trading_engine.get_status()
                await ws_manager.broadcast({
                    'type': 'status_update',
                    'data': status,
                    'timestamp': datetime.utcnow().isoformat()
                })
            await asyncio.sleep(2)  # Update every 2 seconds
        except Exception as e:
            logger.error(f"Error in status broadcast: {e}")
            await asyncio.sleep(5)

# ===== API ENDPOINTS =====

@app.get("/")
async def root():
    """API root"""
    return {
        "name": "AI TRADING SIGMA API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "trading_engine": "running" if trading_engine and trading_engine.is_running else "stopped"
    }

# ===== CHAT ENDPOINTS =====

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with AI assistant.
    Handles: strategy questions, market analysis, performance queries, general Q&A
    """
    try:
        logger.info(f"Chat request: {request.message[:100]}...")
        
        # Prepare context
        context = request.context or {}
        
        # Add trading engine status to context
        if trading_engine:
            context['engine_status'] = trading_engine.get_status()
        
        # Get AI response
        response = await prompt_processor.process_chat_message(
            user_message=request.message,
            context=context
        )
        
        # Log interaction to database
        if db_manager:
            db_manager.log_ai_interaction({
                'interaction_type': 'chat',
                'user_message': request.message,
                'ai_response': response['response'],
                'context': context,
                'input_tokens': response.get('input_tokens'),
                'output_tokens': response.get('output_tokens'),
                'cost': response.get('cost'),
                'response_time': response.get('response_time')
            })
        
        return ChatResponse(
            response=response['response'],
            context=response.get('context'),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ===== STRATEGY ENDPOINTS =====

@app.post("/api/strategy/create")
async def create_strategy(request: StrategyCreateRequest):
    """
    Generate strategy from natural language prompt.
    Example: "Create RSI oversold strategy for BTC with 10x leverage"
    """
    try:
        logger.info(f"Creating strategy from prompt: {request.user_prompt}")
        
        # Generate strategy using AI
        strategy_config = await prompt_processor.generate_strategy_from_prompt(
            request.user_prompt
        )
        
        if not strategy_config:
            raise HTTPException(status_code=400, detail="Failed to generate strategy")
        
        # Save to database
        if db_manager:
            strategy_model = db_manager.create_strategy({
                'strategy_id': f"STRAT_{int(datetime.utcnow().timestamp())}",
                'name': strategy_config.get('name', 'AI Generated Strategy'),
                'description': strategy_config.get('description', request.user_prompt),
                'symbol': strategy_config.get('symbol', settings.DEFAULT_SYMBOL),
                'timeframe': strategy_config.get('timeframe', settings.DEFAULT_TIMEFRAME),
                'leverage': strategy_config.get('leverage', 1.0),
                'config': strategy_config,
                'generated_by_ai': True,
                'ai_prompt': request.user_prompt
            })
            
            logger.info(f"✅ Strategy created: {strategy_model.strategy_id}")
        
        return {
            'success': True,
            'strategy': strategy_config,
            'message': 'Strategy generated successfully'
        }
        
    except Exception as e:
        logger.error(f"Strategy creation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategy/apply")
async def apply_strategy(request: StrategyApplyRequest):
    """
    Apply strategy to trading engine.
    This will replace the current active strategy.
    """
    try:
        if not trading_engine:
            raise HTTPException(status_code=500, detail="Trading engine not initialized")
        
        logger.info("Applying new strategy...")
        
        # Apply to engine
        trading_engine.apply_strategy(request.strategy_config)
        
        # Activate in database
        if db_manager:
            strategy_id = request.strategy_config.get('id')
            if strategy_id:
                db_manager.activate_strategy(strategy_id)
        
        # Broadcast update
        await ws_manager.broadcast({
            'type': 'strategy_applied',
            'data': request.strategy_config,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return {
            'success': True,
            'message': 'Strategy applied successfully'
        }
        
    except Exception as e:
        logger.error(f"Strategy application error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategy/list")
async def list_strategies():
    """Get all saved strategies"""
    try:
        if not db_manager:
            return {'strategies': []}
        
        strategies = db_manager.get_all_strategies()
        
        return {
            'strategies': [s.to_dict() for s in strategies]
        }
        
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategy/active")
async def get_active_strategy():
    """Get currently active strategy"""
    try:
        if not db_manager:
            return {'strategy': None}
        
        strategy = db_manager.get_active_strategy()
        
        return {
            'strategy': strategy.to_dict() if strategy else None
        }
        
    except Exception as e:
        logger.error(f"Error getting active strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== TRADING CONTROL ENDPOINTS =====

@app.post("/api/trading/start")
async def start_trading(background_tasks: BackgroundTasks):
    """Start autonomous trading"""
    try:
        if not trading_engine:
            raise HTTPException(status_code=500, detail="Trading engine not initialized")
        
        if trading_engine.is_running:
            return {
                'success': False,
                'message': 'Trading engine already running'
            }
        
        # Start engine in background
        background_tasks.add_task(trading_engine.start)
        
        # Start status broadcast
        background_tasks.add_task(broadcast_status_updates)
        
        logger.info("🚀 Trading started")
        
        await ws_manager.broadcast({
            'type': 'trading_started',
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return {
            'success': True,
            'message': 'Trading started successfully'
        }
        
    except Exception as e:
        logger.error(f"Error starting trading: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trading/stop")
async def stop_trading():
    """Stop trading and close positions"""
    try:
        if not trading_engine:
            raise HTTPException(status_code=500, detail="Trading engine not initialized")
        
        if not trading_engine.is_running:
            return {
                'success': False,
                'message': 'Trading engine not running'
            }
        
        await trading_engine.stop()
        
        logger.info("🛑 Trading stopped")
        
        await ws_manager.broadcast({
            'type': 'trading_stopped',
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return {
            'success': True,
            'message': 'Trading stopped successfully'
        }
        
    except Exception as e:
        logger.error(f"Error stopping trading: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trading/status")
async def get_trading_status():
    """Get current trading status"""
    try:
        if not trading_engine:
            return {
                'is_running': False,
                'message': 'Trading engine not initialized'
            }
        
        status = trading_engine.get_status()
        
        return {
            'success': True,
            'status': status
        }
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== PERFORMANCE ENDPOINTS =====

@app.get("/api/performance")
async def get_performance():
    """Get trading performance metrics"""
    try:
        if not db_manager:
            return {'metrics': {}}
        
        # Get latest metrics
        latest_metrics = db_manager.get_latest_metrics()
        
        # Get trading statistics
        stats = db_manager.get_trading_statistics(days=30)
        
        return {
            'success': True,
            'metrics': latest_metrics.to_dict() if latest_metrics else {},
            'statistics': stats
        }
        
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performance/history")
async def get_performance_history(hours: int = 24):
    """Get performance history"""
    try:
        if not db_manager:
            return {'history': []}
        
        history = db_manager.get_metrics_history(hours=hours)
        
        return {
            'success': True,
            'history': [m.to_dict() for m in history]
        }
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== TRADE ENDPOINTS =====

@app.get("/api/trades")
async def get_trades(limit: int = 50, symbol: Optional[str] = None):
    """Get recent trades"""
    try:
        if not db_manager:
            return {'trades': []}
        
        trades = db_manager.get_recent_trades(limit=limit, symbol=symbol)
        
        return {
            'success': True,
            'trades': [t.to_dict() for t in trades]
        }
        
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trades/open")
async def get_open_trades(symbol: Optional[str] = None):
    """Get open trades"""
    try:
        if not db_manager:
            return {'trades': []}
        
        trades = db_manager.get_open_trades(symbol=symbol)
        
        return {
            'success': True,
            'trades': [t.to_dict() for t in trades]
        }
        
    except Exception as e:
        logger.error(f"Error getting open trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== COMPLIANCE ENDPOINTS =====

@app.get("/api/compliance/report")
async def get_compliance_report():
    """Generate hackathon compliance report"""
    try:
        checker = SafetyChecker()
        report = checker.generate_compliance_report()
        
        return {
            'success': True,
            'report': report
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compliance/logs")
async def get_compliance_logs(limit: int = 100):
    """Get AI decision logs for compliance"""
    try:
        checker = SafetyChecker()
        # This would read from the JSONL log file
        return {
            'success': True,
            'message': 'Logs available in logs/hackathon/ai_trading_log.jsonl'
        }
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== WEBSOCKET ENDPOINT =====

@app.websocket("/ws/live-feed")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    Sends: status updates, new trades, performance metrics, signals
    """
    await ws_manager.connect(websocket)
    
    try:
        # Send initial status
        if trading_engine:
            await ws_manager.send_to(websocket, {
                'type': 'initial_status',
                'data': trading_engine.get_status(),
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Keep connection alive
        while True:
            try:
                # Receive messages from client (for ping/pong)
                data = await websocket.receive_text()
                
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    
    finally:
        ws_manager.disconnect(websocket)

# ===== ERROR HANDLERS =====

@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={'error': str(exc), 'type': 'validation_error'}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={'error': 'Internal server error', 'detail': str(exc)}
    )

# ===== RUN SERVER =====

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
  )
