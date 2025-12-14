# 🤖 AI_Trading_Sigma-V.01

> **Autonomous AI-powered trading bot for WEEX Trading Hackathon (DoraHacks)**
> 
> **Hybrid Architecture:** 90% Python (speed) + 10% AI (intelligence)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [WEEX Hackathon Compliance](#-weex-hackathon-compliance)
- [Development](#-development)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🎯 Core Features
- **Autonomous Trading:** Bot trades automatically 24/7 without manual intervention
- **AI Strategy Generation:** Create strategies from natural language prompts
- **Hybrid Intelligence:** Python for speed + AWS Bedrock Claude for strategy
- **Real-time Monitoring:** Live dashboard with WebSocket updates
- **Risk Management:** Multi-layer safety checks and position sizing
- **WEEX Compliance:** Built-in hackathon rules enforcement

### 🤖 AI Capabilities
- **Chat Interface:** Ask questions, get market analysis, strategy advice
- **Strategy Generation:** "Create RSI oversold strategy for BTC" → Complete strategy
- **Periodic Review:** AI analyzes performance every 6 hours
- **Market Analysis:** Deep market intelligence and context awareness
- **Decision Logging:** Full AI decision trail for hackathon compliance

### 📊 Technical Features
- **9-Phase Technical Analysis:** RSI, MACD, EMA, Bollinger Bands, ATR, Stochastic, ADX, CCI, MFI
- **Backtesting Engine:** Test strategies on historical data
- **Position Management:** Automatic stop loss, take profit, trailing stops
- **Database Tracking:** Complete trade history and performance metrics
- **Safety Checker:** Validates all orders against WEEX rules

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND (React + Tailwind)                            │
│  ┌──────────────────┐  ┌────────────────────────────┐  │
│  │ Chat Interface   │  │ Dashboard                  │  │
│  │ (AI Interaction) │  │ (Live Monitoring)          │  │
│  └──────────────────┘  └────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↕ WebSocket + REST
┌─────────────────────────────────────────────────────────┐
│  BACKEND (Python FastAPI)                               │
│  ┌────────────────────────────────────────────────────┐ │
│  │ HybridTradingEngine (Autonomous Loop)              │ │
│  │ ├─ Fetch data every 5s                             │ │
│  │ ├─ Calculate indicators (Python - FAST)            │ │
│  │ ├─ Generate signals                                │ │
│  │ ├─ Validate with SafetyChecker                     │ │
│  │ ├─ Execute trades                                  │ │
│  │ └─ AI review every 6h                              │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│  EXTERNAL SERVICES                                       │
│  ├─ AWS Bedrock (Claude 3.5 Sonnet)                     │
│  └─ WEEX Exchange API (via CCXT)                        │
└─────────────────────────────────────────────────────────┘
```

### Key Design Principles
1. **Autonomous First:** Bot trades independently, user monitors via chat
2. **Speed Where It Matters:** Python for real-time calculations
3. **AI Where It Helps:** Strategy generation, periodic analysis, chat
4. **Safety Obsessed:** Multiple validation layers before every trade
5. **Fully Transparent:** Complete logging for hackathon evaluation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ 
- Node.js 18+ (for frontend)
- AWS Account (free tier works)
- WEEX Account with API keys

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/yourusername/weex-ai-scalping-bot.git
cd weex-ai-scalping-bot

# Backend setup
cd backend
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required variables:**
```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1

WEEX_API_KEY=your_key
WEEX_API_SECRET=your_secret
WEEX_TESTNET=true  # Start with testnet!

DEFAULT_SYMBOL=BTC/USDT:USDT
```

### 3. Run

```bash
# Terminal 1: Start backend
cd backend
python main.py

# Terminal 2: Start frontend
cd frontend
npm start
```

Open **http://localhost:3000** and start trading! 🎉

---

## 📦 Installation

### Detailed Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from database.models import create_tables; from sqlalchemy import create_engine; create_tables(create_engine('sqlite:///trading_bot.db'))"

# Run tests (optional)
pytest tests/
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env.local

# Build for production (optional)
npm run build
```

### Docker Setup (Alternative)

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## ⚙️ Configuration

### Trading Parameters

Edit `.env` to configure:

```bash
# Risk Management
MAX_RISK_PER_TRADE=0.02  # 2% per trade
MAX_DAILY_LOSS=0.05      # 5% max daily loss
MAX_POSITIONS=3          # Concurrent positions
DEFAULT_LEVERAGE=10      # 10x leverage

# AI Configuration
AI_MODE=hybrid           # hybrid / python_only / ai_only
AI_STRATEGY_REVIEW_HOURS=6
AI_CONFIDENCE_THRESHOLD=0.7

# Strategy Parameters
RSI_OVERSOLD=30
RSI_OVERBOUGHT=70
EMA_FAST_PERIOD=9
EMA_SLOW_PERIOD=20
```

### Strategy Configuration

Strategies can be configured via:
1. **Chat Interface:** "Create strategy with RSI < 30 and MACD bullish"
2. **Config File:** `config/strategy.json`
3. **Database:** Saved strategies in SQLite/PostgreSQL

---

## 💬 Usage

### Basic Workflow

1. **Open Dashboard:** http://localhost:3000

2. **Create Strategy via Chat:**
   ```
   "Create an RSI oversold strategy for BTC with 10x leverage"
   ```

3. **AI Generates Strategy:**
   - Analyzes your request
   - Creates complete configuration
   - Shows strategy in chat

4. **Apply Strategy:**
   - Click "Apply Strategy" button
   - Or say: "Apply this strategy"

5. **Start Trading:**
   - Say: "Start trading"
   - Bot begins autonomous execution
   - Monitor via dashboard

6. **Ask Questions:**
   ```
   "How's performance today?"
   "Why did you enter that BTC trade?"
   "What's the current market condition?"
   ```

7. **Stop Trading:**
   ```
   "Stop trading and close positions"
   ```

### Example Conversations

**Strategy Creation:**
```
User: Create a scalping strategy using RSI oversold and EMA crossover
AI: I've created a strategy with:
    - Entry: RSI < 30 and price above EMA20
    - Exit: RSI > 70 or EMA9 crosses below EMA20
    - Risk: 2% per trade, 10x leverage
    [Apply Strategy] button
```

**Performance Query:**
```
User: How many trades today and what's the P&L?
AI: Today's Performance:
    - Total Trades: 8
    - Winning Trades: 6 (75% win rate)
    - Total P&L: +$234.50 (+2.35%)
    - Best Trade: BTC/USDT +$78.20
```

**Market Analysis:**
```
User: Should I be trading right now?
AI: Current Market Analysis:
    - BTC: Consolidating near $50,000
    - RSI: 45 (neutral)
    - Volume: Below average
    - Recommendation: Wait for clearer signals
    Current conditions favor patience.
```

---

## 📚 API Documentation

### REST Endpoints

#### **Chat**
```http
POST /api/chat
Content-Type: application/json

{
  "message": "Create RSI strategy",
  "context": {}
}
```

#### **Strategy**
```http
POST /api/strategy/create
{
  "user_prompt": "Create momentum strategy for ETH"
}

POST /api/strategy/apply
{
  "strategy_config": { ... }
}

GET /api/strategy/list
GET /api/strategy/active
```

#### **Trading Control**
```http
POST /api/trading/start
POST /api/trading/stop
GET /api/trading/status
```

#### **Performance**
```http
GET /api/performance
GET /api/performance/history?hours=24
GET /api/trades?limit=50
GET /api/trades/open
```

#### **Compliance**
```http
GET /api/compliance/report
GET /api/compliance/logs
```

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live-feed');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'status_update':
      // Update dashboard
      break;
    case 'new_trade':
      // Show new trade
      break;
    case 'performance_update':
      // Update metrics
      break;
  }
};
```

Full API docs: **http://localhost:8000/docs** (Swagger UI)

---

## 📂 Project Structure

```
weex-ai-scalping-bot/
├── backend/
│   ├── main.py                    # FastAPI server
│   ├── config.py                  # Configuration
│   ├── ai/                        # AI components
│   │   ├── bedrock_client.py      # AWS Bedrock
│   │   └── prompt_processor.py    # Strategy generation
│   ├── core/                      # Core engine
│   │   ├── hybrid_engine.py       # Main trading loop
│   │   ├── signal_generator.py    # Signal generation
│   │   └── risk_manager.py        # Risk management
│   ├── strategies/                # Trading strategies
│   │   ├── scalping_strategy.py   # 9-phase strategy
│   │   └── technical_indicators.py # TA calculations
│   ├── exchange/                  # Exchange integration
│   │   ├── weex_client.py         # WEEX API
│   │   ├── safety_checker.py      # Compliance
│   │   └── order_manager.py       # Order management
│   ├── database/                  # Database
│   │   ├── models.py              # SQLAlchemy models
│   │   └── db_manager.py          # CRUD operations
│   └── utils/                     # Utilities
│
├── frontend/
│   ├── src/
│   │   ├── components/            # React components
│   │   │   ├── ChatInterface.jsx  # Chat UI
│   │   │   └── Dashboard.jsx      # Dashboard
│   │   ├── services/              # API services
│   │   └── App.jsx                # Main app
│   └── package.json
│
├── logs/
│   └── hackathon/                 # Compliance logs
│       ├── ai_trading_log.jsonl   # AI decisions
│       └── safety_violations.jsonl
│
├── .env.example                   # Environment template
├── docker-compose.yml             # Docker setup
├── README.md                      # This file
└── requirements.txt               # Python deps
```

---

## 🏆 WEEX Hackathon Compliance

### Mandatory Rules

1. **✅ Allowed Trading Pairs (ONLY 8):**
   - ADA/USDT:USDT
   - SOL/USDT:USDT
   - LTC/USDT:USDT
   - DOGE/USDT:USDT
   - BTC/USDT:USDT
   - ETH/USDT:USDT
   - XRP/USDT:USDT
   - BNB/USDT:USDT

2. **✅ Maximum Leverage:** 20x (enforced by `SafetyChecker`)

3. **✅ Minimum Trades:** 10 trades required (tracked automatically)

4. **✅ API Trading Only:** All trades via API (no manual)

5. **✅ AI Decision Logging:** Complete JSONL logs in `logs/hackathon/`

### Compliance Features

- **SafetyChecker:** Validates every order before execution
- **Auto-blocking:** Invalid pairs/leverage automatically rejected
- **Decision Logging:** Every trade logs AI context
- **Compliance Report:** Generate submission report via `/api/compliance/report`

### Generating Submission Report

```bash
# Via API
curl http://localhost:8000/api/compliance/report

