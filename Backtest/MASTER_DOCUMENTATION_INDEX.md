# Interactive Backtest Runner - Master Documentation Index

## 📋 Overview

The **Interactive Backtest Runner v2.0** is a comprehensive backtesting system with integrated AI-powered strategy validation and code generation. This index provides quick navigation to all documentation.

---

## 🚀 Quick Start (5 Minutes)

**For impatient users:**

1. **Install dependencies**:
   ```powershell
   pip install yfinance pandas numpy google-generativeai python-dotenv
   ```

2. **Set API key**:
   ```powershell
   $env:GEMINI_API_KEY = "your-api-key"
   ```

3. **Run**:
   ```powershell
   cd c:\Users\nyaga\Documents\AlgoAgent\Backtest
   python interactive_backtest_runner.py
   ```

4. **Read**: [`QUICK_START_COMMANDS.md`](QUICK_START_COMMANDS.md) for detailed walkthrough

---

## 📚 Documentation Map

### 🎯 For First-Time Users

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [`QUICK_START_COMMANDS.md`](QUICK_START_COMMANDS.md) | Command reference & examples | **START HERE** - Complete command guide with examples |
| [`SETUP_GUIDE.md`](SETUP_GUIDE.md) | Installation instructions | Setting up environment for first time |
| [`INTERACTIVE_BACKTEST_README.md`](INTERACTIVE_BACKTEST_README.md) | Feature overview | Understanding what the system does |

### 🔧 For Strategy Development

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [`STRATEGY_INTEGRATION_GUIDE.md`](STRATEGY_INTEGRATION_GUIDE.md) | Strategy creation walkthrough | **KEY** - Learning to create/validate strategies |
| [`STRATEGY_INTEGRATION_DIAGRAM.md`](STRATEGY_INTEGRATION_DIAGRAM.md) | Visual flow diagrams | Understanding how modules connect |
| [`STRATEGY_INTEGRATION_SUMMARY.md`](STRATEGY_INTEGRATION_SUMMARY.md) | Detailed v2.0 features | Deep dive into all capabilities |
| [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) | AI code generation rules | Understanding how Gemini generates code |

### 📖 For Daily Reference

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) | Function reference card | Quick lookup during development |
| [`API_REFERENCE.md`](API_REFERENCE.md) | Complete API documentation | Deep reference for all modules |
| [`WORKFLOW_DIAGRAM.md`](WORKFLOW_DIAGRAM.md) | Step-by-step flow charts | Visualizing the process |

### 🏗️ For Advanced Users

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md) | Technical implementation details | Understanding internal architecture |
| [`MODULE_STRUCTURE.md`](MODULE_STRUCTURE.md) | Module organization | Contributing to codebase |
| [`STRATEGY_TEMPLATE.md`](STRATEGY_TEMPLATE.md) | Strategy class template | Creating custom strategies manually |

---

## 🗂️ Documentation by Topic

### Installation & Setup
- [`SETUP_GUIDE.md`](SETUP_GUIDE.md) - Complete installation process
- [`QUICK_START_COMMANDS.md`](QUICK_START_COMMANDS.md) - Command reference
- `validate_setup.py` - Automated setup validation

### Core Features (v1.0)
- [`INTERACTIVE_BACKTEST_README.md`](INTERACTIVE_BACKTEST_README.md) - Feature overview
- [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md) - Implementation details
- [`WORKFLOW_DIAGRAM.md`](WORKFLOW_DIAGRAM.md) - Visual flows

### Strategy Integration (v2.0)
- [`STRATEGY_INTEGRATION_GUIDE.md`](STRATEGY_INTEGRATION_GUIDE.md) - **Main guide**
- [`STRATEGY_INTEGRATION_SUMMARY.md`](STRATEGY_INTEGRATION_SUMMARY.md) - Complete reference
- [`STRATEGY_INTEGRATION_DIAGRAM.md`](STRATEGY_INTEGRATION_DIAGRAM.md) - Visual architecture

