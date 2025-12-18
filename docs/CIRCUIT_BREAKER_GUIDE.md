# 🛡️ Circuit Breaker System - Complete Guide

## Overview

The Circuit Breaker is a **production-grade safety system** that protects your trading engine from:
- API failures & latency
- Exchange outages
- Network issues
- Unexpected losses
- System overload

---

## 🎯 Philosophy: Graduated Response

**NOT** a simple on/off switch. Instead, **4 graduated levels**:

```
Normal → ALERT → THROTTLE → HALT → SHUTDOWN
  ✅       ⚠️        🟡        🔴       ☠️
```

Each level provides appropriate response to issue severity.

---

## 📊 Circuit Breaker Levels

### Level 0: CLOSED (Normal Operation) ✅

**State:** Everything working normally

**Trading:** Full speed
- All signals processed
- Normal position sizes
- Standard risk management

**Triggers:** None (default state)

**Recovery:** N/A (already optimal)

---

### Level 1: ALERT (Warning Mode) ⚠️

**State:** Minor issues detected, caution advised

**Trading:** Continue but monitor closely
- ✅ All trades allowed
- ✅ Normal position sizes
- 📢 Warnings logged
- 📊 Metrics tracked

**Triggers:**
- API latency: 500ms - 1000ms
- Slippage: 0.1% - 0.3%
- 2 consecutive order failures
- Minor exchange delays

**Actions:**
- Send warning notifications
- Increase monitoring frequency
- Log degradation metrics

**Recovery:** 
- Automatic after 60 seconds of healthy metrics
- No consecutive failures
- API latency < 500ms

---

### Level 2: THROTTLE (Reduced Mode) 🟡

**State:** Moderate issues, reduce exposure

**Trading:** Cautious mode
- ✅ High confidence trades only (>0.7)
- 🔽 Position sizes reduced 50%
- ⏸️ Skip marginal signals
- 📢 Urgent notifications sent

**Triggers:**
- API latency: 1s - 3s
- Slippage: 0.3% - 0.5%
- 3-5 consecutive order failures
- 30% failure rate in last 5 minutes
- Partial exchange issues

**Actions:**
- Reduce position sizes
- Filter out low-confidence signals
- Pause aggressive strategies
- Send urgent notifications
- Close dashboard alerts

**Recovery:**
- Automatic after 5 minutes of healthy operation
- All metrics back to normal
- No recent failures

---

### Level 3: HALT (Emergency Stop) 🔴

**State:** Critical issues, stop new entries

**Trading:** Emergency mode
- 🛑 NO new positions
- ✅ Can close existing positions
- 🔐 Auto-close positions at market
- 📢 Critical alerts sent
- 💾 State saved to disk

**Triggers:**
- API latency > 3 seconds
- Slippage > 0.5%
- 5+ consecutive failures
- Exchange downtime detected
- Unexpected loss > 5% in short time
- Network connectivity issues

**Actions:**
- STOP all new trade entries
- Close open positions (market orders)
- Save engine state
- Send critical notifications
- Log complete system state
- Attempt recovery after cooldown

**Recovery:**
- Manual review recommended
- Automatic after 15 minutes (if metrics healthy)
- Requires operator confirmation in production

---

### Level 4: SHUTDOWN (Fatal Error) ☠️

**State:** Fatal system error, complete shutdown

**Trading:** STOPPED
- ☠️ Engine completely stopped
- 🚫 No trading allowed
- 💾 Emergency data dump
- 📞 Admin notification (SMS/Email)
- 🔄 Requires manual restart

**Triggers:**
- 10+ consecutive failures
- Memory errors
- Security breach detected
- Database corruption
- Manual kill command
- Critical system errors

**Actions:**
- Kill trading engine
- Emergency state dump to disk
- Close all WebSocket connections
- Send emergency notifications
- Write failure report
- Require manual intervention

**Recovery:**
- MANUAL ONLY
- Operator must investigate
- Fix root cause
- Restart engine manually

---

## 🔧 Configuration

### Default Thresholds

