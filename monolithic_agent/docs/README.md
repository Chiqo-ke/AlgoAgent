# Monolithic Agent Documentation

**Last Updated:** December 4, 2025  
**Version:** 2.0 - Backend-to-API Integration Complete

---

## 📚 Documentation Structure

This documentation is organized following best practices for clear navigation and maintenance.

### Quick Links

- **[Start Here](guides/BOT_EXECUTION_START_HERE.md)** - New to the system? Begin here
- **[Quick Reference](guides/QUICK_REFERENCE.md)** - Fast lookups and common tasks
- **[Architecture Overview](architecture/ARCHITECTURE.md)** - System design and components
- **[API Integration Guide](api/BACKEND_API_INTEGRATION.md)** - Latest API updates

---

## 📂 Documentation Organization

### `/architecture` - System Design
High-level system architecture, design decisions, and component interactions.

- **[ARCHITECTURE.md](architecture/ARCHITECTURE.md)** - Complete system architecture
- **[BACKEND_API_INTEGRATION.md](api/BACKEND_API_INTEGRATION.md)** - API integration architecture

### `/api` - API Documentation
REST API endpoints, integration guides, and production deployment.

- **[BACKEND_API_INTEGRATION.md](api/BACKEND_API_INTEGRATION.md)** - Backend-to-API integration
- **[PRODUCTION_API_GUIDE.md](api/PRODUCTION_API_GUIDE.md)** - Production API deployment
- **[API_ENDPOINTS.md](api/API_ENDPOINTS.md)** - Complete endpoint reference

### `/guides` - User Guides
Step-by-step guides for common tasks and workflows.

- **[BOT_EXECUTION_START_HERE.md](guides/BOT_EXECUTION_START_HERE.md)** - Getting started
- **[QUICK_REFERENCE.md](guides/QUICK_REFERENCE.md)** - Quick command reference
- **[BOT_EXECUTION_QUICK_REFERENCE.md](guides/BOT_EXECUTION_QUICK_REFERENCE.md)** - Bot execution guide
- **[BOT_CREATION_WITH_KEY_ROTATION_QUICKSTART.md](guides/BOT_CREATION_WITH_KEY_ROTATION_QUICKSTART.md)** - Key rotation setup
- **[E2E_QUICK_REFERENCE.md](guides/E2E_QUICK_REFERENCE.md)** - End-to-end workflow

### `/implementation` - Implementation Details
Deep dives into specific features and their implementation.

- **[KEY_ROTATION_IMPLEMENTATION_SUMMARY.md](implementation/KEY_ROTATION_IMPLEMENTATION_SUMMARY.md)** - Key rotation system
- **[KEY_ROTATION_INTEGRATION.md](implementation/KEY_ROTATION_INTEGRATION.md)** - Integration guide
- **[BOT_EXECUTION_IMPLEMENTATION_SUMMARY.md](implementation/BOT_EXECUTION_IMPLEMENTATION_SUMMARY.md)** - Bot execution internals
- **[BOT_EXECUTION_INTEGRATION_GUIDE.md](implementation/BOT_EXECUTION_INTEGRATION_GUIDE.md)** - Integration details
- **[SETUP_AND_INTEGRATION.md](implementation/SETUP_AND_INTEGRATION.md)** - System setup

### `/testing` - Testing Documentation
Testing guides, methodologies, and best practices (not test reports).

- **[E2E_TESTING_GUIDE.md](testing/E2E_TESTING_GUIDE.md)** - End-to-end testing guide
- **[E2E_TESTING_COMPLETE.md](testing/E2E_TESTING_COMPLETE.md)** - Testing completion status
- **[E2E_TEST_INDEX.md](testing/E2E_TEST_INDEX.md)** - Test documentation index

---

## 🚀 Quick Start

### For New Users

1. **Read**: [BOT_EXECUTION_START_HERE.md](guides/BOT_EXECUTION_START_HERE.md)
2. **Setup**: Follow [SETUP_AND_INTEGRATION.md](implementation/SETUP_AND_INTEGRATION.md)
3. **Try**: Use [QUICK_REFERENCE.md](guides/QUICK_REFERENCE.md) for common tasks

### For API Developers

1. **Architecture**: [BACKEND_API_INTEGRATION.md](api/BACKEND_API_INTEGRATION.md)
2. **Endpoints**: [API_ENDPOINTS.md](api/API_ENDPOINTS.md)
3. **Production**: [PRODUCTION_API_GUIDE.md](api/PRODUCTION_API_GUIDE.md)

### For System Integrators

1. **Architecture**: [ARCHITECTURE.md](architecture/ARCHITECTURE.md)
2. **Key Rotation**: [KEY_ROTATION_INTEGRATION.md](implementation/KEY_ROTATION_INTEGRATION.md)
3. **Bot Execution**: [BOT_EXECUTION_INTEGRATION_GUIDE.md](implementation/BOT_EXECUTION_INTEGRATION_GUIDE.md)

---

## 🎯 Key Features

### ✅ Autonomous Bot Generation
- AI-powered strategy generation from natural language
- 8-key rotation system for high availability
- Automatic error detection and fixing
- Execution with real backtesting results

