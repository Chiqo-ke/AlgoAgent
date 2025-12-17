# AlgoAgent - Autonomous Trading Strategy System

**Status:** ✅ Production Ready | **Last Updated:** December 17, 2025  
**Version:** 2.1 - Multi-Agent & Monolithic Systems Complete

---

## 🚀 Overview

AlgoAgent is a **dual-architecture autonomous trading strategy system** featuring both **monolithic** and **multi-agent** implementations. Both systems generate, test, and fix trading strategies with zero manual intervention using advanced AI capabilities.

### System Comparison

| Feature | Monolithic Agent | Multi-Agent System | Frontend |
|---------|------------------|-------------------|----------|
| **Architecture** | Single Django service | Distributed agent architecture | React + TypeScript SPA |
| **Best For** | Production trading, API integration | Research, advanced workflows | Web interface, user-friendly |
| **API** | Full Django REST API | CLI-based interface | REST client (connects to Monolithic) |
| **Interface** | REST endpoints | CLI REPL | Web dashboard with AI chat |
| **Agents** | Unified generator | Planner, Architect, Coder, Tester, Debugger | N/A (consumes Monolithic API) |
| **Execution** | Direct bot execution | Sandbox isolation with Docker | Visualizes execution from backend |
| **Error Fixing** | Integrated AI fixing | Debugger agent with failure analysis | UI for error viewing |
| **Status** | ✅ Production Ready | ✅ CLI Ready | ✅ Production Ready |

### Key Capabilities

#### ✅ Monolithic Agent
- Django REST API with 5 autonomous endpoints
- Natural language → Trading strategy code
- 8-key rotation system for high availability
- Automatic error detection and iterative fixing
- Real backtesting with performance metrics
- Execution history tracking (SQLite database)
- 7 pre-built technical indicators
- 90% E2E test pass rate (18/20 tests)

#### ✅ Multi-Agent System
- CLI interface (interactive REPL + command-line)
- Schema-aware AI with 100% valid TodoList generation
- 5 specialized agents (Planner, Orchestrator, Architect, Coder, Tester)
- Docker sandbox for isolated test execution
- Adapter architecture (same code for backtest + live)
- Template fallback for reliability
- Event-driven message bus with correlation tracking
- Deterministic testing with fixture generation

#### ✅ Frontend Application (Algo)
- Modern React 18 + TypeScript + Vite
- Full Monolithic Agent API integration (90/90 endpoints, 100%)
- AI-powered dashboard with conversational interface
- Real-time backtesting with WebSocket streams
- Type-safe service layer (19 modules, 123+ methods)
- JWT authentication & protected routes
- Comprehensive logging system
- Mobile-responsive design with shadcn/ui components

---

## 📁 Project Structure