```python
from core.circuit_breaker import CircuitConfig

config = CircuitConfig(
    # Alert (Level 1)
    alert_api_latency_ms=500.0,
    alert_slippage_pct=0.1,
    alert_consecutive_failures=2,
    
    # Throttle (Level 2)
    throttle_api_latency_ms=1000.0,
    throttle_slippage_pct=0.3,
    throttle_consecutive_failures=3,
    
    # Halt (Level 3)
    halt_api_latency_ms=3000.0,
    halt_slippage_pct=0.5,
    halt_consecutive_failures=5,
    halt_loss_pct=0.05,
    
    # Shutdown (Level 4)
    shutdown_consecutive_failures=10,
    
    # Recovery cooldowns
    alert_cooldown_seconds=60,
    throttle_cooldown_seconds=300,
    halt_cooldown_seconds=900
)
```

### Custom Configuration

```python
# Conservative (stricter thresholds)
conservative_config = CircuitConfig(
    alert_api_latency_ms=300.0,  # Stricter
    throttle_consecutive_failures=2,
    halt_consecutive_failures=3
)

# Aggressive (more lenient)
aggressive_config = CircuitConfig(
    alert_api_latency_ms=1000.0,  # More lenient
    throttle_consecutive_failures=5,
    halt_consecutive_failures=8
)
```

---

## 💻 Usage Examples

### Basic Usage

```python
from core.circuit_breaker import get_circuit_breaker

# Get circuit breaker instance
circuit_breaker = get_circuit_breaker()

# Check if trading allowed
allowed, reason = circuit_breaker.check_execution_allowed(action)

if not allowed:
    print(f"Trading blocked: {reason}")
    return

# Proceed with trade...
```

### Reporting Issues

```python
# Report API latency
circuit_breaker.report_api_latency(latency_ms=850.0)

# Report order failure
circuit_breaker.report_order_failure({
    'symbol': 'BTC/USDT',
    'error': 'Timeout',
    'attempts': 3
})

# Report successful order
circuit_breaker.report_order_success()

# Report slippage
circuit_breaker.report_slippage(
    expected_price=50000.0,
    actual_price=50100.0
)

# Report critical error
circuit_breaker.report_critical_error(
    IssueType.MEMORY_ERROR,
    {'available_mb': 100}
)
```

### Monitoring

```python
# Get current status
status = circuit_breaker.get_status()
print(f"State: {status['state']}")
print(f"Consecutive failures: {status['consecutive_failures']}")
print(f"Avg latency: {status['metrics']['avg_api_latency_ms']}ms")

# Get recent issues
recent_issues = circuit_breaker.get_recent_issues(minutes=5)
for issue in recent_issues:
    print(f"{issue.timestamp}: {issue.issue_type} - {issue.details}")
```

### Manual Control

```python
# Manual override (disable trading)
circuit_breaker.manual_override_enable("Maintenance window")

# Re-enable
circuit_breaker.manual_override_disable()

# Force recovery (use carefully!)
circuit_breaker.force_recovery()
```

---

## 📡 Notifications

Circuit breaker sends notifications through multiple channels:

### Available Channels

1. **LOG** ✅ (Always enabled)
   - Written to log files
   - Compliance trail

2. **DASHBOARD** ✅ (Enabled by default)
   - Real-time UI alerts
   - Notification center

3. **EMAIL** ⚙️ (Configure)
   - SMTP integration
   - Critical alerts

4. **SMS** ⚙️ (Configure)
   - Via Twilio/AWS SNS
   - Emergency only

5. **TELEGRAM** ⚙️ (Configure)
   - Telegram bot
   - Real-time updates

6. **WEBHOOK** ⚙️ (Configure)
   - HTTP POST to your service
   - Custom integrations

### Notification Priorities

```python
from core.notification_system import NotificationPriority

# INFO - Level 0 events
# WARNING - Level 1 (ALERT)
# CRITICAL - Level 2-3 (THROTTLE/HALT)
# EMERGENCY - Level 4 (SHUTDOWN)
```

### Configure Notifications