### Reference Materials
- [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) - Function quick ref
- [`API_REFERENCE.md`](API_REFERENCE.md) - Complete API
- [`STRATEGY_TEMPLATE.md`](STRATEGY_TEMPLATE.md) - Code template

### AI & Code Generation
- [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) - Gemini AI rules
- [`GEMINI_INTEGRATION_GUIDE.md`](GEMINI_INTEGRATION_GUIDE.md) - Gemini usage

---

## 🎓 Learning Paths

### Path A: New User → Running Backtest (15 minutes)
1. Read: [`QUICK_START_COMMANDS.md`](QUICK_START_COMMANDS.md)
2. Install dependencies (commands in doc)
3. Run: `python validate_setup.py`
4. Run: `python interactive_backtest_runner.py`
5. Choose Option 3 (Example strategy) for quick test

### Path B: Strategy Developer → Create Custom Strategy (30 minutes)
1. Read: [`STRATEGY_INTEGRATION_GUIDE.md`](STRATEGY_INTEGRATION_GUIDE.md)
2. Review: [`STRATEGY_INTEGRATION_DIAGRAM.md`](STRATEGY_INTEGRATION_DIAGRAM.md)
3. Run: `python interactive_backtest_runner.py`
4. Choose Option 1 (New strategy)
5. Enter strategy in plain English
6. Review generated code in `codes/`
7. Reference: [`STRATEGY_TEMPLATE.md`](STRATEGY_TEMPLATE.md) for manual edits

### Path C: Advanced User → System Architecture (45 minutes)
1. Read: [`STRATEGY_INTEGRATION_SUMMARY.md`](STRATEGY_INTEGRATION_SUMMARY.md)
2. Read: [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md)
3. Review: [`MODULE_STRUCTURE.md`](MODULE_STRUCTURE.md)
4. Read: [`API_REFERENCE.md`](API_REFERENCE.md)
5. Explore: Source code in `interactive_backtest_runner.py`

### Path D: Troubleshooting → Fix Issues (Variable)
1. Run: `python validate_setup.py`
2. Check: Troubleshooting section in [`SETUP_GUIDE.md`](SETUP_GUIDE.md)
3. Review: Common errors in [`QUICK_START_COMMANDS.md`](QUICK_START_COMMANDS.md)
4. Reference: [`API_REFERENCE.md`](API_REFERENCE.md) for function signatures

---

## 📂 File Organization

### Main Execution Files
```
interactive_backtest_runner.py    # v2.0 with strategy integration
quick_interactive_backtest.py     # Quick mode with defaults
run_interactive_backtest.bat      # Windows launcher (full)
run_quick_backtest.bat            # Windows launcher (quick)
validate_setup.py                 # Setup validator
```

### Documentation Files
```
MASTER_DOCUMENTATION_INDEX.md     # ← You are here
QUICK_START_COMMANDS.md           # Command reference
SETUP_GUIDE.md                    # Installation guide
INTERACTIVE_BACKTEST_README.md    # Feature overview
STRATEGY_INTEGRATION_GUIDE.md     # Strategy creation guide
STRATEGY_INTEGRATION_SUMMARY.md   # Complete v2.0 reference
STRATEGY_INTEGRATION_DIAGRAM.md   # Visual diagrams
IMPLEMENTATION_SUMMARY.md         # Technical details
WORKFLOW_DIAGRAM.md               # Flow charts
QUICK_REFERENCE.md                # Function reference
API_REFERENCE.md                  # API docs
STRATEGY_TEMPLATE.md              # Code template
SYSTEM_PROMPT.md                  # AI rules
```

### Generated Files (Runtime)
```
codes/
  *.py                             # Generated strategy code
  *.json                           # Canonical strategy JSON

results/
  *_trades_*.csv                   # Trade logs
  *_metrics_*.json                 # Performance metrics
```

---

## 🔍 Quick Search

### "How do I..."