# Or via chat
"Generate hackathon compliance report"
```

**Report includes:**
- Total trades
- Pairs traded
- Leverage used
- AI decision logs
- Performance metrics
- Compliance status

---

## 🛠️ Development

### Running Tests

```bash
cd backend
pytest tests/ -v

# With coverage
pytest tests/ --cov=backend --cov-report=html
```

### Code Quality

```bash
# Format code
black backend/

# Lint
flake8 backend/

# Type checking
mypy backend/
```

### Adding New Indicators

```python
# backend/strategies/technical_indicators.py

@staticmethod
def your_indicator(prices: np.ndarray, period: int) -> np.ndarray:
    """Your custom indicator"""
    # Implementation
    return result
```

### Creating Custom Strategies

```python
# backend/strategies/custom_strategy.py

from backend.strategies.scalping_strategy import ScalpingStrategy

class MyStrategy(ScalpingStrategy):
    def generate_signal(self, ohlcv, indicators):
        # Your custom logic
        return signal
```

---

## 🚢 Deployment

### Production Deployment

```bash
# 1. Set production environment
cp .env.example .env.production
nano .env.production

# Update:
WEEX_TESTNET=false
DEBUG_MODE=false
LOG_LEVEL=WARNING

# 2. Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# 3. Monitor logs
docker-compose logs -f
```

### Cloud Deployment (AWS)

```bash
# Deploy to AWS ECS/Fargate
# TODO: Add AWS deployment guide
```

### Security Checklist

- [ ] Change all default passwords
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS
- [ ] Set up firewall rules
- [ ] Regular backups of database
- [ ] Monitor logs for suspicious activity
- [ ] Use separate testnet/mainnet environments

---

## 🐛 Troubleshooting

### Common Issues

**1. AWS Bedrock Connection Failed**
```
Error: Unable to connect to AWS Bedrock
Solution: 
- Verify AWS credentials in .env
- Check AWS region (must be us-east-1 for Claude)
- Ensure Bedrock model access is enabled
```

**2. WEEX API Errors**
```
Error: Invalid API key
Solution:
- Generate new API keys from WEEX dashboard
- Ensure API key has trading permissions
- Start with WEEX_TESTNET=true
```

**3. Database Locked**
```
Error: Database is locked
Solution:
- Close other connections to database
- Use PostgreSQL for production
- Restart backend server
```

**4. WebSocket Disconnects**
```
Error: WebSocket closed unexpectedly
Solution:
- Check CORS settings
- Verify frontend/backend URLs
- Check network connectivity
```

### Debug Mode

```bash
# Enable verbose logging
LOG_LEVEL=DEBUG
VERBOSE_LOGGING=true