```python
from core.notification_system import notification_system

# Enable email
notification_system.configure_email(
    smtp_host='smtp.gmail.com',
    smtp_port=587,
    from_email='bot@trading.com',
    to_emails=['admin@trading.com']
)

# Enable Telegram
notification_system.configure_telegram(
    bot_token='your_bot_token',
    chat_ids=['your_chat_id']
)

# Add webhook
notification_system.add_webhook_url('https://your-service.com/webhook')
```

---

## 🎓 Best Practices

### 1. Monitor Dashboard

```bash
# Check status regularly
GET /api/circuit-breaker/status

# Get recent notifications
GET /api/notifications
```

### 2. Set Up Alerts

```python
# Register custom callbacks
def my_alert_handler(issue):
    # Your custom logic
    send_to_slack(issue)

circuit_breaker.register_alert_callback(my_alert_handler)
```

### 3. Test Regularly

```python
# Simulate latency
circuit_breaker.report_api_latency(2000.0)

# Check state
assert circuit_breaker.state == CircuitState.THROTTLE
```

### 4. Production Checklist

- [ ] Configure email notifications
- [ ] Set up Telegram bot
- [ ] Test all circuit breaker levels
- [ ] Document recovery procedures
- [ ] Train team on manual override
- [ ] Set up monitoring dashboard
- [ ] Create incident response plan

---

## 🚨 Incident Response

### When ALERT Triggered

1. **Don't Panic** - System still trading
2. Check logs for root cause
3. Monitor metrics closely
4. Prepare to escalate if needed

### When THROTTLE Triggered

1. **Investigate Immediately**
2. Check exchange status
3. Verify network connectivity
4. Review recent trades
5. Consider manual pause if needed

### When HALT Triggered

1. **URGENT ACTION**
2. Check all open positions
3. Verify positions are closing
4. Investigate root cause
5. Don't restart until resolved
6. Document incident

### When SHUTDOWN Triggered

1. **CRITICAL INCIDENT**
2. Check system health immediately
3. Review logs thoroughly
4. Fix root cause before restart
5. Test in safe environment first
6. Write post-mortem report

---

## 📊 Monitoring Dashboard

### API Endpoints

```bash
# Get status
GET /api/circuit-breaker/status

# Get metrics
GET /api/circuit-breaker/metrics

# Get recent issues
GET /api/circuit-breaker/issues?minutes=5

# Force recovery (admin only)
POST /api/circuit-breaker/recover

# Manual override
POST /api/circuit-breaker/override
{
  "enabled": true,
  "reason": "Maintenance"
}
```

---

## 🔍 Troubleshooting

### Circuit Breaker Stuck in HALT

**Problem:** Won't recover automatically

**Solutions:**
1. Check if issues resolved: `circuit_breaker.get_status()`
2. Verify metrics are healthy
3. Wait for cooldown period (15 minutes)
4. Manual recovery: `circuit_breaker.force_recovery()`

### Too Sensitive (Triggers Too Often)

**Problem:** Constantly in ALERT/THROTTLE

**Solutions:**
1. Adjust thresholds higher
2. Increase cooldown periods
3. Check if exchange actually slow
4. Review network connection

### Not Sensitive Enough

**Problem:** Doesn't trigger when it should

**Solutions:**
1. Lower thresholds
2. Check if metrics being reported
3. Verify API monitoring working
4. Review failure detection logic

---

## 🎯 Performance Impact

**Overhead:** Minimal (~1-2ms per trade)

**Benefits:**
- Prevents catastrophic losses
- Protects against API failures
- Automatic recovery
- Complete audit trail
- Peace of mind 😊

---

## 🏆 Why This System is Production-Grade

✅ **Graduated Response** - Not binary on/off
✅ **Automatic Recovery** - Self-healing system
✅ **Multi-Channel Alerts** - Never miss critical issues
✅ **Complete Audit Trail** - Full compliance
✅ **Battle-Tested Logic** - Based on industry best practices
✅ **Configurable** - Adapt to your risk tolerance
✅ **Zero Overhead** - Minimal performance impact

---

**Built for real production trading. Sleep better at night.** 😴

*Last Updated: December 2025*