| Task | Document | Section |
|------|----------|---------|
| **Install the system?** | [`SETUP_GUIDE.md`](SETUP_GUIDE.md) | Prerequisites |
| **Run my first backtest?** | [`QUICK_START_COMMANDS.md`](QUICK_START_COMMANDS.md) | Example Session |
| **Create a new strategy?** | [`STRATEGY_INTEGRATION_GUIDE.md`](STRATEGY_INTEGRATION_GUIDE.md) | Option 1: New Strategy |
| **Use an existing strategy?** | [`STRATEGY_INTEGRATION_GUIDE.md`](STRATEGY_INTEGRATION_GUIDE.md) | Option 2: Existing |
| **Understand the workflow?** | [`STRATEGY_INTEGRATION_DIAGRAM.md`](STRATEGY_INTEGRATION_DIAGRAM.md) | Interactive Runner Flow |
| **Fix an error?** | [`SETUP_GUIDE.md`](SETUP_GUIDE.md) | Troubleshooting |
| **Find a function?** | [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) | Function Reference |
| **Understand AI generation?** | [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) | Full document |
| **Compare v1 vs v2?** | [`STRATEGY_INTEGRATION_SUMMARY.md`](STRATEGY_INTEGRATION_SUMMARY.md) | Before & After |
| **See visual flows?** | [`STRATEGY_INTEGRATION_DIAGRAM.md`](STRATEGY_INTEGRATION_DIAGRAM.md) | All diagrams |

### "What is..."

| Concept | Document | Explanation |
|---------|----------|-------------|
| **SimBroker?** | [`API_REFERENCE.md`](API_REFERENCE.md) | Simulated broker class |
| **StrategyValidatorBot?** | [`STRATEGY_INTEGRATION_GUIDE.md`](STRATEGY_INTEGRATION_GUIDE.md) | AI strategy validator |
| **Canonical JSON?** | [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) | Strategy definition format |
| **GeminiStrategyGenerator?** | [`GEMINI_INTEGRATION_GUIDE.md`](GEMINI_INTEGRATION_GUIDE.md) | AI code generator |
| **DataFetcher?** | [`API_REFERENCE.md`](API_REFERENCE.md) | Market data loader |
| **on_bar()?** | [`STRATEGY_TEMPLATE.md`](STRATEGY_TEMPLATE.md) | Strategy callback method |

---

## 📊 System Capabilities Matrix

| Feature | v1.0 | v2.0 | Document |
|---------|------|------|----------|
| Interactive symbol selection | ✅ | ✅ | [`INTERACTIVE_BACKTEST_README.md`](INTERACTIVE_BACKTEST_README.md) |
| Date range input | ✅ | ✅ | [`INTERACTIVE_BACKTEST_README.md`](INTERACTIVE_BACKTEST_README.md) |
| Data fetching (Yahoo Finance) | ✅ | ✅ | [`SETUP_GUIDE.md`](SETUP_GUIDE.md) |
| Multiple timeframes | ✅ | ✅ | [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) |
| Configuration (fees, slippage) | ✅ | ✅ | [`API_REFERENCE.md`](API_REFERENCE.md) |
| Example strategy | ✅ | ✅ | [`STRATEGY_TEMPLATE.md`](STRATEGY_TEMPLATE.md) |
| **AI strategy validation** | ❌ | ✅ | [`STRATEGY_INTEGRATION_GUIDE.md`](STRATEGY_INTEGRATION_GUIDE.md) |
| **Natural language input** | ❌ | ✅ | [`STRATEGY_INTEGRATION_GUIDE.md`](STRATEGY_INTEGRATION_GUIDE.md) |
| **Automatic code generation** | ❌ | ✅ | [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) |
| **Strategy library** | ❌ | ✅ | [`STRATEGY_INTEGRATION_SUMMARY.md`](STRATEGY_INTEGRATION_SUMMARY.md) |
| **Dynamic strategy loading** | ❌ | ✅ | [`STRATEGY_INTEGRATION_SUMMARY.md`](STRATEGY_INTEGRATION_SUMMARY.md) |
| **Three strategy sources** | ❌ | ✅ | [`STRATEGY_INTEGRATION_GUIDE.md`](STRATEGY_INTEGRATION_GUIDE.md) |

