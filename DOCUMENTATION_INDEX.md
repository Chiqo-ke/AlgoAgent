# AlgoAgent - Complete Documentation Index

**Last Updated:** January 26, 2026  
**Primary System:** `monolithic_agent` (Production - Integrated with Frontend)  
**Secondary System:** `multi_agent` (Research/Development - CLI Only)

---

## 🚀 Getting Started

**New to AlgoAgent?** Start here:

1. **[README.md](README.md)** - Project overview and system comparison
   - Understand the system architecture
   - **Primary System:** Monolithic Agent (production, integrated with frontend)
   - **Research System:** Multi-Agent (experimental, CLI-based)
   - See key capabilities and features

2. **[QUICK_START.md](QUICK_START.md)** - Get up and running in 5-10 minutes
   - **Recommended:** Monolithic Agent + Frontend setup
   - Prerequisites and setup
   - API keys configuration
   - Usage examples and troubleshooting

**💡 For most users:** Use the Monolithic Agent system with the Algo frontend for the complete web-based experience.

---

## 📚 System-Specific Documentation

### 🚀 Monolithic Agent System (PRIMARY - IN PRODUCTION)

**This is the main system integrated with the frontend web application.**

**Primary Resources:**
- **[monolithic_agent/README.md](monolithic_agent/README.md)** - Complete overview
  - Architecture and capabilities
  - Django REST API integration
  - Frontend integration details
  - Test results and metrics
  - Quick start guide
  
- **[monolithic_agent/DOCUMENTATION_INDEX.md](monolithic_agent/DOCUMENTATION_INDEX.md)** - Documentation hub
  - Organized by category
  - Navigation by task
  - Quick reference guides

- **[monolithic_agent/STATUS.md](monolithic_agent/STATUS.md)** - System health & status
  - Component status matrix
  - Known issues and limitations
  - Test results summary
  - Troubleshooting guide

**Documentation Structure:**
```
monolithic_agent/docs/
├── README.md                           ← Documentation overview
├── architecture/                       ← System design
│   ├── ARCHITECTURE.md
│   └── BACKEND_API_INTEGRATION.md
├── api/                               ← API documentation
│   ├── API_ENDPOINTS.md
│   ├── PRODUCTION_API_GUIDE.md
│   └── BACKEND_API_INTEGRATION.md
├── guides/                            ← User guides
│   ├── QUICK_REFERENCE.md
│   ├── BOT_EXECUTION_START_HERE.md
│   └── BOT_EXECUTION_QUICK_REFERENCE.md
├── implementation/                    ← Technical details
│   ├── KEY_ROTATION_IMPLEMENTATION_SUMMARY.md
│   ├── BOT_EXECUTION_IMPLEMENTATION_SUMMARY.md
│   └── SETUP_AND_INTEGRATION.md
└── testing/                          ← Testing documentation
    ├── E2E_TESTING_GUIDE.md
    └── E2E_TESTING_COMPLETE.md
```

---

### 🔬 Multi-Agent System (RESEARCH/DEVELOPMENT)

**This is an experimental system for research purposes. Not integrated with the frontend.**

**Primary Resources:**
- **[multi_agent/README.md](multi_agent/README.md)** - Complete overview
  - Multi-agent architecture
  - CLI interface documentation
  - Adapter system overview
  - Component descriptions

- **[multi_agent/ARCHITECTURE.md](multi_agent/ARCHITECTURE.md)** - Architecture specification
  - Single-file strategy design
  - Adapter pattern details
  - Agent interactions
  - Module layout

- **[multi_agent/QUICKSTART_GUIDE.md](multi_agent/QUICKSTART_GUIDE.md)** - Getting started guide
  - CLI interface tutorial
  - Workflow examples
  - Common tasks

**Note:** For production use and frontend integration, use the Monolithic Agent system instead.

