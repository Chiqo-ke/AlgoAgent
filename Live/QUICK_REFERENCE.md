# Live Trader Quick Reference Card

**Emergency Contact**: [Your contact info]  
**System**: AlgoAgent Live Trader v1.0  
**Last Updated**: October 18, 2025

---

## 🚨 EMERGENCY PROCEDURES

### STOP TRADING IMMEDIATELY
```powershell
# Method 1: Kill-switch file (Recommended)
New-Item -Path EMERGENCY_STOP -ItemType File

# Method 2: Stop process
Ctrl+C  # In trader terminal

# Method 3: Manually close positions in MT5
# Right-click position → Close Position
```

---

## 📋 DAILY CHECKLIST

### Morning (Pre-Market)
- [ ] Check overnight positions: http://127.0.0.1:5000
- [ ] Review logs for errors: `logs\live_trader.log`
- [ ] Verify account balance in MT5 terminal
- [ ] Check kill-switch is NOT active: `dir EMERGENCY_STOP` (should not exist)
- [ ] Confirm trading is enabled in dashboard

### During Trading Hours
- [ ] Monitor dashboard every 2 hours
- [ ] Check for alerts (Telegram/webhook)
- [ ] Verify P/L is within expected range
- [ ] Look for unusual order volumes

### End of Day
- [ ] Review daily P/L
- [ ] Check number of trades vs limit
- [ ] Verify all positions are as expected
- [ ] Check for any failed orders
- [ ] Archive logs if needed

---

## 🖥️ COMMON COMMANDS

### Start Trader
```powershell
# Dry-run (safe testing)
python live_trader.py --strategy ..\Backtest\codes\my_strategy.py --dry-run

# Live trading
python live_trader.py --strategy ..\Backtest\codes\my_strategy.py

# Using startup script
start_trader.bat ..\Backtest\codes\my_strategy.py --dry-run
```

### Monitor
```powershell
# View logs (live tail)
Get-Content logs\live_trader.log -Wait -Tail 20

# Start dashboard
python dashboard.py
# Open: http://127.0.0.1:5000

# Check running processes
Get-Process python | Where-Object {$_.MainWindowTitle -like "*live_trader*"}
```

### Stop Trader
```powershell
# Graceful stop (in trader terminal)
Ctrl+C

# Force stop (find PID first)
Stop-Process -Id [PID]

# Emergency kill-switch
New-Item -Path EMERGENCY_STOP -ItemType File
```

---

## 📊 QUICK METRICS

### Check Today's Performance
```sql
-- Run in SQLite browser (data\audit.db)
SELECT 
  COUNT(*) as trades,
  SUM(profit) as total_pnl,
  AVG(profit) as avg_pnl
FROM trades
WHERE DATE(timestamp) = DATE('now');
```

### View Recent Orders
```powershell
python -c "from audit_logger import AuditLogger; from pathlib import Path; a = AuditLogger(Path('data/audit.db')); orders = a.get_recent_orders(10); print('\n'.join([f\"{o['timestamp']}: {o['symbol']} {o['side']} {o['status']}\" for o in orders]))"
```

### Current Positions
```powershell
# In MT5 terminal: Tools → Trade
# Or via dashboard: http://127.0.0.1:5000
```

---

## ⚙️ CONFIGURATION QUICK REFERENCE

### Key Settings (.env)
| Setting | Safe Value | Aggressive Value |
|---------|------------|------------------|
| `DRY_RUN` | `true` | `false` |
| `DEFAULT_RISK_PCT` | `0.5` | `2.0` |
| `MAX_POSITION_SIZE` | `0.01` | `1.0` |
| `MAX_DAILY_TRADES` | `3` | `20` |
| `MAX_DAILY_LOSS_PCT` | `2.0` | `10.0` |

### Edit Configuration
```powershell
notepad .env
# Restart trader after changes
```

---

## 🔍 TROUBLESHOOTING

### Issue: Trader won't start
**Check:**
1. Is MT5 terminal running?
2. Are credentials correct in `.env`?
3. Run connection test: `python -c "from mt5_connector import MT5Connector; from config import LiveConfig; c = LiveConfig(); m = MT5Connector(c); m.initialize()"`

