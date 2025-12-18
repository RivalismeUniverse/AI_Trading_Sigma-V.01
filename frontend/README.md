# AI Trading SIGMA - Frontend

React-based dashboard for AI Trading SIGMA autonomous trading bot.

## Features

- ✅ Real-time dashboard with WebSocket updates
- ✅ Live price charts (Recharts)
- ✅ Open positions tracking
- ✅ Recent trades history
- ✅ Circuit breaker status monitoring
- ✅ AI chat interface
- ✅ Performance metrics & analytics
- ✅ Notification center
- ✅ Dark theme optimized for trading
- ✅ Mobile responsive

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## Environment Variables

Create `.env.local`:

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## Project Structure

```
frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── Header.jsx
│   │   ├── MetricsRow.jsx
│   │   ├── ChartWidget.jsx
│   │   ├── OpenPositionsWidget.jsx
│   │   ├── RecentTradesWidget.jsx
│   │   ├── SignalsWidget.jsx
│   │   ├── CircuitBreakerWidget.jsx
│   │   ├── PerformanceWidget.jsx
│   │   ├── NotificationPanel.jsx
│   │   ├── AIChat.jsx
│   │   └── FloatingAIButton.jsx
│   ├── services/
│   │   ├── api.js
│   │   └── websocket.js
│   ├── App.jsx
│   ├── App.css
│   ├── index.js
│   └── index.css
├── package.json
├── tailwind.config.js
└── postcss.config.js
```

## Components

### Header
- Balance display
- Daily P/L
- Start/Stop trading button
- Refresh button

### MetricsRow
- 6 key metrics cards
- Real-time updates
- Color-coded values

### ChartWidget
- Live price chart
- Multiple timeframes (5M, 15M, 1H, 4H, 1D)
- Recharts integration

### OpenPositionsWidget
- Current open positions
- Entry price, size, SL, TP
- Real-time P/L

### RecentTradesWidget
- Trade history table
- Entry/exit prices
- P/L per trade
- Time ago display

### SignalsWidget
- Current trading signal
- Action (LONG/SHORT/WAIT)
- Confidence level
- Stop loss & take profit
- Reasoning

### CircuitBreakerWidget
- Circuit breaker state
- Performance metrics
- Status messages

### PerformanceWidget
- 7-day P/L chart
- Performance history

### NotificationPanel
- Real-time alerts
- Priority-based coloring
- Mark as read
- Clear all

### AIChat
- Natural language interface
- Strategy generation
- Market analysis
- Real-time responses

## API Integration

All API calls in `src/services/api.js`:

- `getTradingStatus()` - Get bot status
- `startTrading()` - Start autonomous trading
- `stopTrading()` - Stop trading
- `sendChatMessage()` - Chat with AI
- `createStrategy()` - Generate strategy
- `getPerformance()` - Get metrics
- `getTrades()` - Get trade history
- `getCircuitBreakerStatus()` - CB status
- And more...

## WebSocket Events

Real-time updates via `src/services/websocket.js`:

- `status_update` - Bot status changes
- `new_trade` - New trade opened
- `trade_closed` - Trade closed
- `performance_update` - Metrics update
- `signal_generated` - New signal
- `circuit_breaker_alert` - CB alert

## Styling

- **Tailwind CSS** for utility-first styling
- **Dark theme** optimized for trading
- **Responsive design** for all devices
- **Custom animations** for status indicators

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development

```bash
# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

## Production Deployment

1. Build the app:
```bash
npm run build
```

2. Serve the `build` folder with a static server (nginx, apache, etc.)

3. Update environment variables for production API URL

## Troubleshooting

**WebSocket not connecting:**
- Check `REACT_APP_WS_URL` in `.env`
- Verify backend is running
- Check CORS settings

**API errors:**
- Verify `REACT_APP_API_URL` in `.env`
- Check backend is running on correct port
- Check network console for errors

**Charts not rendering:**
- Check browser console for errors
- Verify Recharts is installed
- Check data format

## License

See main repository LICENSE file.

## Support

For issues or questions, refer to main project documentation.

---

Made with ❤️ for AI Trading SIGMA