**Documentation Structure:**
```
multi_agent/docs/
├── README.md                          ← Documentation overview
├── architecture/                      ← System design
│   ├── PLANNER_DESIGN.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   └── MIGRATION_PLAN.md
├── implementation/                    ← Technical details
│   ├── CODER_AGENT_COMPLETE.md
│   ├── TESTER_AGENT_IMPLEMENTATION_COMPLETE.md
│   ├── LLM_ROUTER_IMPLEMENTATION_SUMMARY.md
│   └── ROUTER_INTEGRATION_COMPLETE.md
├── testing/                          ← Test reports
│   ├── E2E_NO_TEMPLATES_TEST_REPORT.md
│   ├── AI_E2E_TEST_FINAL_REPORT.md
│   └── REAL_LLM_E2E_FINAL_REPORT.md
├── guides/                           ← User guides
│   ├── CLI_READY.md
│   ├── CLI_TEST_COMMAND_GUIDE.md
│   ├── ITERATIVE_LOOP_GUIDE.md
│   └── STRATEGY_NAMING_QUICKREF.md
└── api/                              ← API documentation
    ├── ARTIFACT_STORE.md
    └── llm_key_rotation.md
```

---

## 🎯 Navigation by Task

### "I want to understand the system architecture"

**Monolithic Agent:**
→ [monolithic_agent/docs/architecture/ARCHITECTURE.md](monolithic_agent/docs/architecture/ARCHITECTURE.md)

**Multi-Agent:**
→ [multi_agent/ARCHITECTURE.md](multi_agent/ARCHITECTURE.md)

---

### "I want to set up the system for the first time"

**Both Systems:**
→ [QUICK_START.md](QUICK_START.md)

**Monolithic Detailed:**
→ [monolithic_agent/docs/implementation/SETUP_AND_INTEGRATION.md](monolithic_agent/docs/implementation/SETUP_AND_INTEGRATION.md)

**Multi-Agent Detailed:**
→ [multi_agent/QUICKSTART_GUIDE.md](multi_agent/QUICKSTART_GUIDE.md)

---

### "I want to check if something is working"

**Monolithic Agent:**
→ [monolithic_agent/STATUS.md](monolithic_agent/STATUS.md)

**Both Systems:**
→ [TEST_SUMMARY.md](TEST_SUMMARY.md)

---

### "I want to use the REST API" (Monolithic Only)

**Quick Reference:**
→ [monolithic_agent/docs/guides/QUICK_REFERENCE.md](monolithic_agent/docs/guides/QUICK_REFERENCE.md)

**Complete API Docs:**
→ [monolithic_agent/docs/api/API_ENDPOINTS.md](monolithic_agent/docs/api/API_ENDPOINTS.md)

**Production Guide:**
→ [monolithic_agent/docs/api/PRODUCTION_API_GUIDE.md](monolithic_agent/docs/api/PRODUCTION_API_GUIDE.md)

---

### "I want to use the CLI" (Multi-Agent Only)

**Getting Started:**
→ [multi_agent/docs/guides/CLI_READY.md](multi_agent/docs/guides/CLI_READY.md)

**Command Guide:**
→ [multi_agent/docs/guides/CLI_TEST_COMMAND_GUIDE.md](multi_agent/docs/guides/CLI_TEST_COMMAND_GUIDE.md)

---

### "I want to create a new trading strategy"

**Monolithic Agent:**
→ [monolithic_agent/docs/guides/BOT_EXECUTION_START_HERE.md](monolithic_agent/docs/guides/BOT_EXECUTION_START_HERE.md)

**Multi-Agent:**
→ [multi_agent/docs/guides/STRATEGY_NAMING_QUICKREF.md](multi_agent/docs/guides/STRATEGY_NAMING_QUICKREF.md)

**Examples:**
→ [QUICK_START.md](QUICK_START.md) → Strategy Examples section

---

### "I want to troubleshoot a problem"

**Monolithic Agent:**
→ [monolithic_agent/STATUS.md](monolithic_agent/STATUS.md) → Troubleshooting section

**General Troubleshooting:**
→ [QUICK_START.md](QUICK_START.md) → Troubleshooting section

---

### "I want to run tests"

**Monolithic Agent:**
→ [monolithic_agent/docs/testing/E2E_TESTING_GUIDE.md](monolithic_agent/docs/testing/E2E_TESTING_GUIDE.md)

**Multi-Agent:**
→ [multi_agent/docs/testing/](multi_agent/docs/testing/)

**All Test Results:**
→ [TEST_SUMMARY.md](TEST_SUMMARY.md)

---

## 📋 Core Features Documentation

### Error Fixing System (Monolithic)
- **[E2E_AUTONOMOUS_AGENT_SUMMARY.md](monolithic_agent/docs/guides/E2E_AUTONOMOUS_AGENT_SUMMARY.md)** - Complete system capabilities
  - Architecture diagram
  - Proven end-to-end test results
  - Performance metrics