```
AlgoAgent/
├── 📄 README.md                                    ← You are here
├── 📄 QUICK_START.md                               ← Start here for both systems
├── 📄 DOCUMENTATION_INDEX.md                       ← Complete navigation
│
├── monolithic_agent/                               ← Django REST API System
│   ├── 📄 README.md                                ← Monolithic overview
│   ├── 📄 DOCUMENTATION_INDEX.md                   ← Monolithic docs index
│   ├── 📄 STATUS.md                                ← System health & status
│   ├── manage.py                                   ← Django management
│   ├── requirements.txt                            ← Python dependencies
│   ├── start_server.ps1                            ← Quick server start
│   │
│   ├── Backtest/
│   │   ├── gemini_strategy_generator.py           ← Strategy generator with key rotation
│   │   ├── bot_executor.py                        ← Execute & capture results
│   │   ├── bot_error_fixer.py                     ← Automatic error fixing ⭐
│   │   ├── indicator_registry.py                  ← 7 pre-built indicators
│   │   └── generated_strategies/                  ← Generated bot files
│   │
│   ├── strategy_api/                              ← Django REST API
│   │   ├── views.py                               ← 5 autonomous endpoints
│   │   ├── models.py                              ← Database models
│   │   └── serializers.py                         ← Request/response schemas
│   │
│   ├── tests/                                      ← Test suites (11 files)
│   │   ├── test_e2e_autonomous.py                 ← E2E test suite ✅
│   │   ├── test_api_backend_integration.py        ← API integration tests
│   │   ├── test_backtest_api.py                   ← Backtesting API tests
│   │   ├── test_autonomous_bot_fix.py             ← Bot execution & fixing
│   │   └── test_*.py                              ← Additional test scripts
│   │
│   └── docs/                                       ← Organized documentation
│       ├── README.md                               ← Documentation index
│       ├── architecture/                           ← System design
│       ├── api/                                    ← API documentation
│       ├── guides/                                 ← User guides
│       ├── implementation/                         ← Technical details
│       └── testing/                                ← Testing documentation
│
├── multi_agent/                                    ← Multi-Agent System
│   ├── 📄 README.md                                ← Multi-agent overview
│   ├── 📄 ARCHITECTURE.md                          ← Architecture specification
│   ├── 📄 QUICKSTART_GUIDE.md                      ← Getting started
│   ├── cli.py                                      ← CLI interface ⭐
│   ├── requirements.txt                            ← Python dependencies
│   │
│   ├── planner_service/                           ← NL → TodoList
│   ├── orchestrator_service/                      ← Workflow engine
│   │
│   ├── agents/
│   │   ├── architect_agent/                       ← Contract generation
│   │   ├── coder_agent/                           ← Code implementation ⭐
│   │   ├── tester_agent/                          ← Sandbox testing
│   │   └── debugger_agent/                        ← Failure analysis
│   │
│   ├── adapters/                                  ← Universal broker interface
│   │   ├── base_adapter.py                        ← Protocol definition
│   │   ├── simbroker_adapter.py                   ← Backtesting adapter
│   │   └── live_adapter.py                        ← Live trading adapter
│   │
│   ├── simulator/                                 ← SimBroker backtesting
│   ├── sandbox_runner/                            ← Docker execution
│   ├── fixture_manager/                           ← Test data generation
│   │
│   ├── Backtest/
│   │   └── codes/                                 ← Generated strategies
│   │
│   ├── tests/                                     ← Test suites
│   │   ├── fixtures/                              ← CSV test fixtures
│   │   └── test_*.py                              ← Unit & integration tests
│   │
│   └── docs/                                      ← Organized documentation
│       ├── README.md                              ← Documentation index
│       ├── architecture/                          ← System design
│       ├── implementation/                        ← Technical details
│       ├── testing/                               ← Test reports
│       ├── guides/                                ← User guides
│       └── api/                                   ← API documentation
│
├── Algo/                                           ← Frontend Application
│   ├── 📄 FRONTEND_README.md                       ← Complete frontend docs
│   ├── 📄 README.md                                ← Quick start
│   ├── package.json                                ← Dependencies
│   ├── vite.config.ts                              ← Vite configuration
│   │
│   ├── src/
│   │   ├── components/                            ← React components
│   │   │   ├── AIAssistantPanel.tsx              ← AI chat interface
│   │   │   ├── BacktestConfigDialog.tsx          ← Backtest config
│   │   │   ├── RealtimeBacktestChart.tsx         ← Live charts
│   │   │   └── ui/                               ← shadcn/ui components
│   │   │
│   │   ├── pages/                                 ← Route pages
│   │   │   ├── Dashboard.tsx                     ← Main dashboard
│   │   │   ├── StrategyBuilder.tsx               ← Strategy creation
│   │   │   ├── Backtesting.tsx                   ← Backtest interface
│   │   │   └── Login.tsx                         ← Authentication
│   │   │
│   │   ├── lib/                                   ← Core libraries
│   │   │   ├── api.ts                            ← API client (90 endpoints)
│   │   │   ├── services.ts                       ← Service layer (123 methods)
│   │   │   ├── types.ts                          ← TypeScript types (50+ interfaces)
│   │   │   └── logger.ts                         ← Logging utility
│   │   │
│   │   └── hooks/                                 ← Custom React hooks
│   │       ├── useAuth.tsx                       ← Authentication
│   │       └── use-toast.ts                      ← Notifications
│   │
│   └── docs/                                      ← Frontend documentation
│       ├── README.md                              ← Docs index
│       ├── api/                                   ← API integration (7 files)
│       ├── guides/                                ← User guides (4 files)
│       └── implementation/                        ← Technical details (18 files)
│
└── *.md                                           ← Documentation files
```

---

## 🎯 Quick Start

### Choose Your System

#### For Web Interface → **Frontend Application**
```bash
cd Algo
npm install
npm run dev

# Access at http://localhost:5173
# Requires backend running at http://localhost:8000
```

See [Algo/FRONTEND_README.md](Algo/FRONTEND_README.md) for complete documentation.

#### For Production Trading & API Integration → **Monolithic Agent**
```powershell
cd AlgoAgent/monolithic_agent
python manage.py runserver

# Test the API
curl -X POST http://localhost:8000/api/strategies/generate_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{"description": "RSI strategy: buy when RSI < 30, sell when RSI > 70"}'
```

#### For Research & Advanced Workflows → **Multi-Agent System**
```powershell
cd AlgoAgent/multi_agent
python cli.py

# In CLI:
>>> submit Create RSI strategy: buy at RSI<30, sell at RSI>70
>>> execute workflow_abc123
```