---

## 🏆 Recommended Reading Order

### For Complete Understanding (90 minutes)

**Phase 1: Setup (15 min)**
1. [`SETUP_GUIDE.md`](SETUP_GUIDE.md)
2. [`QUICK_START_COMMANDS.md`](QUICK_START_COMMANDS.md)
3. Run `python validate_setup.py`

**Phase 2: Core Features (20 min)**
4. [`INTERACTIVE_BACKTEST_README.md`](INTERACTIVE_BACKTEST_README.md)
5. [`WORKFLOW_DIAGRAM.md`](WORKFLOW_DIAGRAM.md)
6. Run `python interactive_backtest_runner.py` (Option 3)

**Phase 3: Strategy Integration (30 min)**
7. [`STRATEGY_INTEGRATION_GUIDE.md`](STRATEGY_INTEGRATION_GUIDE.md)
8. [`STRATEGY_INTEGRATION_DIAGRAM.md`](STRATEGY_INTEGRATION_DIAGRAM.md)
9. Run `python interactive_backtest_runner.py` (Option 1)

**Phase 4: Advanced Topics (25 min)**
10. [`STRATEGY_INTEGRATION_SUMMARY.md`](STRATEGY_INTEGRATION_SUMMARY.md)
11. [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md)
12. [`API_REFERENCE.md`](API_REFERENCE.md)

---

## 🛠️ Module Integration Map

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM OVERVIEW                          │
└─────────────────────────────────────────────────────────────┘

Data Module              Strategy Module           Backtest Module
(../Data/)              (../Strategy/)            (Backtest/)
    │                        │                          │
    ├─ data_fetcher.py       ├─ strategy_validator.py  ├─ interactive_backtest_runner.py ★
    ├─ indicator_calculator  ├─ StrategyValidatorBot   ├─ sim_broker.py
    └─ fetch_data_by_        └─ validate_strategy()    ├─ gemini_strategy_generator.py
       date_range()                                     └─ GeminiStrategyGenerator
         │                          │                          │
         └──────────────────────────┼──────────────────────────┘
                                    │
                      ┌─────────────▼────────────┐
                      │  Unified Backtest Flow   │
                      │  • Data fetch            │
                      │  • Strategy validate     │
                      │  • Code generate         │
                      │  • Execute backtest      │
                      │  • Save results          │
                      └──────────────────────────┘

★ = Main entry point
```

**See**: [`STRATEGY_INTEGRATION_DIAGRAM.md`](STRATEGY_INTEGRATION_DIAGRAM.md) for detailed diagrams

---

## 📝 Version History

| Version | Date | Key Features | Primary Document |
|---------|------|--------------|------------------|
| **v1.0** | Oct 19, 2024 | Interactive backtest, data fetch | [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md) |
| **v2.0** | Oct 22, 2024 | Strategy integration, AI validation, code gen | [`STRATEGY_INTEGRATION_SUMMARY.md`](STRATEGY_INTEGRATION_SUMMARY.md) |

---

## 🎯 Decision Tree

**"Which document should I read?"**

```
START
  │
  ├─ Never used the system?
  │  └─► SETUP_GUIDE.md → QUICK_START_COMMANDS.md
  │
  ├─ Want to run a quick test?
  │  └─► QUICK_START_COMMANDS.md (Method 3: Quick Mode)
  │
  ├─ Want to create new strategy?
  │  └─► STRATEGY_INTEGRATION_GUIDE.md (Option 1)
  │
  ├─ Want to understand architecture?
  │  └─► STRATEGY_INTEGRATION_DIAGRAM.md
  │
  ├─ Need function reference?
  │  └─► QUICK_REFERENCE.md or API_REFERENCE.md
  │
  ├─ Troubleshooting an error?
  │  └─► SETUP_GUIDE.md (Troubleshooting) + validate_setup.py
  │
  ├─ Want complete details?
  │  └─► STRATEGY_INTEGRATION_SUMMARY.md
  │
  └─ Need command examples?
     └─► QUICK_START_COMMANDS.md