- **[AUTOMATED_ERROR_FIXING_COMPLETE.md](monolithic_agent/docs/implementation/AUTOMATED_ERROR_FIXING_COMPLETE.md)** - Error fixing main docs
  - How it works
  - Supported error types (10 total)
  - Test results

- **[BOT_ERROR_FIXING_GUIDE.md](monolithic_agent/docs/guides/BOT_ERROR_FIXING_GUIDE.md)** - Detailed usage guide
  - API reference
  - Code examples
  - Best practices

- **[QUICK_REFERENCE_ERROR_FIXING.md](monolithic_agent/docs/guides/QUICK_REFERENCE_ERROR_FIXING.md)** - Quick lookup
  - Common commands
  - Code snippets
  - Configuration examples

- **[IMPLEMENTATION_SUMMARY_ERROR_FIXING.md](monolithic_agent/docs/implementation/IMPLEMENTATION_SUMMARY_ERROR_FIXING.md)** - Technical details
  - Architecture breakdown
  - Component interactions
  - Performance characteristics

### Key Rotation System (Monolithic)
- **[monolithic_agent/docs/implementation/KEY_ROTATION_IMPLEMENTATION_SUMMARY.md](monolithic_agent/docs/implementation/KEY_ROTATION_IMPLEMENTATION_SUMMARY.md)**
  - 8-key rotation system
  - Load balancing
  - Health tracking

### Multi-Agent Orchestration (Multi-Agent)
- **[multi_agent/docs/implementation/CODER_AGENT_COMPLETE.md](multi_agent/docs/implementation/CODER_AGENT_COMPLETE.md)**
  - Coder agent implementation
  - Template fallback
  - Adapter integration

- **[multi_agent/docs/implementation/TESTER_AGENT_IMPLEMENTATION_COMPLETE.md](multi_agent/docs/implementation/TESTER_AGENT_IMPLEMENTATION_COMPLETE.md)**
  - Sandbox testing
  - Docker isolation

---

## 🧪 Testing Documentation

### Root Level Tests
- **[TEST_SUMMARY.md](TEST_SUMMARY.md)** - Quick overview of all tests
- **[SYSTEM_TEST_REPORT.md](SYSTEM_TEST_REPORT.md)** - Detailed system test results
- **[TESTING_INFRASTRUCTURE.md](TESTING_INFRASTRUCTURE.md)** - Testing framework docs
- **[TEST_DOCUMENTATION_INDEX.md](TEST_DOCUMENTATION_INDEX.md)** - Complete test docs index

### Monolithic Agent Tests
- Location: `monolithic_agent/tests/`
- **[monolithic_agent/docs/testing/E2E_TESTING_COMPLETE.md](monolithic_agent/docs/testing/E2E_TESTING_COMPLETE.md)**
- Status: 90% pass rate (18/20 tests)

### Multi-Agent Tests
- Location: `multi_agent/tests/`
- **[multi_agent/docs/testing/REAL_LLM_E2E_FINAL_REPORT.md](multi_agent/docs/testing/REAL_LLM_E2E_FINAL_REPORT.md)**
- Status: 17+ unit tests passing

---

## 📖 By Role

### For New Users
1. [README.md](README.md) - System overview
2. [QUICK_START.md](QUICK_START.md) - Get started
3. Choose system-specific README

### For API Developers (Monolithic)
1. [monolithic_agent/docs/api/API_ENDPOINTS.md](monolithic_agent/docs/api/API_ENDPOINTS.md)
2. [monolithic_agent/docs/api/PRODUCTION_API_GUIDE.md](monolithic_agent/docs/api/PRODUCTION_API_GUIDE.md)
3. [monolithic_agent/docs/guides/QUICK_REFERENCE.md](monolithic_agent/docs/guides/QUICK_REFERENCE.md)

### For Researchers (Multi-Agent)
1. [multi_agent/ARCHITECTURE.md](multi_agent/ARCHITECTURE.md)
2. [multi_agent/docs/guides/CLI_READY.md](multi_agent/docs/guides/CLI_READY.md)
3. [multi_agent/docs/architecture/PLANNER_DESIGN.md](multi_agent/docs/architecture/PLANNER_DESIGN.md)

### For System Architects
1. [monolithic_agent/docs/architecture/ARCHITECTURE.md](monolithic_agent/docs/architecture/ARCHITECTURE.md)
2. [multi_agent/ARCHITECTURE.md](multi_agent/ARCHITECTURE.md)
3. [monolithic_agent/STATUS.md](monolithic_agent/STATUS.md)

