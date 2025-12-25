# 🚀 AI Trading SIGMA
> Experimental Autonomous Trading System with Risk-First Architecture

> Hybrid Design: Rule-Based Execution + Probabilistic Signals + AI-Assisted Analysis

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2-61DAFB.svg)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)
---
## 📋 Table of Contents
- [The Problem We Solve](#-the-problem-we-solve)
- [Our Solution](#-our-solution)
- [Key Innovations](#-key-innovations)
- [System Architecture](#-system-architecture)
- [Quick Start](#-quick-start)
- [Complete Features](#-complete-features)
- [Performance Metrics](#-performance-metrics)
- [API Documentation](#-api-documentation)
- [Repository Structure](#-repository-structure)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
---
## 🎯 The Problem We Solve
### Traditional Trading Bots Fail Because:
❌ **Fake Kelly Criterion**
- Use confidence scores as "win probability" (wrong!)
- Force minimum position size even with negative edge
- Assume static risk/reward ratios
❌ **Regime Blindness**
- Same strategy for trending vs choppy markets
- Oversize in volatility, undersize in trends
- No market condition awareness
❌ **No Learning**
- Don't track actual performance
- Can't detect strategy degradation
- Blow up slowly without warning
❌ **Dumb Exits**
- Only simple TP/SL
- No trailing stops
- No time-based or regime exits
❌ **Portfolio Risk Ignorance**
- No correlation management
- Overconcentration in correlated assets
- One-sided exposure risk
---
## ✅ Our Solution: AI Trading SIGMA
### **Proper Risk Management**
✅ Real Kelly Criterion using actual win rate from closed trades
✅ Regime-aware position sizing (trend vs range vs chop)
✅ Expectancy tracking with sample size confidence
✅ Zero position size if negative edge detected
### **Intelligent Execution**
✅ Dual-layer signals (probabilistic + rule-based)
✅ Portfolio correlation & concentration limits
✅ Dynamic exits (trailing, time-based, thesis validation)
✅ Strategy degradation detection
### **Production Safety**
✅ 4-level circuit breaker (ALERT → THROTTLE → HALT → SHUTDOWN)
✅ Multi-layer compliance validation
✅ Complete audit trail (JSONL logging)
✅ Real-time notifications
---
## 🔥 Key Innovations
### 1. **Proper Kelly Criterion** (Fixed!)
**❌ OLD (Wrong):**
```python
# Uses confidence as win probability - WRONG!
p = confidence_from_indicators  # 0.75
b = 2.5  # Assumed static
kelly = (p * b - q) / b
adjusted = max(0.1, kelly)  # Forces minimum!
```
**✅ NEW (Correct):**
```python
# Uses REAL win rate from closed trades
win_rate = get_win_rate_from_database()  # 0.68 from 45 trades
payoff_ratio = avg_win / avg_loss  # 2.15 actual
kelly = (win_rate * payoff_ratio - (1-win_rate)) / payoff_ratio
if kelly <= 0:
    return 0  # NO TRADE if no edge!
adjusted = kelly * 0.25  # Conservative 25% Kelly
```
### 2. **Regime-Aware Sizing**
```python
# Detect market regime
regime = detect_regime(df)  # TREND_UP, RANGE, CHOP, VOLATILE
# Adjust position size
risk_multipliers = {
    'TREND_UP': 1.3,      # Increase in trends
    'RANGE': 0.8,         # Reduce in ranges
    'CHOP': 0.4,          # Minimal in chop
    'VOLATILE': 0.3       # Very small in extreme vol
}
size = base_size * risk_multipliers[regime]
```
### 3. **Expectancy Engine**
Tracks **real performance** from closed trades:
```python
# After 30+ trades, use real data
expectancy_metrics = {
    'win_rate': 0.68,           # 68% from actual results
    'payoff_ratio': 2.15,       # Real avg_win/avg_loss
    'expectancy': +18.50,       # $18.50 per trade
    'sample_size': 45,
    'kelly_fraction': 0.523
}
# If sample_size < 30: use exploration mode (0.5% risk)
# If expectancy <= 0: NO TRADE (zero position size)
```
### 4. **Dynamic Exit Manager**
Beyond simple TP/SL:
```python
# Intelligent exits
exit_checks = [
    '✓ Stop Loss (always first)',
    '✓ Take Profit',
    '✓ Trailing Stop (regime-aware)',
    '✓ Time Limit (trend: 4h, range: 2h, chop: 1h)',
    '✓ Regime Change (trend → chop)',
    '✓ Portfolio Rebalance (>50% one-sided)',
    '✓ Thesis Invalidation (RSI oversold → overbought)'
]
```
### 5. **Portfolio Risk Manager**
Prevents correlated blow-ups:
```python
# Before executing trade
portfolio_checks = {
    'single_asset_limit': 40%,      # Max 40% in one asset
    'correlated_group_limit': 60%,  # BTC+ETH max 60%
    'sector_limit': 50%,            # Max 50% per sector
    'correlation_adjustment': True   # Risk scaled by correlation
}
```
### 6. **Strategy Monitor**
Detects degradation before disaster:
```python
# Every 5 cycles
degradation = check_degradation(recent_trades)
if degradation.severity == 'critical':
    circuit_breaker.halt()  # STOP trading
    alert('Strategy broken! Review immediately')
# Monitors:
# - Win rate collapse (< 35% critical)
# - Sharpe ratio degradation (< 0 critical)
# - Consecutive losses (>= 10 critical)
# - Expectancy turning negative
```
---
## 🏗️ System Architecture
### High-Level Flow
```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                         │
│         Dashboard | Charts | AI Chat | Real-time           │
└─────────────────────────────────────────────────────────────┘
                    ↕ REST + WebSocket
┌─────────────────────────────────────────────────────────────┐
│                 BACKEND API (FastAPI)                       │
│             30+ Endpoints | WebSocket Feed                  │
└─────────────────────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────────────────────┐
│              TRADING ENGINE (Autonomous)                    │
│  ┌──────────────────────────────────────────────────┐      │
│  │ 1. Market Scanner (Multiple Symbols)             │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │ 2. Signal Generation (V1 + V2 Dual Layer)        │      │
│  │    • V1: Probabilistic (category-based scoring)  │      │
│  │    • V2: Rule-based (explainable validation)     │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │ 3. Regime Detection                              │      │
│  │    • Classify: TREND_UP, TREND_DOWN, RANGE,      │      │
│  │      CHOP, VOLATILE                              │      │
│  │    • Calculate risk multiplier                   │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │ 4. Expectancy Engine                             │      │
│  │    • Track real win rate from closed trades      │      │
│  │    • Calculate actual payoff ratio               │      │
│  │    • Sample size validation (min 30 trades)      │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │ 5. Enhanced Risk Manager (PROPER KELLY)          │      │
│  │    IF (sample >= 30 & expectancy > 0):           │      │
│  │       • Use empirical Kelly                      │      │
│  │    ELSE:                                         │      │
│  │       • Exploration mode (0.5% risk)             │      │
│  │    × regime_multiplier × volatility_penalty      │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │ 6. Portfolio Risk Manager                        │      │
│  │    • Correlation matrix                          │      │
│  │    • Concentration limits                        │      │
│  │    • Sector exposure                             │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │ 7. Safety Checker (5-Layer Validation)           │      │
│  │    ✓ Symbol allowed? ✓ Leverage OK?              │      │
│  │    ✓ Risk OK? ✓ Balance OK? ✓ Daily loss OK?    │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │ 8. Circuit Breaker (4-Level Protection)          │      │
│  │    CLOSED → ALERT → THROTTLE → HALT → SHUTDOWN  │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │ 9. Execute Trade                                 │      │
│  │    • Create market order                         │      │
│  │    • Set SL/TP                                   │      │
│  │    • Log compliance                              │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │ 10. Dynamic Exit Manager                         │      │
│  │     • Trailing stops (regime-aware)              │      │
│  │     • Time-based exits                           │      │
│  │     • Regime change exits                        │      │
│  │     • Thesis invalidation                        │      │
│  │     • Portfolio rebalancing                      │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │ 11. Strategy Monitor (Every 5 Cycles)            │      │
│  │     • Detect win rate collapse                   │      │
│  │     • Sharpe degradation                         │      │
│  │     • Consecutive losses                         │      │
│  │     • Trigger circuit breaker if critical        │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
        ↕                           ↕
┌──────────────────┐      ┌──────────────────┐
│  AI (Optional)   │      │  Exchange API    │
│  Google Gemini   │      │  WEEX | Binance  │
└──────────────────┘      └──────────────────┘
```
### Decision Flow: How a Trade Happens
```
START: New market data arrives (every 5 minutes)
  ↓
┌─────────────────────────────────────┐
│ 1. MARKET SCANNER                   │
│    • Iterate through 8 allowed pairs│
│    • Find best setup                │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 2. INDICATOR CALCULATION            │
│    • RSI, MACD, Stochastic          │
│    • EMA, BB, ATR, ADX              │
│    • Monte Carlo simulation         │
│    • Garman-Klass volatility        │
│    • Z-Score, Linear Regression     │
│    Time: ~70ms                      │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 3. SIGNAL GENERATION                │
│    V1 (Probabilistic):              │
│    • Category-based scoring         │
│    • Continuous values [-1, 1]      │
│    • Volatility adjustment          │
│    ↓                                │
│    V2 (Rule-Based):                 │
│    • Clear indicator rules          │
│    • Explainable reasoning          │
│    • Validation & confirmation      │
│    ↓                                │
│    Orchestrator:                    │
│    • Combine V1 + V2                │
│    • Final confidence               │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 4. REGIME DETECTION                 │
│    • Classify market state          │
│    • Calculate risk multiplier      │
│    • Check if should trade          │
└─────────────────────────────────────┘
  ↓ (if signal confidence >= threshold)
┌─────────────────────────────────────┐
│ 5. EXPECTANCY CHECK                 │
│    • Query closed trades from DB    │
│    • Calculate real win rate        │
│    • Calculate payoff ratio         │
│    • Check sample size >= 30        │
│    • Return Kelly inputs OR None    │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 6. POSITION SIZING                  │
│    IF (Kelly inputs available):     │
│       • Use proper Kelly Criterion  │
│       • kelly = (p*b - q) / b       │
│       • adjusted = kelly * 0.25     │
│    ELSE:                            │
│       • Exploration mode (0.5%)     │
│    × regime_multiplier              │
│    × volatility_penalty             │
│    IF (expectancy <= 0): size = 0   │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 7. PORTFOLIO RISK VALIDATION        │
│    • Check single asset limit       │
│    • Check correlated group limit   │
│    • Check sector concentration     │
│    • Block if exceeds limits        │
└─────────────────────────────────────┘
  ↓ (if portfolio risk OK)
┌─────────────────────────────────────┐
│ 8. SAFETY VALIDATION                │
│    ✓ Symbol in allowed list?        │
│    ✓ Leverage <= 20x?               │
│    ✓ Position size reasonable?      │
│    ✓ Sufficient balance?            │
│    ✓ Daily loss limit not hit?      │
│    Block if ANY check fails         │
└─────────────────────────────────────┘
  ↓ (if all checks pass)
┌─────────────────────────────────────┐
│ 9. CIRCUIT BREAKER CHECK            │
│    • Current state: CLOSED/ALERT/   │
│      THROTTLE/HALT/SHUTDOWN?        │
│    • Block if HALT or SHUTDOWN      │
│    • Reduce if THROTTLE             │
└─────────────────────────────────────┘
  ↓ (if allowed)
┌─────────────────────────────────────┐
│ 10. ORDER EXECUTION                 │
│     • Create market order           │
│     • Set stop loss                 │
│     • Set take profit               │
│     • Save to database              │
│     • Log compliance (JSONL)        │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 11. POSITION MANAGEMENT (Loop)      │
│     Every 5 seconds:                │
│     • Fetch current price           │
│     • Update highest/lowest         │
│     • Detect current regime         │
│     • Check dynamic exits:          │
│       - Stop loss                   │
│       - Take profit                 │
│       - Trailing stop               │
│       - Time limit                  │
│       - Regime change               │
│       - Portfolio rebalance         │
│       - Thesis invalidation         │
│     • Close if exit condition met   │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 12. STRATEGY MONITORING             │
│     Every 5 cycles (25 seconds):    │
│     • Get last 100 closed trades    │
│     • Check degradation:            │
│       - Win rate < 35%?             │
│       - Sharpe ratio < 0?           │
│       - Consecutive losses >= 10?   │
│       - Expectancy negative?        │
│     • If critical: HALT trading     │
└─────────────────────────────────────┘
  ↓
LOOP: Wait 5 seconds, repeat from START
```
---
## 🚀 Quick Start
### Prerequisites
- **Python 3.9+**
- **Node.js 18+**
- **WEEX or Binance Account** (testnet recommended)
- **Google Gemini API Key** (optional, for AI chat)
### 1. Clone Repository
```bash
git clone https://github.com/RivalismeUniverse/AI_Trading_Sigma-V.01.git
cd ai-trading-sigma
```
### 2. Backend Setup
```bash
cd backend
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
# Configure environment
cp .env.example .env
nano .env  # Add your API keys
```
**Required `.env` variables:**
```bash
# Exchange (Choose one)
EXCHANGE=weex  # or binance
# WEEX
WEEX_API_KEY=your_key
WEEX_API_SECRET=your_secret
WEEX_TESTNET=true
# Google Gemini (Optional - for AI chat)
GEMINI_API_KEY=your_gemini_key
# Trading
DEFAULT_SYMBOL=BTC/USDT:USDT
DEFAULT_LEVERAGE=10
MAX_RISK_PER_TRADE=0.02
MAX_DAILY_LOSS=0.05
```
### 3. Start Backend
```bash
python main.py
```
You should see:
```
✅ Hybrid Trading Engine initialized with prop-firm grade components
✅ Engine initialized with weex
💰 Starting balance: $10,000.00
🚀 Starting autonomous trading in SCANNER MODE...
```
### 4. Frontend Setup (New Terminal)
```bash
cd frontend
# Install dependencies
npm install
# Copy environment
cp .env.example .env.local
# Start frontend
npm start
```
### 5. Access Application
Open browser: **http://localhost:3000**
✅ You're ready to trade!
---
## 📦 Complete Features
### Signal Generation
**16 Technical Indicators:**
- **Basic (12):** RSI, MACD, Stochastic, EMA (9/20/50/200), SMA, Bollinger Bands, ATR, ADX, CCI, MFI, OBV, VWAP
- **Advanced (4):** Monte Carlo Simulation, Garman-Klass Volatility, Z-Score Mean Reversion, Linear Regression Slope
**Dual-Layer System:**
- **V1 (Probabilistic):** Category-based scoring, continuous values, volatility-aware
- **V2 (Rule-Based):** Clear rules, explainable reasoning, compliance-focused
- **Orchestrator:** Combines both for optimal decisions
### Risk Management
**Expectancy Engine:**
- Tracks real win rate from closed trades
- Calculates actual payoff ratio (avg_win / avg_loss)
- Sample size validation (minimum 30 trades)
- Rolling windows (30/100/500 trades)
**Enhanced Risk Manager:**
- Proper Kelly Criterion (uses real data, not confidence)
- Exploration mode for < 30 trades (0.5% risk)
- Zero position size if expectancy <= 0
- Regime-aware multipliers (0.3x - 1.5x)
- Volatility penalties
**Portfolio Risk Manager:**
- Correlation matrix (BTC+ETH = 0.85)
- Single asset limit (40% max)
- Correlated group limit (60% max)
- Sector concentration (50% max)
- Correlation-adjusted portfolio heat
### Regime Detection
**Market Classifications:**
- **TREND_UP:** ADX > 30, bullish EMA alignment
- **TREND_DOWN:** ADX > 30, bearish EMA alignment
- **RANGE:** ADX < 20, low volatility
- **CHOP:** ADX < 20, high volatility
- **VOLATILE:** GK volatility > 0.8
**Risk Multipliers:**
- Trend: 1.3x (increase size)
- Range: 0.8x (reduce size)
- Chop: 0.4x (minimal size)
- Volatile: 0.3x (very small)
### Dynamic Exits
**7 Exit Conditions (Beyond TP/SL):**
1. **Stop Loss** (always checked first)
2. **Take Profit**
3. **Trailing Stop** (regime-aware: 1-2.5%)
4. **Time Limit** (trend: 4h, range: 2h, chop: 1h)
5. **Regime Change** (trend → chop)
6. **Portfolio Rebalance** (>50% one-sided)
7. **Thesis Invalidation** (RSI oversold → overbought)
### Strategy Monitoring
**Degradation Detection:**
- Win rate collapse (< 35% critical)
- Sharpe ratio degradation (< 0 critical)
- Consecutive losses (>= 10 critical)
- Expectancy turning negative
- Triggers circuit breaker if critical
**Severity Levels:**
- **Minor:** Monitor closely
- **Moderate:** Reduce size 50%
- **Severe:** HALT new entries
- **Critical:** EMERGENCY HALT
### Circuit Breaker
**4-Level Graduated Protection:**
- **CLOSED:** Normal operation
- **ALERT:** Warning, continue with caution
- **THROTTLE:** Reduced operation (high confidence only)
- **HALT:** Emergency stop (close positions only)
- **SHUTDOWN:** Fatal error (manual restart required)
**Triggers:**
- API latency (500ms → 1s → 3s)
- Order failures (2 → 3 → 5 → 10)
- Slippage (0.1% → 0.3% → 0.5%)
- Strategy degradation (new!)
- Expectancy collapse (new!)
### Safety & Compliance
**5-Layer Validation:**
1. Symbol allowed? (8 pairs only)
2. Leverage <= 20x?
3. Position size reasonable?
4. Sufficient balance?
5. Daily loss limit not hit?
**Complete Audit Trail:**
- Every AI decision logged (JSONL)
- Safety violations logged
- Execution failures logged
- P&L tracking per trade
---
---
## 🗂️ Repository Structure
```
ai-trading-sigma/
│
├── README.md                          # This file
├── LICENSE                            # MIT License
├── docker-compose.yml                 # Docker orchestration
│
├── backend/                           # Python Backend
│   ├── main.py                        # FastAPI entry point (30+ endpoints)
│   ├── config.py                      # Configuration management
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Environment template
│   │
│   ├── core/                          # Trading Engine Core
│   │   ├── hybrid_engine.py           # Main autonomous loop (UPGRADED)
│   │   ├── signal_generator_v1.py     # Probabilistic engine
│   │   ├── signal_validator_v2.py     # Rule-based validator
│   │   ├── integrated_signal_manager.py  # Orchestrator
│   │   │
│   │   ├── expectancy_engine.py       # 🆕 Real performance tracking
│   │   ├── regime_detector.py         # 🆕 Market classification
│   │   ├── enhanced_risk_manager.py   # 🆕 PROPER Kelly + regime
│   │   ├── portfolio_risk_manager.py  # 🆕 Correlation & concentration
│   │   ├── strategy_monitor.py        # 🆕 Degradation detection
│   │   ├── dynamic_exit_manager.py    # 🆕 Smart exits
│   │   │
│   │   ├── circuit_breaker.py         # 4-level protection (UPGRADED)
│   │   ├── notification_system.py     # Multi-channel alerts
│   │   └── api_monitor.py             # Performance tracking
│   │
│   ├── strategies/                    # Trading Strategies
│   │   └── technical_indicators.py    # 16 indicators (12 basic + 4 advanced)
│   │
│   ├── exchange/                      # Exchange Integration
│   │   ├── base_client.py             # Abstract base
│   │   ├── weex_client.py             # WEEX implementation
│   │   ├── binance_client.py          # Binance implementation
│   │   └── safety_checker.py          # 5-layer compliance
│   │
│   ├── ai/                            # AI Integration (Optional)
│   │   └── bedrock_client.py          # Google Gemini client
│   │
│   ├── database/                      # Database Layer
│   │   ├── models.py                  # SQLAlchemy models (6 tables)
│   │   └── db_manager.py              # CRUD operations
│   │
│   ├── utils/                         # Utilities
│   │   ├── logger.py                  # Logging system
│   │   ├── constants.py               # Trading constants
│   │   ├── validators.py              # Input validation
│   │   └── helpers.py                 # Helper functions
│   │
│   └── tests/                         # Testing Suite
│       ├── test_hybrid_engine.py
│       ├── conftest.py
│       └── pytest.ini
│
├── frontend/                          # React Frontend
│   ├── public/
│   │   └── index.html
│   │
│   ├── src/
│   │   ├── App.jsx                    # Main application
│   │   ├── index.js                   # Entry point
│   │   ├── index.css                  # Global styles
│   │   │
│   │   ├── components/                # UI Components
│   │   │   ├── Header.jsx
│   │   │   ├── MetricsRow.jsx
│   │   │   ├── ChartWidget.jsx
│   │   │   ├── OpenPositionsWidget.jsx
│   │   │   ├── RecentTradesWidget.jsx
│   │   │   ├── SignalsWidget.jsx
│   │   │   ├── CircuitBreakerWidget.jsx
│   │   │   ├── PerformanceWidget.jsx
│   │   │   ├── NotificationPanel.jsx
│   │   │   ├── AIChat.jsx
│   │   │   └── FloatingAIButton.jsx
│   │   │
│   │   └── services/                  # API Services
│   │       ├── api.js                 # REST client
│   │       └── websocket.js           # WebSocket service
│   │
│   ├── package.json                   # NPM dependencies
│   ├── tailwind.config.js             # Tailwind config
│   └── .env.example                   # Frontend env template
│
├── logs/                              # Log Files
│   ├── hackathon/                     # Compliance logs (CRITICAL)
│   │   ├── ai_trading_log.jsonl       # Every AI decision
│   │   ├── safety_violations.jsonl    # Blocked trades
│   │   ├── execution_failures.jsonl   # Failed executions
│   │   └── pnl_tracking.jsonl         # P&L per trade
│   └── trading_bot.log                # General logs
│
└── docs/                              # Documentation
    ├── SETUP_GUIDE.md                 # Complete setup
    ├── SIGNAL_ARCHITECTURE.md         # Signal system deep dive
    ├── CIRCUIT_BREAKER_GUIDE.md       # CB usage guide
    └── DEPLOYMENT.md                  # Production deployment
```
---
## 🔧 API Documentation
### REST API Endpoints
**Full documentation:** `http://localhost:8000/docs` (Swagger UI)
#### Trading Control
```bash
POST   /api/trading/start              # Start autonomous trading
POST   /api/trading/stop               # Stop trading
GET    /api/trading/status             # Get bot status
```
#### Strategy Management
```bash
POST   /api/strategy/create            # Generate strategy (AI)
POST   /api/strategy/apply             # Apply strategy
GET    /api/strategy/list              # List strategies
GET    /api/strategy/active            # Get active strategy
```
#### Performance & Analytics
```bash
GET    /api/performance                # Current metrics
GET    /api/performance/history        # Historical data
GET    /api/balance                    # Account balance
GET    /api/trades                     # Trade history
GET    /api/trades/open                # Open positions
```
#### Circuit Breaker
```bash
GET    /api/circuit-breaker/status     # CB status
GET    /api/circuit-breaker/issues     # Recent issues
POST   /api/circuit-breaker/recover    # Force recovery
POST   /api/circuit-breaker/override   # Manual override
```
#### Notifications
```bash
GET    /api/notifications              # Recent notifications
POST   /api/notifications/{id}/read    # Mark as read
DELETE /api/notifications              # Clear all
```
#### AI Chat (Optional)
```bash
POST   /api/chat                       # Chat with AI
```
### WebSocket Events
**Connection:** `ws://localhost:8000/ws/live-feed`
**Event Types:**
```javascript
{
  type: "status_update",
  data: {
    is_running: true,
    balance: 10000,
    open_positions: 2,
    total_pnl: 234.56
  }
}
{
  type: "new_trade",
  data: {
    symbol: "BTC/USDT:USDT",
    action: "ENTER_LONG",
    price: 50000,
    size: 0.001,
    regime: "TREND_UP"
  }
}
{
  type: "circuit_breaker_alert",
  data: {
    state: "ALERT",
    issue_type: "api_latency",
    severity: "warning"
  }
}
```
---
## 🚀 Deployment
### Development
```bash
# Terminal 1 - Backend
cd backend
python main.py
# Terminal 2 - Frontend
cd frontend
npm start
```
**Access:** http://localhost:3000
### Production (Docker)
```bash
# Build and start
docker-compose up -d
# View logs
docker-compose logs -f
# Stop
docker-compose down
```
### Production (Manual)
```bash
# Backend
cd backend
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
# Frontend
cd frontend
npm run build
# Serve build/ with nginx
```
---
## 🐛 Troubleshooting
### Backend Issues
**Problem:** Backend won't start
```bash
# Check Python version
python --version  # Should be 3.9+
# Reinstall dependencies
pip install -r requirements.txt
# Check .env configuration
cat .env | grep API_KEY
```
**Problem:** Database errors
```bash
# Delete database (WARNING: loses data)
rm trading_data.db
# Restart backend
python main.py
```
**Problem:** Exchange connection failed
```bash
# Verify API keys in .env
# Make sure testnet=true for testing
# Check if exchange API is accessible
# Test connection
python -c "from exchange.weex_client import WEEXClient; print('OK')"
```
### Frontend Issues
**Problem:** Frontend won't start
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
# Start again
npm start
```
**Problem:** WebSocket not connecting
```bash
# Check backend is running
curl http://localhost:8000/api/health
# Check CORS settings in main.py
# Verify REACT_APP_WS_URL in .env.local
```
### Trading Issues
**Problem:** No trades executing
```bash
# Check bot status
curl http://localhost:8000/api/trading/status
# Check circuit breaker
curl http://localhost:8000/api/circuit-breaker/status
# Check recent trades (need 30+ for proper Kelly)
curl http://localhost:8000/api/trades
# Review logs
tail -f logs/trading_bot.log
tail -f logs/hackathon/safety_violations.jsonl
```
**Problem:** Position size is zero
```bash
# This is NORMAL if:
# 1. Less than 30 closed trades (exploration mode with tiny sizes)
# 2. Expectancy is negative (no edge detected)
# 3. Regime is CHOP or VOLATILE (very small multipliers)
# Check expectancy
# Look in logs for: "Expectancy: $X.XX per trade"
# If negative, bot correctly refuses to trade!
```
**Problem:** Circuit breaker in HALT
```bash
# Check issues
curl http://localhost:8000/api/circuit-breaker/issues
# Wait for cooldown (15 minutes default)
# Or force recovery (if you're sure it's safe)
curl -X POST http://localhost:8000/api/circuit-breaker/recover
```
---
## 📈 Performance Analysis
### Reading the Logs
**Expectancy Metrics:**
```bash
tail -f logs/trading_bot.log | grep "Expectancy"
# Good output:
Expectancy: $18.50 per trade (n=45)
Kelly inputs: WR=0.68, PR=2.15, Kelly=0.523, n=45
# Bad output:
Expectancy: $-5.20 per trade (n=52)
# → Bot will correctly refuse to trade!
```
**Regime Detection:**
```bash
tail -f logs/trading_bot.log | grep "Regime:"
# Output:
Regime: TREND_UP (conf=0.85, risk_mult=1.30)
Regime: RANGE (conf=0.72, risk_mult=0.80)
Regime: CHOP (conf=0.68, risk_mult=0.40)
```
**Position Sizing:**
```bash
tail -f logs/trading_bot.log | grep "Position size"
# Output:
Position size: 0.001234 | Method: empirical_kelly | 
Regime mult: 1.30 | Vol penalty: 1.00
```
**Strategy Health:**
```bash
tail -f logs/trading_bot.log | grep "degradation"
# Good:
Strategy performing normally. Continue monitoring.
# Warning:
⚠️ Strategy degradation: moderate
Moderate degradation detected. Reduce position sizes by 50%
# Critical:
⚠️ Strategy degradation: critical
CRITICAL degradation. EMERGENCY HALT. Close all positions.
```
### Dashboard Metrics
**Key Metrics to Watch:**
1. **Win Rate:** Should be 60-75%
   - < 50%: Strategy may be degrading
   - < 35%: Critical - circuit breaker should trigger
2. **Sharpe Ratio:** Should be > 1.0
   - 1.5-2.5: Excellent
   - 0.5-1.5: Good
   - < 0.5: Review strategy
3. **Expectancy:** Should be positive
   - > $10/trade: Excellent
   - $0-$10: OK but marginal
   - < $0: Bot should HALT
4. **Sample Size:** Need 30+ for proper Kelly
   - < 30: Exploration mode (tiny sizes)
   - 30-100: Building confidence
   - > 100: Full Kelly
5. **Max Drawdown:** Should be < 10%
   - 2-5%: Excellent control
   - 5-10%: Acceptable
   - > 10%: Risk management issue
---
## 🎓 Educational Resources
### Understanding the System
**New to Algorithmic Trading?**
1. Start with `docs/SETUP_GUIDE.md`
2. Read `docs/SIGNAL_ARCHITECTURE.md`
3. Understand `docs/CIRCUIT_BREAKER_GUIDE.md`
**Key Concepts:**
**Kelly Criterion:**
- Formula: `f = (p*b - q) / b`
- `p` = win probability (from real trades!)
- `b` = payoff ratio (avg_win / avg_loss)
- `f` = fraction of capital to risk
**Expectancy:**
- `E = (Win_Rate × Avg_Win) - (Loss_Rate × Avg_Loss)`
- Must be positive for profitable trading
- Example: `(0.68 × $50) - (0.32 × $20) = $27.60`
**Regime Detection:**
- Markets have different states
- Same strategy won't work in all regimes
- Adapt position size to regime
**Portfolio Risk:**
- Don't overconcentrate in correlated assets
- BTC + ETH = 85% correlated
- If BTC drops, ETH likely drops too
---
## 🤝 Contributing
We welcome contributions! Here's how:
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes with tests
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open Pull Request
**Development Guidelines:**
- Follow PEP 8 for Python
- Use ESLint for JavaScript
- Write tests for new features
- Update documentation
- Add type hints
---
## 📝 Changelog
### Version 1.0.0 (Current) - 
**Major Upgrades:**
- ✅ Fixed Kelly Criterion (uses real win rate)
- ✅ Added Expectancy Engine (performance tracking)
- ✅ Added Regime Detector (market classification)
- ✅ Enhanced Risk Manager (proper Kelly + regime)
- ✅ Portfolio Risk Manager (correlation limits)
- ✅ Strategy Monitor (degradation detection)
- ✅ Dynamic Exit Manager (smart exits)
- ✅ Upgraded Circuit Breaker (strategy monitoring)
**Breaking Changes:**
- Risk Manager interface changed (added regime_result param)
- Position sizing logic completely rewritten
- Exit logic enhanced (more exit conditions)
**Migration:**
- Existing databases compatible
- Old risk_manager.py still exists as fallback
- Gradual rollout recommended
### Version 1.0.0 - Initial Release
**Features:**
- Dual-layer signal system (V1 + V2)
- 16 technical indicators
- Basic risk management
- Circuit breaker (4 levels)
- Safety checker (5 layers)
- Real-time dashboard
---
## ⚠️ Disclaimer
**FOR EDUCATIONAL PURPOSES ONLY**
- This software is provided for educational and research purposes
- Trading involves substantial risk of loss
- Past performance does not guarantee future results
- Never trade with money you cannot afford to lose
- Always start with testnet/demo accounts
- Use proper risk management
- Not financial advice
> Note: The following architecture represents the intended system design. 
Some modules are experimental or partially implemented for hackathon purposes.

**NO WARRANTY**
This software is provided "AS IS" without warranty of any kind. The authors are not responsible for any losses incurred from using this software.
---
## 📄 License
MIT License
Copyright (c) 2025 AI Trading SIGMA
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
---
## 🙏 Acknowledgments
- **WEEX/WOO X** - Exchange integration
- **Google Gemini** - AI integration
- **FastAPI** - Excellent web framework
- **React** - UI library
- **Tailwind CSS** - Beautiful styling
- **CCXT** - Exchange abstraction
- **All contributors** - Thank you!
---
## 📞 Support & Contact
**Questions?**
- 📖 Check `docs/` folder
- 🐛 Open an issue on GitHub
- 💬 Join our Discord (coming soon)
**For Developers:**
- API Docs: http://localhost:8000/docs
- Architecture: `docs/SIGNAL_ARCHITECTURE.md`
- Setup Guide: `docs/SETUP_GUIDE.md`
---
## 🎯 Project Goals
**Our Mission:**
Build a trading system that:
1. ✅ Uses **proper mathematics** (Kelly, expectancy)
2. ✅ Learns from **real results** (not backtests)
3. ✅ Adapts to **market conditions** (regime detection)
4. ✅ Manages **portfolio risk** (correlation awareness)
5. ✅ Detects **strategy failure** (before disaster)
6. ✅ Operates **autonomously** (minimal supervision)
**What We're NOT:**
- ❌ Get-rich-quick scheme
- ❌ Holy grail strategy
- ❌ Guaranteed profits
- ❌ High-frequency trading
- ❌ Market manipulation
**What We ARE:**
- ✅ Educational tool for algorithmic trading
- ✅ Production-grade architecture
- ✅ Proper risk management implementation
- ✅ Open-source and transparent
- ✅ Continuously improving
---
## 🚀 Future Roadmap
**Phase 1: Optimization (Q1 2026)**
- [ ] Machine learning prediction layer
- [ ] Multi-timeframe analysis
- [ ] Sentiment analysis integration
- [ ] Advanced backtesting engine
**Phase 2: Expansion (Q2 2026)**
- [ ] More exchange integrations
- [ ] Options trading support
- [ ] Portfolio optimization
- [ ] Social trading features
**Phase 3: Enterprise (Q3 2026)**
- [ ] Multi-user support
- [ ] White-label licensing
- [ ] Advanced analytics dashboard
- [ ] Institutional features
---
## 📊 System Requirements
**Minimum:**
- CPU: 2 cores
- RAM: 2GB
- Storage: 10GB
- Network: Stable internet
**Recommended:**
- CPU: 4+ cores
- RAM: 4GB
- Storage: 20GB SSD
- Network: Low-latency connection
**For Production:**
- CPU: 8+ cores
- RAM: 8GB+
- Storage: 50GB+ SSD
- Network: Dedicated server
- Monitoring: 24/7 uptime monitoring
---
## 🎓 Learn More
**Recommended Reading:**
1. "The Kelly Criterion in Blackjack Sports Betting and the Stock Market" - Edward O. Thorp
2. "Quantitative Trading" - Ernest P. Chan
3. "Algorithmic Trading" - Andreas F. Clenow
4. "Trading Systems and Methods" - Perry Kaufman
**Online Resources:**
- QuantStart: https://quantstart.com
- Investopedia: https://investopedia.com
- QuantConnect: https://quantconnect.com
---
## ✨ Why AI Trading SIGMA?
**Traditional Bots:**
- Use confidence as win rate ❌
- Ignore market regimes ❌
- Don't learn from results ❌
- Simple TP/SL only ❌
- Blow up slowly ❌
**AI Trading SIGMA:**
- Uses real win rate from trades ✅
- Adapts to market regimes ✅
- Tracks expectancy & degradation ✅
- Smart dynamic exits ✅
- Fails fast and safely ✅
---
**Built with ❤️ for algorithmic traders**
**Status:** Go to Production Ready ✅  
**Version:** 1.0.0  
**Last Updated:** December 2025
---
**Ready to start trading scientifically?**
```bash
git clone 
https://github.com/RivalismeUniverse/AI_Trading_Sigma-V.01.git
cd ai-trading-sigma
# Follow Quick Start guide above
```
**Happy Trading! 🚀📈**