# Run with debug
python backend/main.py --debug
```

### Getting Help

- **GitHub Issues:** [Report bugs](https://github.com/yourusername/weex-ai-scalping-bot/issues)
- **Discussions:** [Ask questions](https://github.com/yourusername/weex-ai-scalping-bot/discussions)
- **Email:** support@yourdomain.com

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint/Prettier for JavaScript
- Write tests for new features
- Update documentation
- Add type hints

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- **WEEX/WOO X** for the trading hackathon
- **DoraHacks** for hosting the competition
- **Anthropic** for Claude AI
- **AWS** for Bedrock service
- **CCXT** for exchange integration
- **FastAPI** for the awesome framework

---

## 📞 Contact

- **Author:** Your Name
- **Email:** your.email@example.com
- **GitHub:** [@yourusername](https://github.com/yourusername)
- **Twitter:** [@yourhandle](https://twitter.com/yourhandle)

---

## 🔮 Roadmap

- [ ] Add more technical indicators
- [ ] Implement ML-based signal generation
- [ ] Multi-timeframe analysis
- [ ] Portfolio optimization
- [ ] Mobile app (React Native)
- [ ] Telegram bot integration
- [ ] Advanced backtesting features
- [ ] Strategy marketplace

---

## ⚠️ Disclaimer

**This software is for educational and competition purposes only.**

- Not financial advice
- Past performance ≠ future results
- Trading carries risk of loss
- Start with testnet/demo mode
- Never trade more than you can afford to lose

**USE AT YOUR OWN RISK**

---

**Made with ❤️ for WEEX Trading Hackathon**

**Good luck trading! 🚀📈**