### For DevOps Engineers
1. [monolithic_agent/docs/implementation/SETUP_AND_INTEGRATION.md](monolithic_agent/docs/implementation/SETUP_AND_INTEGRATION.md)
2. [monolithic_agent/STATUS.md](monolithic_agent/STATUS.md)
3. [monolithic_agent/docs/api/PRODUCTION_API_GUIDE.md](monolithic_agent/docs/api/PRODUCTION_API_GUIDE.md)

### For QA / Testers
1. [TEST_SUMMARY.md](TEST_SUMMARY.md)
2. [SYSTEM_TEST_REPORT.md](SYSTEM_TEST_REPORT.md)
3. [TESTING_INFRASTRUCTURE.md](TESTING_INFRASTRUCTURE.md)

---

## � Organized Documentation Structure

### Root Level - Main Navigation (3 files)
- **README.md** - Project overview and system comparison
- **QUICK_START.md** - Quick start for both systems
- **DOCUMENTATION_INDEX.md** - Complete navigation hub

### Root Level - Test Documentation (4 files)
- **TEST_SUMMARY.md** - Test overview for both systems
- **SYSTEM_TEST_REPORT.md** - Detailed test results
- **TESTING_INFRASTRUCTURE.md** - Testing framework documentation
- **TEST_DOCUMENTATION_INDEX.md** - Test documentation navigation

### Monolithic Agent Documentation
- **Location:** `monolithic_agent/docs/`
- **Structure:** architecture/, api/, guides/, implementation/, testing/
- **Includes:** All error fixing docs, API docs, guides, and implementation details

### Multi-Agent Documentation
- **Location:** `multi_agent/docs/`
- **Structure:** architecture/, implementation/, testing/, guides/, api/
- **Includes:** All agent-specific docs, CLI guides, and architecture specs

### Legacy Documentation
- **Monolithic:** `monolithic_agent/_legacy_docs/`
- **Purpose:** Historical reference only
- **Note:** Current documentation in organized `docs/` folders

**Important:** All new documentation should be added to the appropriate system's `docs/` subfolder, not to root level.

---

## 📖 Quick Reference Cards

### Monolithic Agent Cheat Sheet
```bash
# Start server
cd monolithic_agent && python manage.py runserver

# Generate strategy via API
curl -X POST http://localhost:8000/api/strategies/generate_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{"description": "RSI strategy: buy <30, sell >70"}'

# Run tests
python tests/test_e2e_autonomous.py

# Check status
python manage.py check
```

### Multi-Agent Cheat Sheet
```bash
# Start CLI
cd multi_agent && python cli.py

# CLI commands
>>> submit Create RSI strategy
>>> list
>>> execute workflow_abc123
>>> status workflow_abc123
>>> exit

# Run tests
python -m pytest tests/test_*.py
```

---

## 🚀 System Status Summary

### Monolithic Agent
- **Status:** ✅ Production Ready
- **API Endpoints:** 5 operational
- **Test Pass Rate:** 90% (18/20)
- **Key Rotation:** 8 keys configured
- **Error Fixing:** 10+ error types
- **Documentation:** Complete & organized

### Multi-Agent System
- **Status:** ✅ CLI Production Ready
- **Agents:** 5 operational
- **Test Pass Rate:** 17+ unit tests
- **CLI Interface:** Interactive + command-line
- **Adapter System:** Complete
- **Documentation:** Complete & organized

---

## 📞 Support & Resources

### Getting Help
1. Check system-specific STATUS files
2. Review troubleshooting sections in QUICK_START.md
3. Check test documentation for known issues
4. Review implementation docs for technical details

### Contributing
- Both systems are modular and extensible
- Follow existing documentation structure
- Add tests for new features
- Update relevant documentation

---

**✅ All Documentation Organized! Start with [QUICK_START.md](QUICK_START.md) to begin your journey.**
- [ ] Review generated code
- [ ] Check results in results directory

---

## 📞 Contact & Support

For issues, questions, or contributions:
1. Check this documentation index
2. Review relevant documentation files
3. Examine test files for examples
4. Study source code and comments

---

**Last Updated:** December 3, 2025  
**Version:** 1.0 (Production Ready)  
**Test Status:** ✅ All Passing (14/14)
