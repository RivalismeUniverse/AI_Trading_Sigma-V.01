# AI Trading SIGMA - Setup Guide

Complete setup instructions for getting AI Trading SIGMA running on your system.

## 📋 Prerequisites

### Required Software
- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)

### Required Accounts
1. **AWS Account** - For Bedrock access
   - Sign up: https://aws.amazon.com/
   - Enable Bedrock: https://console.aws.amazon.com/bedrock/
   - Request Claude 3.5 Sonnet access

2. **WEEX Account** (or Binance)
   - WEEX: https://www.woo.network/
   - Binance: https://www.binance.com/
   - Enable API access
   - Generate testnet keys first!

---

## 🚀 Quick Start (5 Minutes)

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/ai-trading-sigma.git
cd ai-trading-sigma
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your favorite editor
```

### 3. Configure Environment Variables

Edit `backend/.env` and fill in:

```bash
# AWS Bedrock (Required)
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_REGION=us-east-1

# WEEX Exchange (Testnet recommended)
EXCHANGE=weex
WEEX_API_KEY=your_weex_key
WEEX_API_SECRET=your_weex_secret
WEEX_TESTNET=true
```

### 4. Start Backend
```bash
python main.py
```

You should see:
```
INFO: Starting AI Trading SIGMA...
INFO: Database initialized
INFO: AWS Bedrock client initialized
INFO: Trading engine initialized
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 5. Frontend Setup (New Terminal)
```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Start frontend
npm start
```

### 6. Access Application

Open browser: **http://localhost:3000**

🎉 **You're ready to trade!**

---

## 🔐 Getting API Keys

### AWS Bedrock

1. **Create AWS Account**: https://aws.amazon.com/
2. **Enable Bedrock**:
   - Go to AWS Console
   - Search for "Bedrock"
   - Select "Model access"
   - Request access to "Claude 3.5 Sonnet"
3. **Create IAM User**:
   - Go to IAM Console
   - Create user with Bedrock permissions
   - Generate access keys
4. **Copy Credentials** to `.env`

### WEEX Exchange

1. **Sign Up**: https://www.woo.network/
2. **Enable Testnet** (Recommended first!):
   - Go to Account Settings
   - Enable Testnet mode
   - Get testnet credentials
3. **Generate API Keys**:
   - Go to API Management
   - Create new API key
   - Enable "Trading" permission
   - Copy Key and Secret
4. **Add to `.env`**:
```bash
WEEX_API_KEY=your_key
WEEX_API_SECRET=your_secret
WEEX_TESTNET=true
```

### Binance Exchange (Alternative)

1. **Sign Up**: https://testnet.binancefuture.com/
2. **Get Testnet Keys**: Available immediately
3. **Configure**:
```bash
EXCHANGE=binance
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
BINANCE_TESTNET=true
```

---

## 🐳 Docker Setup (Alternative)

### Using Docker Compose
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker Build
```bash
# Backend
cd backend
docker build -t aitrading-backend .
docker run -p 8000:8000 --env-file .env aitrading-backend

# Frontend
cd frontend
docker build -t aitrading-frontend .
docker run -p 3000:3000 aitrading-frontend
```

---

## 🧪 Testing Setup

### Verify Backend
```bash
cd backend
pytest tests/ -v
```

Expected output:
```
test_hybrid_engine.py::test_engine_initialization PASSED
test_strategies.py::test_indicator_calculation PASSED
test_safety.py::test_compliance_checks PASSED
...
======================== 25 passed in 5.23s =========================
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:8000/api/health

# Get balance
curl http://localhost:8000/api/balance

# Get status
curl http://localhost:8000/api/trading/status
```

---

## 📊 First Trade

### 1. Open Dashboard
Navigate to: http://localhost:3000

### 2. Create Strategy via Chat
Click the AI chat button and type:
```
Create an RSI oversold strategy for BTC with 10x leverage
```

### 3. Apply Strategy
Click "Apply Strategy" button in the response

### 4. Start Trading
Click "Start Trading" button in header

### 5. Monitor
Watch the dashboard for:
- Real-time signals
- Trade executions
- P&L updates
- Performance metrics

---

## ⚙️ Configuration Options

### Trading Parameters

Edit `backend/.env`:

```bash
# Symbol to trade
DEFAULT_SYMBOL=BTC/USDT:USDT

# Leverage (max 20x for hackathon)
DEFAULT_LEVERAGE=10

# Risk per trade (2% recommended)
MAX_RISK_PER_TRADE=0.02

# Daily loss limit (5%)
MAX_DAILY_LOSS=0.05

# Max open positions
MAX_OPEN_POSITIONS=3
```

### Strategy Indicators

```bash
# RSI
RSI_PERIOD=14
RSI_OVERSOLD=30
RSI_OVERBOUGHT=70

# MACD
MACD_FAST=12
MACD_SLOW=26
MACD_SIGNAL=9

# Monte Carlo
MC_SIMULATIONS=1000
MC_CONFIDENCE=0.65
```

---

## 🐛 Troubleshooting

### Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate      # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Error**: `AWS credentials not configured`
```bash
# Check .env file
cat .env | grep AWS

# Verify credentials
aws configure list  # If AWS CLI installed
```

### Frontend Won't Start

**Error**: `Cannot find module 'react'`
```bash
# Delete node_modules and reinstall
rm -rf node_modules
npm install
```

**Error**: `EADDRINUSE: address already in use`
```bash
# Kill process on port 3000
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:3000 | xargs kill -9
```

### Exchange Connection Issues

**Error**: `Invalid API key`
```bash
# Verify keys in .env
# Make sure no extra spaces
# Check testnet setting matches your keys
WEEX_TESTNET=true  # For testnet keys
```

**Error**: `Symbol not allowed`
```bash
# Check symbol format
# WEEX uses: BTC/USDT:USDT
# Binance uses: BTC/USDT

# Verify in allowed list (config.py)
```

### Database Issues

**Error**: `Database locked`
```bash
# Stop all instances
pkill -f "python main.py"

# Delete database (WARNING: loses data)
rm trading_data.db
```

---

## 📁 Project Structure

```
ai-trading-sigma/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Configuration
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables
│   │
│   ├── core/                   # Trading engine
│   │   ├── hybrid_engine.py    # Main trading loop
│   │   ├── signal_generator.py # Signal generation
│   │   └── risk_manager.py     # Risk management
│   │
│   ├── exchange/               # Exchange clients
│   │   ├── weex_client.py      # WEEX implementation
│   │   ├── binance_client.py   # Binance implementation
│   │   └── safety_checker.py   # Compliance
│   │
│   ├── strategies/             # Strategies
│   │   └── technical_indicators.py
│   │
│   ├── ai/                     # AI integration
│   │   └── bedrock_client.py
│   │
│   ├── database/               # Database
│   │   ├── models.py
│   │   └── db_manager.py
│   │
│   └── utils/                  # Utilities
│
├── frontend/                   # React frontend
├── logs/                       # Log files
└── data/                       # Data storage
```

---

## 🔍 Verification Checklist

Before starting trading, verify:

- [ ] Backend running on http://localhost:8000
- [ ] Frontend accessible on http://localhost:3000
- [ ] API health check passes: `curl http://localhost:8000/api/health`
- [ ] AWS Bedrock connection works
- [ ] Exchange connection successful
- [ ] Balance fetched correctly
- [ ] Chat with AI works
- [ ] Strategy can be created
- [ ] Testnet mode enabled (for safety!)

---

## 📞 Support

If you encounter issues:

1. **Check logs**: `tail -f logs/trading_bot.log`
2. **Check compliance logs**: `logs/hackathon/`
3. **Read error messages carefully**
4. **Check this guide's troubleshooting section**
5. **Verify all environment variables**

---

## 🎓 Next Steps

1. **Read Strategy Guide**: Understand how strategies work
2. **Try Different Strategies**: RSI, MACD, Monte Carlo
3. **Monitor Performance**: Track metrics
4. **Adjust Parameters**: Fine-tune for your style
5. **Read Compliance Guide**: Understand hackathon rules

---

## ⚠️ Important Notes

- **Always start with testnet!**
- Never commit `.env` to git
- Keep API keys secure
- Monitor the bot regularly
- Start with small positions
- Test thoroughly before live trading
- Review compliance logs regularly

---

## 🎉 You're All Set!

Your AI Trading SIGMA is now ready to trade. Happy trading! 🚀

For more information:
- **API Documentation**: http://localhost:8000/docs
- **Architecture Guide**: See ARCHITECTURE.md
- **Trading Strategy**: See TRADING_STRATEGY.md

---

*Last Updated: December 2024*
*Version: 1.0.0*