### Issue: No trades executing
**Check:**
1. Is `DRY_RUN=true`? (Set to `false` for real trading)
2. Are daily limits reached? (Check dashboard)
3. Is kill-switch active? (`dir EMERGENCY_STOP`)
4. Check logs for errors

### Issue: Orders rejected
**Check:**
1. Sufficient margin? (MT5 terminal → Tools → Account)
2. Symbol in Market Watch? (Right-click → Symbols)
3. Lot size valid? (Check symbol specifications)
4. View error in logs: `Get-Content logs\live_trader.log -Tail 50`

### Issue: High slippage
**Actions:**
1. Increase `deviation` in order request (edit `live_trader.py`)
2. Switch to LIMIT orders (edit strategy)
3. Avoid trading during news events
4. Consider different broker

---

## 📈 PERFORMANCE TARGETS

| Metric | Target | Warning Level | Action Required |
|--------|--------|---------------|-----------------|
| Win Rate | >50% | <40% | Review strategy |
| Daily Trades | 3-10 | >20 or <1 | Check parameters |
| Avg Slippage | <5 pips | >10 pips | Review execution |
| Drawdown | <10% | >20% | Reduce risk |
| Connection Uptime | >99% | <95% | Check network |

---

## 🔔 ALERTS SETUP

### Telegram Bot
1. Create bot: https://t.me/BotFather
2. Get token and chat ID
3. Add to `.env`:
   ```env
   ENABLE_ALERTS=true
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```
4. Restart trader

### Webhook
1. Set up webhook endpoint (e.g., Discord, Slack)
2. Add to `.env`:
   ```env
   ALERT_WEBHOOK_URL=https://your-webhook-url
   ```
3. Restart trader

---

## 📞 CONTACTS

| Role | Name | Contact |
|------|------|---------|
| System Admin | [Your Name] | [Email/Phone] |
| Broker Support | [Broker] | [Support Number] |
| Emergency | [Backup Contact] | [Emergency Number] |

---

## 🗂️ FILES & LOCATIONS

| What | Where |
|------|-------|
| Configuration | `.env` |
| Logs | `logs\live_trader.log` |
| Audit DB | `data\audit.db` |
| Dashboard | http://127.0.0.1:5000 |
| Kill-switch | `EMERGENCY_STOP` (file) |
| Strategy | `..\Backtest\codes\*.py` |
| MT5 Terminal | `C:\Program Files\MetaTrader 5\` |

---

## 🛠️ MAINTENANCE

### Weekly
- [ ] Review logs for patterns
- [ ] Check disk space (`logs\` and `data\`)
- [ ] Verify backups (if configured)
- [ ] Update strategy if needed

### Monthly
- [ ] Archive old logs (>30 days)
- [ ] Review performance vs backtest
- [ ] Optimize parameters
- [ ] Update documentation

---

## 🔐 SECURITY REMINDERS

- ✅ Never commit `.env` to git
- ✅ Use strong passwords
- ✅ Enable 2FA on MT5 account
- ✅ Keep API keys secret
- ✅ Regularly review audit logs
- ✅ Set file permissions: `icacls .env /inheritance:r /grant:r "$env:USERNAME:F"`

---

## 📚 DOCUMENTATION

- **Full Setup**: `SETUP_AND_TESTING.md`
- **Architecture**: `README.md`
- **Implementation**: `IMPLEMENTATION_SUMMARY.md`
- **Backtest Integration**: `..\Backtest\SYSTEM_PROMPT.md`

---

## 🎯 RULES OF THUMB

1. **Always start with dry-run mode**
2. **Test on demo before live**
3. **Start small, scale gradually**
4. **Monitor closely in first week**
5. **Never risk more than you can afford to lose**
6. **Keep kill-switch accessible**
7. **Review daily P/L vs expectations**
8. **Don't trade during major news events**
9. **Have a plan for losses**
10. **Document all changes**

---

**Version**: 1.0  
**System Ready**: ✅  
**Last Test**: [Date]  
**Next Review**: [Date]

---

_Print this card and keep it near your trading station_ 📋