### ✅ REST API Integration
- Complete Django REST Framework implementation
- 5 core endpoints for autonomous features
- Key rotation enabled at API level
- Error fixing accessible via HTTP

### ✅ Indicator Registry
- 7 pre-built technical indicators
- Parameter schemas and examples
- Easy integration into strategies
- Browseable via API

### ✅ Execution Tracking
- SQLite-based execution history
- Performance metrics storage
- Win rate, Sharpe ratio, drawdown tracking
- Historical analysis and comparison

### ✅ Error Recovery
- 10 error types supported
- AI-powered fix generation
- Iterative fixing (up to 3 attempts)
- Success rate tracking

---

## 📊 System Status

**Current Version:** 2.0  
**Backend Status:** ✅ Fully Operational  
**API Status:** ✅ Integrated & Connected  
**Key Rotation:** ✅ Active (8 keys)  
**E2E Tests:** ✅ Passing (14/14)  

### Recent Updates (Dec 4, 2025)

- ✅ Backend-to-API integration complete
- ✅ All autonomous features exposed via REST API
- ✅ Documentation reorganized into `docs/` structure
- ✅ API architecture updated with latest changes
- ✅ Comprehensive endpoint reference created

---

## 🔍 Finding Documentation

### By Topic

**Strategy Generation:**
- [BOT_CREATION_WITH_KEY_ROTATION_QUICKSTART.md](guides/BOT_CREATION_WITH_KEY_ROTATION_QUICKSTART.md)
- [KEY_ROTATION_IMPLEMENTATION_SUMMARY.md](implementation/KEY_ROTATION_IMPLEMENTATION_SUMMARY.md)

**Bot Execution:**
- [BOT_EXECUTION_START_HERE.md](guides/BOT_EXECUTION_START_HERE.md)
- [BOT_EXECUTION_IMPLEMENTATION_SUMMARY.md](implementation/BOT_EXECUTION_IMPLEMENTATION_SUMMARY.md)

**API Integration:**
- [BACKEND_API_INTEGRATION.md](api/BACKEND_API_INTEGRATION.md)
- [API_ENDPOINTS.md](api/API_ENDPOINTS.md)

**Testing:**
- [E2E_TESTING_GUIDE.md](testing/E2E_TESTING_GUIDE.md)
- [E2E_TEST_INDEX.md](testing/E2E_TEST_INDEX.md)

### By User Type

**Developers:**
- Architecture docs in `/architecture`
- Implementation details in `/implementation`
- API reference in `/api`

**Users:**
- Getting started in `/guides`
- Quick reference in `/guides`
- FAQ in main README

**System Admins:**
- Setup guide in `/implementation`
- Production API guide in `/api`
- Testing documentation in `/testing`

---

## 🆘 Getting Help

### Common Tasks

1. **Generate a strategy**
   - Guide: [BOT_CREATION_WITH_KEY_ROTATION_QUICKSTART.md](guides/BOT_CREATION_WITH_KEY_ROTATION_QUICKSTART.md)
   - API: `POST /api/strategies/generate_with_ai/`

2. **Execute a strategy**
   - Guide: [BOT_EXECUTION_QUICK_REFERENCE.md](guides/BOT_EXECUTION_QUICK_REFERENCE.md)
   - API: `POST /api/strategies/{id}/execute/`

3. **Fix errors**
   - API: `POST /api/strategies/{id}/fix_errors/`
   - See: [BACKEND_API_INTEGRATION.md](api/BACKEND_API_INTEGRATION.md)

4. **View execution history**
   - API: `GET /api/strategies/{id}/execution_history/`
   - Database: `Backtest/codes/results/execution_history.db`

5. **Browse indicators**
   - API: `GET /api/strategies/available_indicators/`
   - Code: `Backtest/indicator_registry.py`

---

## 📞 Support Resources

### Documentation
- This README (main navigation)
- Topic-specific guides in `/guides`
- Implementation details in `/implementation`

### Code Examples
- `example_bot_execution_workflow.py`
- `minimal_bot_execution_example.py`
- `test_backend_integration.py`

### Test Files
- E2E tests in `tests/`
- Unit tests: `test_bot_error_fixer.py`, `test_indicator_registry.py`
- Integration test: `test_backend_integration.py`

---

## 🔄 Update History

### Version 2.0 (December 4, 2025)
- Backend-to-API integration complete
- All autonomous features accessible via REST API
- Documentation reorganized
- API architecture updated
- 5 new endpoints added

### Version 1.0 (December 3, 2025)
- Initial autonomous system
- Key rotation implemented
- Error fixing system
- Bot execution with tracking
- E2E testing complete

---

## 📝 Contributing

When adding new documentation:

1. Place in appropriate `/docs` subfolder
2. Update this README with links
3. Follow existing naming conventions
4. Include last-updated dates
5. Add to relevant index files

---

## ✅ Documentation Checklist

- [x] Architecture documentation
- [x] API integration guide
- [x] User guides and quick references
- [x] Implementation details
- [x] Testing guides
- [x] Code examples
- [x] Troubleshooting sections
- [x] Update history

---

**Documentation maintained by:** AlgoAgent Team  
**Last comprehensive review:** December 4, 2025  
**Next review scheduled:** As needed with major updates
