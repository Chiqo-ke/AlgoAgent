# Scripts Directory

**Purpose:** Utility scripts, diagnostic tools, and temporary test files  
**Last Updated:** January 26, 2026

---

## Directory Structure

```
scripts/
├── diagnostics/      - System health checks and diagnostics
├── utilities/        - Database cleanup, model lists, and utilities
└── temp_tests/       - Temporary test scripts (can be deleted)
```

---

## Diagnostics (`diagnostics/`)

**Purpose:** Check system health, API status, and component configuration

### API & Model Diagnostics

| Script | Purpose | Usage |
|--------|---------|-------|
| `check_all_quotas.py` | Check quota status for all API keys | `python scripts/diagnostics/check_all_quotas.py` |
| `check_models.py` | List available Gemini models | `python scripts/diagnostics/check_models.py` |
| `diagnose_api_keys.py` | Comprehensive API key diagnostics | `python scripts/diagnostics/diagnose_api_keys.py` |
| `verify_api_key_projects.py` | Verify API key project assignments | `python scripts/diagnostics/verify_api_key_projects.py` |

### Copilot Diagnostics

| Script | Purpose | Usage |
|--------|---------|-------|
| `check_copilot_token.py` | Check GitHub Copilot token status | `python scripts/diagnostics/check_copilot_token.py` |
| `verify_copilot_setup.py` | Verify complete Copilot integration | `python scripts/diagnostics/verify_copilot_setup.py` |
| `quick_status.py` | Quick Copilot authentication status | `python scripts/diagnostics/quick_status.py` |

### System Diagnostics

| Script | Purpose | Usage |
|--------|---------|-------|
| `check_routes.py` | Verify Django API route registration | `python scripts/diagnostics/check_routes.py` |
| `check_bot_performance.py` | Check bot execution performance | `python scripts/diagnostics/check_bot_performance.py` |

---

## Utilities (`utilities/`)

**Purpose:** Maintenance scripts, cleanup tools, and data management

### Database Management

| Script | Purpose | Usage |
|--------|---------|-------|
| `cleanup_database_records.py` | Remove strategy and backtest records | `python scripts/utilities/cleanup_database_records.py` |
| `list_database_tables.py` | List all database tables and counts | `python scripts/utilities/list_database_tables.py` |

### File & Code Management

| Script | Purpose | Usage |
|--------|---------|-------|
| `cleanup_generated_files.py` | Remove generated strategy files | `python scripts/utilities/cleanup_generated_files.py` |
| `update_templates.py` | Update strategy templates | `python scripts/utilities/update_templates.py` |
| `verify_templates.py` | Verify template system | `python scripts/utilities/verify_templates.py` |

### API & Model Utilities

| Script | Purpose | Usage |
|--------|---------|-------|
| `list_available_models.py` | List all available AI models | `python scripts/utilities/list_available_models.py` |
| `list_models.py` | Alternative model listing | `python scripts/utilities/list_models.py` |
| `refresh_copilot_auth.py` | Refresh Copilot authentication token | `python scripts/utilities/refresh_copilot_auth.py` |

---

## Temporary Tests (`temp_tests/`)

**Purpose:** Ad-hoc test scripts created during development

⚠️ **Note:** These files are temporary and can be safely deleted after verification

| Script | Purpose | Status |
|--------|---------|--------|
| `create_working_bot_strategy.py` | Create test bot strategy | Can be deleted |
| `quick_test_settings_fix.py` | Test settings configuration | Can be deleted |

**Recommendation:** Review and delete these files once their functionality is confirmed working in the main test suite.

---

## Usage Guidelines

### Running Diagnostic Scripts

```bash
# Change to monolithic_agent directory
cd c:\Users\nyaga\Documents\AlgoAgent\monolithic_agent

# Run any diagnostic script
python scripts/diagnostics/check_all_quotas.py
```

### Running Utility Scripts

```bash
# Database cleanup
python scripts/utilities/cleanup_database_records.py

# File cleanup
python scripts/utilities/cleanup_generated_files.py

# Refresh Copilot auth
python scripts/utilities/refresh_copilot_auth.py
```

### Common Maintenance Tasks

**Check System Health:**
```bash
python scripts/diagnostics/check_all_quotas.py
python scripts/diagnostics/check_routes.py
python scripts/diagnostics/quick_status.py
```

**Clean Up After Testing:**
```bash
python scripts/utilities/cleanup_database_records.py
python scripts/utilities/cleanup_generated_files.py
```

**Model & API Information:**
```bash
python scripts/utilities/list_available_models.py
python scripts/diagnostics/diagnose_api_keys.py
```

---

## Integration with Main Test Suite

These scripts complement the main test suite in `tests/`:

| Purpose | Location | Type |
|---------|----------|------|
| **Automated Tests** | `tests/` | pytest-based unit/integration tests |
| **Diagnostics** | `scripts/diagnostics/` | Manual health checks |
| **Utilities** | `scripts/utilities/` | Maintenance & cleanup |
| **Temp Tests** | `scripts/temp_tests/` | Ad-hoc testing (delete after use) |

---

## Migration Notes

**Moved from Root (January 26, 2026):**
- Diagnostics: 9 files moved from root to `scripts/diagnostics/`
- Utilities: 8 files moved from root to `scripts/utilities/`
- Temp Tests: 2 files moved from root to `scripts/temp_tests/`
- Test Files: 17 files moved from root to `tests/`

**Reason:** Cleanup and organization of monolithic_agent repository

**Impact:** None - All scripts remain functional with updated paths

---

## Maintenance

### Adding New Scripts

**Diagnostics:**
- Place in `scripts/diagnostics/` if it checks system health
- Name pattern: `check_*.py`, `verify_*.py`, `diagnose_*.py`

**Utilities:**
- Place in `scripts/utilities/` if it performs maintenance
- Name pattern: `cleanup_*.py`, `list_*.py`, `update_*.py`

**Temporary Tests:**
- Place in `scripts/temp_tests/` if it's a quick test
- Delete after functionality is confirmed in main tests

### Periodic Cleanup

**Monthly:**
- Review `scripts/temp_tests/` and delete obsolete files
- Update this README if scripts are added/removed
- Verify all diagnostic scripts still work

**Quarterly:**
- Archive old temp test files if not deleted
- Review utility scripts for deprecation
- Update documentation

---

## Related Documentation

- **Main Tests:** [tests/README.md](../tests/README.md) - pytest test suite
- **Testing Guide:** [docs/testing/E2E_TESTING_GUIDE.md](../docs/testing/E2E_TESTING_GUIDE.md)
- **Status Report:** [docs/testing/STATUS.md](../docs/testing/STATUS.md)

---

*This README provides a complete reference for all utility scripts in the monolithic_agent system.*