```

---

## 💡 Pro Tips

### Documentation
- **Bookmark this index** for quick navigation
- Start with `QUICK_START_COMMANDS.md` for immediate action
- Use `QUICK_REFERENCE.md` during development
- Reference `API_REFERENCE.md` for deep dives

### Development
- Always run `validate_setup.py` after environment changes
- Use Option 3 (Example) for quick testing
- Save successful strategies (auto-saved in `codes/`)
- Review generated code to learn patterns

### Workflow
- **New idea**: Option 1 → Validate → Generate → Test
- **Refinement**: Option 2 → Load existing → Modify params
- **Comparison**: Same data, different strategies
- **Optimization**: Same strategy, different parameters

---

## 🆘 Getting Help

### Self-Service
1. Check [`QUICK_START_COMMANDS.md`](QUICK_START_COMMANDS.md) troubleshooting section
2. Run `python validate_setup.py` to check setup
3. Review error-specific docs:
   - Import errors: [`SETUP_GUIDE.md`](SETUP_GUIDE.md) Prerequisites
   - API errors: [`GEMINI_INTEGRATION_GUIDE.md`](GEMINI_INTEGRATION_GUIDE.md)
   - Strategy errors: [`STRATEGY_INTEGRATION_GUIDE.md`](STRATEGY_INTEGRATION_GUIDE.md)

### Documentation Search
- Use Ctrl+F in this index to find topics
- Check "Quick Search" section above
- Follow learning paths for structured guidance

---

## 📌 Key Files Quick Access

### Must-Read (First Session)
1. [`QUICK_START_COMMANDS.md`](QUICK_START_COMMANDS.md)
2. [`SETUP_GUIDE.md`](SETUP_GUIDE.md)
3. [`STRATEGY_INTEGRATION_GUIDE.md`](STRATEGY_INTEGRATION_GUIDE.md)

### Daily Reference
1. [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md)
2. [`API_REFERENCE.md`](API_REFERENCE.md)

### Deep Dives
1. [`STRATEGY_INTEGRATION_SUMMARY.md`](STRATEGY_INTEGRATION_SUMMARY.md)
2. [`STRATEGY_INTEGRATION_DIAGRAM.md`](STRATEGY_INTEGRATION_DIAGRAM.md)
3. [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md)

---

## 🚦 Status Indicators

### System Status
- ✅ **v2.0 Complete** - All strategy integration features implemented
- ✅ **Tested** - Core functionality validated
- ⚠️ **Requires Setup** - User must install dependencies and API keys

### Documentation Status
- ✅ **Complete** - All features documented
- ✅ **Up-to-date** - Reflects v2.0 capabilities
- ✅ **Comprehensive** - 10+ documents covering all aspects

### Next Steps for Users
1. Install dependencies (`pip install ...`)
2. Configure Gemini API key
3. Run validation (`python validate_setup.py`)
4. Start backtesting (`python interactive_backtest_runner.py`)

---

## 📧 Document Maintenance

This index is maintained alongside the codebase. When new features are added:
1. Update relevant feature documents
2. Add new documents to this index
3. Update learning paths if necessary
4. Refresh version history

**Last Updated**: October 22, 2024 (v2.0 Release)

---

## 🎉 Ready to Start?

**Run this command now:**
```powershell
cd c:\Users\nyaga\Documents\AlgoAgent\Backtest
python interactive_backtest_runner.py
```

**Or start with validation:**
```powershell
python validate_setup.py
```

**Need help? Start here:**
- **Installation**: [`SETUP_GUIDE.md`](SETUP_GUIDE.md)
- **Quick commands**: [`QUICK_START_COMMANDS.md`](QUICK_START_COMMANDS.md)
- **Strategy creation**: [`STRATEGY_INTEGRATION_GUIDE.md`](STRATEGY_INTEGRATION_GUIDE.md)

---

**Happy Backtesting! 🚀📈**
