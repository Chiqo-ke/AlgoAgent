# AlgoAgent Monolithic Agent - Documentation Index

**Created:** December 3, 2025  
**Last Updated:** March 11, 2026  
**Purpose:** Central hub for navigating monolithic agent documentation  
**System Status:** ✅ Live Trading System Operational

**Latest Updates:**
- ✅ [LIVE_TRADING_SESSIONS_API.md](LIVE_TRADING_SESSIONS_API.md) - Complete live trading API (March 11, 2026)
- ✅ [CHANGELOG.md](CHANGELOG.md) - Added March 2026 live trading E2E testing results (March 11, 2026)
- ✅ [CHANGELOG.md](CHANGELOG.md) - Consolidated all fix summaries (Jan 26, 2026)
- ✅ Archive created - Historical docs moved to [archive/](archive/) (Jan 26, 2026)

---

## 📋 Documentation Overview

This index provides a roadmap through all monolithic agent documentation. Start here to find what you need.

---

## 🚀 START HERE

### For First-Time Users
1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** (5 min read)
   - File structure overview
   - Common commands & API endpoints
   - Quick code snippets
   - When: You need a quick lookup

2. **[SETUP_AND_INTEGRATION.md](SETUP_AND_INTEGRATION.md)** (15 min read)
   - Installation instructions
   - Environment setup
   - Database initialization
   - When: Setting up the system for the first time

3. **[ARCHITECTURE.md](ARCHITECTURE.md)** (20 min read)
   - System design overview
   - Component responsibilities
   - Data flow diagrams
   - When: Understanding how everything fits together

4. **[STATUS.md](STATUS.md)** (10 min read)
   - Component status matrix
   - What's working & what's not
   - Known issues & troubleshooting
   - When: Checking system health or debugging

---

## 📚 Detailed Documentation

### Core System Design

| Document | Purpose | Audience | Read Time |
|----------|---------|----------|-----------|
| **[CHANGELOG.md](CHANGELOG.md)** | All fixes and improvements since Dec 2025 | All developers | 15 min |
| **ARCHITECTURE.md** | Complete system design with all modules | Architects, Senior Devs | 20 min |
| **STATUS.md** | Component health check & known issues | DevOps, QA, Developers | 10 min |
| **QUICK_REFERENCE.md** | Quick lookup tables & commands | All developers | 5 min |

### Setup & Operations

| Document | Purpose | Audience | Read Time |
|----------|---------|----------|-----------|
| **SETUP_AND_INTEGRATION.md** | Installation, config, deployment | New team members, DevOps | 30 min |
| **start_server.ps1** | PowerShell server startup script | Windows developers | 1 min |
| **requirements.txt** | Python dependencies | DevOps, Automation | 2 min |

### Feature-Specific Guides

| Document | Purpose | Location | Status |
|----------|---------|----------|--------|
| **LIVE_TRADING_SESSIONS_API.md** | Live trading on MT5: credentials, sessions, subprocess spawning | Root | ✅ **NEW (March 2026)** |
| PRODUCTION_API_GUIDE.md | REST API reference | Root | ✅ Exists |
| STRATEGY_QUICKSTART.md | Strategy creation guide | Strategy/ | ✅ Exists |
| BACKTESTING_PY_MIGRATION_COMPLETE.md | Migration notes | Root | ✅ Exists |
| AI_STRATEGY_API_GUIDE.md | AI integration details | Root | ✅ Exists |
| SYSTEM_PROMPT_BACKTESTING_PY.md | AI system prompt | Backtest/ | ✅ Exists |

### Previous Implementation Docs

**Note:** Completed implementations have been archived. See [archive/README.md](archive/README.md) for details.

| Document | Purpose | Status | Location |
|----------|---------|--------|----------|
| COPILOT_MIGRATION_COMPLETE.md | Copilot integration | ✅ Archived | [archive/](archive/) |
| COPILOT_INTEGRATION_README.md | Copilot auth setup | ✅ Archived | [archive/](archive/) |
| COPILOT_VALIDATION_INTEGRATION.md | Validation integration | ✅ Archived | [archive/](archive/) |
| IMPLEMENTATION_SUMMARY.md | Overall implementation | ✅ Archived | [archive/](archive/) |
| All Fix Summaries (5 files) | Fix documentation | ✅ Consolidated | [CHANGELOG.md](CHANGELOG.md) |

**For current information:**
- Implementation details: See [implementation/](implementation/) folder
- All fixes: See [CHANGELOG.md](CHANGELOG.md)
- Historical reference: See [archive/](archive/) folder

---