**📖 See [QUICK_START.md](QUICK_START.md) for detailed setup instructions**

---

## 📚 Documentation

### Essential Reading

| Document | Purpose | Audience |
|----------|---------|----------|
| [QUICK_START.md](QUICK_START.md) | Get started in 5 minutes | Everyone |
| [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) | Complete navigation guide | Everyone |
| [monolithic_agent/README.md](monolithic_agent/README.md) | Monolithic system details | API developers |
| [multi_agent/README.md](multi_agent/README.md) | Multi-agent system details | Researchers |
| [monolithic_agent/STATUS.md](monolithic_agent/STATUS.md) | System health & status | DevOps |

### By Role

**New Users:**
1. [QUICK_START.md](QUICK_START.md)
2. Choose system: [monolithic_agent/README.md](monolithic_agent/README.md) or [multi_agent/README.md](multi_agent/README.md)
3. Follow system-specific quick start

**API Developers (Monolithic):**
1. [monolithic_agent/docs/api/BACKEND_API_INTEGRATION.md](monolithic_agent/docs/api/BACKEND_API_INTEGRATION.md)
2. [monolithic_agent/docs/api/API_ENDPOINTS.md](monolithic_agent/docs/api/API_ENDPOINTS.md)
3. [monolithic_agent/docs/guides/QUICK_REFERENCE.md](monolithic_agent/docs/guides/QUICK_REFERENCE.md)

**Researchers (Multi-Agent):**
1. [multi_agent/ARCHITECTURE.md](multi_agent/ARCHITECTURE.md)
2. [multi_agent/QUICKSTART_GUIDE.md](multi_agent/QUICKSTART_GUIDE.md)
3. [multi_agent/docs/guides/CLI_READY.md](multi_agent/docs/guides/CLI_READY.md)

**System Architects:**
1. [monolithic_agent/docs/architecture/ARCHITECTURE.md](monolithic_agent/docs/architecture/ARCHITECTURE.md)
2. [multi_agent/ARCHITECTURE.md](multi_agent/ARCHITECTURE.md)
3. [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) → Architecture sections

---

## ✅ System Status

### Monolithic Agent
- **Status:** ✅ Production Ready
- **API:** 5 endpoints operational
- **Tests:** 90% pass rate (18/20)
- **Key Rotation:** 8 keys configured
- **Error Fixing:** 10+ error types supported
- **Documentation:** Complete

### Multi-Agent System
- **Status:** ✅ CLI Production Ready
- **Interface:** Interactive + Command-line
- **Agents:** 5 agents operational
- **Tests:** 17+ unit tests passing
- **Adapter System:** Complete
- **Documentation:** Complete

---

## 🧪 Testing

### Monolithic Agent Tests
```powershell
cd monolithic_agent
python tests/test_e2e_autonomous.py              # E2E autonomous workflow
python tests/test_api_backend_integration.py     # API integration
python tests/test_backtest_api.py                # Backtesting API
python tests/test_autonomous_bot_fix.py          # Bot execution & error fixing
```

### Multi-Agent Tests
```powershell
cd multi_agent
python -m pytest tests/test_*.py                 # All unit tests
python cli.py --request "Create EMA strategy"    # CLI integration test
```

---

## 🔑 Key Features Summary

### Monolithic Agent
✅ Django REST API with autonomous endpoints  
✅ 8-key rotation for high availability  
✅ Automatic error detection & fixing  
✅ Real backtesting with metrics  
✅ Execution history tracking  
✅ 7 pre-built indicators  
✅ Production ready with 90% test pass rate

### Multi-Agent System
✅ CLI interface (REPL + command-line)  
✅ 5 specialized agents  
✅ Schema-aware AI with 100% valid generation  
✅ Docker sandbox isolation  
✅ Adapter architecture  
✅ Template fallback for reliability  
✅ Event-driven message bus

---

## 📖 Additional Resources

- **Issue Tracking:** See [monolithic_agent/STATUS.md](monolithic_agent/STATUS.md) for known issues
- **Testing:** See [TEST_SUMMARY.md](TEST_SUMMARY.md) for test results
- **Contributing:** Both systems are modular and extensible
- **Support:** Check system-specific README files for troubleshooting

---

## 🚧 Current Focus

### Monolithic Agent
- ⏳ Frontend integration (API ready)
- ⏳ Live trading implementation (backtesting only)
- ✅ All core features complete

### Multi-Agent System
- ⏳ Tester agent full integration
- ⏳ SQLite persistence for cross-session workflows
- ✅ CLI and core agents complete

---

**Next Steps:** See [QUICK_START.md](QUICK_START.md) to begin!