## 🎯 Documentation by Task

### "I want to..."

#### ...understand the system architecture
→ Read: [ARCHITECTURE.md](ARCHITECTURE.md) Section A-D

#### ...set up the system for the first time
→ Read: [SETUP_AND_INTEGRATION.md](SETUP_AND_INTEGRATION.md) → Quick Start

#### ...check if something is working
→ Read: [STATUS.md](testing/STATUS.md) → Component Status Matrix
→ Recent Changes: [CHANGELOG.md](CHANGELOG.md) → January 2026

#### ...understand recent fixes and improvements
→ Read: [CHANGELOG.md](CHANGELOG.md) → All improvements since December 2025
→ Categories: Execution fixes, auto-fix improvements, error prevention

#### ...prevent errors in generated strategies
→ Read: [guides/ERROR_PREVENTION_QUICKSTART.md](guides/ERROR_PREVENTION_QUICKSTART.md) → 3-step setup
→ Then: [guides/AGENT_ERROR_PREVENTION_GUIDE.md](guides/AGENT_ERROR_PREVENTION_GUIDE.md) → Complete guide
→ Reference: `Backtest/SIMBROKER_API_REFERENCE.md` → API documentation

#### ...use the REST API
→ Read: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) → API Quick Reference
→ Then: [PRODUCTION_API_GUIDE.md](PRODUCTION_API_GUIDE.md) (external)

#### ...create a new trading strategy
→ Read: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) → Common Patterns
→ Then: [STRATEGY_QUICKSTART.md](STRATEGY_QUICKSTART.md) (external)

#### ...start a live trading session on MT5
→ Read: [LIVE_TRADING_SESSIONS_API.md](LIVE_TRADING_SESSIONS_API.md) → Overview & Architecture
→ Then: [LIVE_TRADING_SESSIONS_API.md](LIVE_TRADING_SESSIONS_API.md) → Endpoints (Credentials & Sessions)
→ Examples: [LIVE_TRADING_SESSIONS_API.md](LIVE_TRADING_SESSIONS_API.md) → Usage Examples
→ Status: ✅ E2E tested (all 5 steps passing, March 11, 2026)

#### ...run the interactive strategy tester
→ Read: [SETUP_AND_INTEGRATION.md](SETUP_AND_INTEGRATION.md) → Interactive Strategy Tester

#### ...troubleshoot a problem
→ Read: [STATUS.md](STATUS.md) → Troubleshooting
→ Then: [SETUP_AND_INTEGRATION.md](SETUP_AND_INTEGRATION.md) → Troubleshooting

#### ...deploy to production
→ Read: [SETUP_AND_INTEGRATION.md](SETUP_AND_INTEGRATION.md) → Production Deployment
→ Then: [STATUS.md](STATUS.md) → Deployment Status

#### ...understand the code generation
→ Read: [ARCHITECTURE.md](ARCHITECTURE.md) Section G
→ Then: [BACKTESTING_PY_MIGRATION_COMPLETE.md](BACKTESTING_PY_MIGRATION_COMPLETE.md) (external)

#### ...run tests
→ Read: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) → Quick Commands → Testing

---

## 🏗️ System Architecture at a Glance

```
┌─────────────────────────────────────────────┐
│  REST API Layer (Django)                    │
│  /api/auth/ | /api/strategies/ | /api/backtests/
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Business Logic Layer                       │
├─────────────────────────────────────────────┤
│  • Strategy Validator                       │
│  • Gemini AI Code Generator                 │
│  • Conversation Memory Manager              │
│  • Backtest Orchestrator                    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Execution Layer                            │
├─────────────────────────────────────────────┤
│  • backtesting.py (Strategy Execution)      │
│  • yfinance (Data Fetching)                 │
│  • TA-Lib (Indicators)                      │
│  • SQLite (Persistence)                     │
└─────────────────────────────────────────────┘
```

**Full Details:** See [ARCHITECTURE.md](ARCHITECTURE.md) Section A-B

---

## ✅ Component Status Summary

| Component | Status | Tests | Details |
|-----------|--------|-------|---------|
| Authentication | ✅ Working | 4 | JWT login, register, refresh |
| Strategy CRUD | ✅ Working | 5+ | Create, read, update strategies |
| Code Generation | ✅ Working | 4+ | Gemini → Python (backtesting.py) |
| Backtesting | ✅ Working | 5+ | Full backtest execution & metrics |
| Data Pipeline | ✅ Working | 3+ | yfinance + indicators |
| REST API | ✅ Working | 6+ | All endpoints tested |
| Conversation Memory | ✅ Working | 2+ | Session tracking |
| Live Trading | 🔶 Partial | 0 | Placeholder only |
| Real-time Streaming | 🔶 Partial | 0 | Backtesting only |

**Full Details:** See [STATUS.md](STATUS.md) → Component Status Matrix

---

## 📖 Document Mapping

### By Role

**System Architect:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - Full system design
- [STATUS.md](STATUS.md) - Current state & limitations
- [SETUP_AND_INTEGRATION.md](SETUP_AND_INTEGRATION.md) - Deployment guide

**Backend Developer:**
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - API reference
- [ARCHITECTURE.md](ARCHITECTURE.md) Section C-H - Components & endpoints
- PRODUCTION_API_GUIDE.md - API details

**Frontend Developer:**
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - API endpoints
- PRODUCTION_API_GUIDE.md - Response formats
- [SETUP_AND_INTEGRATION.md](SETUP_AND_INTEGRATION.md) → API Integration

**DevOps Engineer:**
- [SETUP_AND_INTEGRATION.md](SETUP_AND_INTEGRATION.md) - Full setup & deployment
- [STATUS.md](STATUS.md) - Health checks & monitoring
- Production Deployment section

**QA / Tester:**
- [STATUS.md](STATUS.md) - Known issues & limitations
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) → Quick Commands
- test files in `tests/` directory

**Data Scientist / Strategist:**
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) → Common Patterns
- [ARCHITECTURE.md](ARCHITECTURE.md) Section G - Strategy creation flow
- STRATEGY_QUICKSTART.md - Strategy guide

---

## 🔑 Key Concepts

### Canonical JSON Schema
A standardized JSON format for defining trading strategies:
```json
{
  "strategy_name": "RSI Oversold",
  "indicators": [{"name": "RSI", "timeperiod": 14}],
  "entry_rules": [{"condition": "RSI < 30", "action": "BUY"}],
  "exit_rules": [{"condition": "RSI > 70", "action": "SELL"}],
  "risk_management": {"stop_loss_pct": 2.0}
}
```
**See:** [ARCHITECTURE.md](ARCHITECTURE.md) Section C.3 for details

### Code Generation Pipeline
```
User Input → Validation → Canonical JSON → Gemini AI → Python Code
```
**See:** [ARCHITECTURE.md](ARCHITECTURE.md) Section G for flow

### Backtest Execution
```
Strategy Class + Data → backtesting.py → Metrics + Trades CSV
```
**See:** [ARCHITECTURE.md](ARCHITECTURE.md) Section C.3

---

## 🧪 Testing

**All Tests Passing:** ✅ 26+ tests

**Run Tests:**
```bash
pytest tests/ -v
```

**Test Files:**
- test_auth_flow.py - Authentication
- test_ai_strategy_api.py - Code generation
- test_production_endpoints.py - API endpoints
- test_dynamic_data_loader.py - Data pipeline
- test_strategy_conversation_memory.py - Memory system

**See:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md) → Quick Commands → Testing

---

## 🛠️ Quick Commands

**Start Server:**
```bash
python manage.py runserver
```

**Run Tests:**
```bash
pytest tests/ -v
```

**Launch Interactive Tester:**
```bash
cd Strategy
python interactive_strategy_tester.py
```

**Check System Health:**
```bash
curl http://localhost:8000/api/health/
```

**Full Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---

## 🚨 Troubleshooting Flowchart

```
Problem occurs
    ↓
Check [STATUS.md](STATUS.md) → Known Issues
    ↓ (Not listed)
Check [SETUP_AND_INTEGRATION.md](SETUP_AND_INTEGRATION.md) → Troubleshooting
    ↓ (Not resolved)
Check test output: pytest tests/ -v
    ↓
Check debug logs: tail -f logs/algoagent.log
    ↓
See [ARCHITECTURE.md](ARCHITECTURE.md) for component details
```

---

## 📊 Documentation Statistics

| Category | Count | Status |
|----------|-------|--------|
| Core Documentation | 4 docs | ✅ Complete |
| Feature Guides | 5+ docs | ✅ Exist |
| API Documentation | 2+ docs | ✅ Exist |
| Setup & Deployment | 3 docs | ✅ Complete |
| Test Coverage | 26+ tests | ✅ Passing |
| **Total Lines of New Docs** | **5,000+** | **✅ Written** |

---

## 🔄 Document Relationships

```
QUICK_REFERENCE (Entry Point)
    ↓
SETUP_AND_INTEGRATION (Installation)
    ↓
ARCHITECTURE (System Design)
    ↓
STATUS (Monitoring & Troubleshooting)
    ↓
Feature-Specific Guides (External)
```

---

## 📝 How to Use This Index

### For Quick Lookup
1. Use the **"I want to..."** section above
2. Follow the recommended document chain
3. Use QUICK_REFERENCE for commands

### For Learning
1. Start with QUICK_REFERENCE (5 min overview)
2. Read SETUP_AND_INTEGRATION (15 min)
3. Study ARCHITECTURE (20 min)
4. Reference STATUS for specific components (10 min)

### For Troubleshooting
1. Check STATUS → Known Issues
2. Check SETUP_AND_INTEGRATION → Troubleshooting
3. Run tests: `pytest tests/ -v`
4. Check logs

### For Development
1. Read QUICK_REFERENCE → API Reference
2. Read ARCHITECTURE → Component of interest
3. Check related test file
4. Implement feature

---

## 🎓 Learning Paths

### Path 1: System Overview (30 minutes)
1. QUICK_REFERENCE (5 min)
2. ARCHITECTURE Section A-C (15 min)
3. STATUS Section 1-5 (10 min)

### Path 2: Setting Up Development Environment (1 hour)
1. SETUP_AND_INTEGRATION → Quick Start (5 min)
2. SETUP_AND_INTEGRATION → Detailed Installation (30 min)
3. QUICK_REFERENCE → Quick Commands (5 min)
4. SETUP_AND_INTEGRATION → Testing (20 min)

### Path 3: API Development (1 hour)
1. QUICK_REFERENCE → API Quick Reference (10 min)
2. ARCHITECTURE → REST API Layer (10 min)
3. PRODUCTION_API_GUIDE (30 min)
4. QUICK_REFERENCE → Common Patterns (10 min)

### Path 4: Strategy Development (1 hour)
1. QUICK_REFERENCE → Indicator Reference (10 min)
2. ARCHITECTURE Section G (15 min)
3. STRATEGY_QUICKSTART.md (20 min)
4. QUICK_REFERENCE → Common Patterns (15 min)

### Path 5: Troubleshooting (30 minutes)
1. STATUS → Known Issues (5 min)
2. SETUP_AND_INTEGRATION → Troubleshooting (15 min)
3. QUICK_REFERENCE → Common Errors (10 min)

---

## 📞 Support Resources

### Documentation
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Status & Health:** [STATUS.md](STATUS.md)
- **Quick Ref:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Setup:** [SETUP_AND_INTEGRATION.md](SETUP_AND_INTEGRATION.md)

### External Resources
- backtesting.py: https://kernc.github.io/backtesting.py/
- Gemini API: https://ai.google.dev/
- Django: https://docs.djangoproject.com/
- TA-Lib: https://mrjbq7.github.io/ta-lib/

### Tests
- Run: `pytest tests/ -v`
- Location: `tests/` directory
- Coverage: 26+ tests covering all major components

---

## ✨ What's New in This Documentation

**Created December 3, 2025:**
- ✅ **ARCHITECTURE.md** (1,400 lines) - Complete system design
- ✅ **STATUS.md** (800 lines) - Component health & troubleshooting
- ✅ **SETUP_AND_INTEGRATION.md** (900 lines) - Installation & deployment
- ✅ **QUICK_REFERENCE.md** (600 lines) - Developer quick reference
- ✅ **DOCUMENTATION_INDEX.md** (this file) - Navigation hub

**Total: 5,000+ lines of consolidated, direct documentation**

---

## 🎯 Next Steps

1. **Read QUICK_REFERENCE.md** (5 minutes)
2. **Follow SETUP_AND_INTEGRATION.md** to set up (15 minutes)
3. **Explore ARCHITECTURE.md** for deep understanding (20 minutes)
4. **Check STATUS.md** for current state (10 minutes)
5. **Start developing!**

---

## 📅 Document Maintenance

| Document | Last Updated | Review Cycle |
|----------|--------------|--------------|
| ARCHITECTURE.md | Dec 3, 2025 | Quarterly |
| STATUS.md | Dec 3, 2025 | Monthly |
| SETUP_AND_INTEGRATION.md | Dec 3, 2025 | Quarterly |
| QUICK_REFERENCE.md | Dec 3, 2025 | Quarterly |
| DOCUMENTATION_INDEX.md | Dec 3, 2025 | Quarterly |

---

**END OF DOCUMENTATION INDEX**

**Last Generated:** December 3, 2025  
**Status:** ✅ Complete & Current  
**System Status:** ✅ Production-Ready

Use the table of contents above to navigate to the documentation you need!
