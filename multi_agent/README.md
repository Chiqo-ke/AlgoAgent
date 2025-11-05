# Multi-Agent AI Developer System

Production-ready multi-agent architecture for automated code generation, testing, and deployment.

## Overview

This system converts the single-agent `AIDeveloperAgent` into a **Planner→Orchestrator→(Architect, Coder, Tester)** multi-agent workflow with:

- ✅ Independent, testable milestones
- ✅ Machine-readable contracts and schemas
- ✅ Durable workflow execution
- ✅ Isolated sandbox testing
- ✅ Event-driven architecture
- ✅ Git-based artifact versioning

## Architecture

```
User / API
   ↓
Planner Agent  (creates todo list JSON)
   ↓ (todo list)
Orchestrator  ─ Message Bus ─┬─> Architect Agent  --> contract + docs
   │                          ├─> Coder Agent     --> code artifacts
   │                          └─> Tester Agent    --> test results
   ↓
Artifact Store (git)
```

## Components

### 1. **Planner Service** (`planner_service/`)
- Converts natural language to structured `TodoList` JSON
- Decomposes requests into independent milestones
- Defines acceptance criteria and dependencies
- API: `POST /planner/plan`

### 2. **Orchestrator Service** (`orchestrator_service/`)
- Durable workflow engine with state management
- Task scheduling, retry policies, and timeouts
- Dependency resolution and execution ordering
- Human-in-the-loop approval checkpoints
- API: `POST /orchestrator/execute`, `GET /orchestrator/status/{workflow_id}`

### 3. **Architect Agent** (`agents/architect_agent/`)
- Generates machine-readable contracts (JSON/OpenAPI)
- Creates test skeletons and documentation
- Defines function signatures and data models
- Outputs: `contract.json`, test templates, architecture docs

### 4. **Coder Agent** (`agents/coder_agent/`) ✅
- Implements code following contracts from Architect
- Generates production-ready modules using strategy template
- Validates with static analysis (mypy, flake8)
- Uses Gemini Thinking Mode (temperature=0.1 for deterministic code)
- Outputs: source code (`Backtest/codes/`), validation reports
- Status: Complete with 17 unit tests passing

### 5. **Tester Agent** (`agents/tester_agent/`)
- Runs tests in isolated sandbox environment
- Executes acceptance criteria commands
- Produces structured test reports
- Outputs: `test_report.json`, coverage, logs

### 6. **Artifact Store** (`artifacts/`)
- Git-based versioning for code artifacts
- Metadata tracking (agent versions, prompts, commits)
- Branch strategy: `ai/generated/<workflow_id>/<task_id>`

### 7. **Message Bus** (`contracts/message_bus.py`)
- Redis-based pub/sub messaging
- Event correlation and tracing
- Channels: `agent.requests`, `agent.results`, `workflow.events`, `audit.logs`

### 8. **Debugger Agent** (`agents/debugger_agent/`) ✅
- Handles branch todos for automated debugging
- Analyzes test failures and routes to appropriate agents (coder/architect/tester)
- Classifies 5 failure types: implementation_bug, spec_mismatch, timeout, missing_dependency, flaky_test
- Collects diagnostics (tracebacks, logs, sample inputs)
- Outputs: failure reports, branch todos, fix suggestions

### 9. **Fixture Manager** (`fixture_manager/`) ✅
- Generates deterministic test data for reproducible testing
- OHLCV fixtures (seeded CSV), indicator expected values (JSON)
- Entry/exit scenario fixtures
- CLI tool: `python fixture_manager.py --symbol AAPL --bars 30`

## Planner Design: Predictable & Testable Workflows

The Planner follows a **4-step template** for all strategy workflows, ensuring predictable, independently testable milestones:

### The 4 Primary Steps

1. **Data Loading Integration** (`coder`)
   - Implement `fetch_and_prepare_data()` with OHLCV output
   - Tests: DataFrame structure, column validation, fixture comparison
   - Artifacts: `backtesting_adapter.py`, `fixtures/sample_*.csv`

2. **Indicator & Candle Pattern Loading** (`architect` → `coder`)
   - Define interfaces for indicators (RSI, MACD, etc.) and pattern detectors
   - Tests: Deterministic value checks against known fixtures
   - Artifacts: `indicator_contract.json`, `indicators/*.py`

3. **Entry Conditions Setup** (`coder`)
   - Implement `should_enter(bar, indicators, position)` logic
   - Tests: Scenarios that should/shouldn't trigger entry
   - Artifacts: `ai_strategy_entry.py`

4. **Exit Conditions Setup** (`coder`)
   - Implement `should_exit(bar, indicators, position)` with stop/target logic
   - Tests: Stop loss, take profit, signal exit scenarios
   - Artifacts: `ai_strategy_exit.py`

### Branch Todos: Automated Debugging

When a step **fails its acceptance tests**, the Orchestrator automatically creates a **branch todo**:

```json
{
  "id": "t2_branch_01",
  "parent_id": "t2_indicators",
  "title": "Debug indicator failures (RSI mismatch)",
  "agent_role": "debugger",
  "branch_reason": "test_failure",
  "debug_instructions": "RSI calculation incorrect. Expected 28.5, got 32.1.",
  "is_temporary": true,
  "max_debug_attempts": 3
}
```

**Branch Lifecycle:**
1. Primary todo fails → Orchestrator captures diagnostics
2. Failure routed to appropriate agent (`coder`, `architect`, `tester`)
3. Branch todo created and dispatched
4. Branch resolves → Parent tests re-run
5. If passes → workflow continues; if fails → escalate or retry

**Failure Routing:**
- `implementation_bug` → `coder` (logic errors, wrong calculations)
- `spec_mismatch` → `architect` (interface violations)
- `timeout` → `tester` (infinite loops, slow tests)
- `flaky_test` → `tester` (non-deterministic tests need fixtures)

### Key Benefits

✅ **Predictability** - Every workflow follows the same 4-step pattern  
✅ **Testability** - Each step has machine-executable acceptance tests  
✅ **Debuggability** - Failures auto-create targeted debug branches  
✅ **Reproducibility** - Deterministic fixtures eliminate flakiness  
✅ **Traceability** - Branch todos create clear audit trail  

See [PLANNER_DESIGN.md](PLANNER_DESIGN.md) for complete specification.

## Data Formats

### TodoList Schema (`contracts/todo_schema.json`)
Defines workflow structure with:
- Task IDs, titles, descriptions
- Agent roles and priorities
- Dependencies and acceptance criteria
- Expected artifacts and metrics

### Contract Schema (`contracts/contract_schema.json`)
Machine-readable code contracts with:
- Interface definitions (functions, classes, methods)
- Data models (Pydantic, dataclasses)
- Parameters, return types, exceptions
- Examples and test skeletons

### Test Report Schema (`contracts/test_report_schema.json`)
Structured test results with:
- Pass/fail status and summary
- Individual test outcomes
- Coverage metrics
- Environment details

## Getting Started

### Prerequisites

```powershell
# Setup virtual environment
cd c:\Users\nyaga\Documents\AlgoAgent\multi_agent
.\scripts\setup_venv.ps1  # Creates .venv and installs core dependencies

# Activate venv (optional for interactive sessions)
c:\Users\nyaga\Documents\AlgoAgent\.venv\Scripts\Activate.ps1

# Install additional dependencies (if needed)
pip install -r requirements.txt

# Install Redis (for production message bus)
# Option 1: Docker
docker run -d -p 6379:6379 redis:latest

# Option 2: Windows installer
# Download from https://redis.io/download
```

### Quick Start

```powershell
# 1. Validate a todo list
.\.venv\Scripts\python.exe -m contracts.validate_contract contracts/sample_todo_list.json --type todo

# 2. Run integration tests
.\.venv\Scripts\python.exe phase3_integration_test.py

# 3. Generate fixtures
.\.venv\Scripts\python.exe fixture_manager/fixture_manager.py --symbol AAPL --bars 30

# 4. Create a plan (requires GOOGLE_API_KEY)
$env:GOOGLE_API_KEY = "your_key"
.\.venv\Scripts\python.exe -m planner_service.planner "Create RSI momentum strategy" -o plans

# 5. Execute workflow
.\.venv\Scripts\python.exe -m orchestrator_service.orchestrator plans/workflow_*.json
```

### Validation Tools

```powershell
# Validate todo list
python -m contracts.validate_contract path/to/todo_list.json --type todo

# Validate contract
python -m contracts.validate_contract path/to/contract.json --type contract

# Validate test report
python -m contracts.validate_contract path/to/test_report.json --type test_report
```

## Development Workflow

### Phase 1: Design ✅ COMPLETE
- [x] Create `todo_schema.json` with validation and branch todo fields
- [x] Create `contract_schema.json` and `test_report_schema.json`
- [x] Build validation tools (`validate_contract.py`)
- [x] Implement event types (23 types) and message bus (Redis + InMemory)

### Phase 2: Core Services ✅ COMPLETE
- [x] Build Planner service with Gemini integration and 4-step template
- [x] Build Orchestrator with workflow engine
- [x] Implement task scheduling, retry logic, and dependency resolution
- [x] Add workflow state tracking (in-memory, DB integration pending)

### Phase 3: Core Agents ✅ COMPLETE
- [x] Implement Architect agent (contract generation with fixtures)
- [x] Implement Debugger agent (failure analysis and branch todos)
- [x] Implement Fixture Manager (deterministic test data)
- [x] Add branch todo logic to Orchestrator (depth limiting, auto-fix mode)
- [x] Integration tests for Phase 3 components (all passing)
- [x] Implement Coder agent (code generation with static analysis) - **COMPLETE**
- [ ] Implement Tester agent (sandbox execution) - **NEXT**

### Phase 4: Integration
- [ ] Build artifact store with Git integration
- [ ] Create sandbox runner with Docker
- [ ] Add human approval UI
- [ ] Implement observability and metrics

### Phase 5: Testing & Deployment
- [x] Integration tests for Phase 1-3 components
- [ ] End-to-end workflow tests (with actual LLM calls)
- [ ] CI/CD pipeline setup
- [ ] Production deployment (PostgreSQL, Redis, Git storage)

## Testing Strategy

### Unit Tests
Each module has isolated unit tests:
```powershell
pytest tests/unit/test_planner.py
pytest tests/unit/test_orchestrator.py
pytest tests/unit/test_architect_agent.py
```

### Integration Tests
Test agent interactions:
```powershell
pytest tests/integration/test_workflow_execution.py
pytest tests/integration/test_message_bus.py
```

### End-to-End Tests
Complete workflow validation:
```powershell
pytest tests/e2e/test_strategy_generation.py
```

## Security & Sandboxing

- **Docker Isolation**: All generated code runs in ephemeral containers
- **Resource Limits**: CPU, memory, and time constraints
- **Network Deny**: No network access by default
- **Security Scans**: `bandit`, secret scanning before execution
- **Allowlist**: Permitted system calls and file access

## Observability

### Metrics Tracked
- `task_pass_rate`: Success rate per task type
- `avg_iterations`: Average retries before success
- `avg_time_per_task`: Execution time by agent role
- `llm_cost_per_task`: Cost tracking
- `test_flakiness_rate`: Test reliability

### Logging
- Correlation IDs for request tracing
- Event stream in `audit.logs` channel
- Workflow state changes logged to DB
- Agent activity tracking

## Migration from Single Agent

See [MIGRATION_PLAN.md](MIGRATION_PLAN.md) for detailed rollout strategy:

1. **Week 1**: Orchestrator prototype + agent stubs
2. **Week 2-3**: Planner adapter + Architect agent
3. **Week 4-5**: Coder agent + Tester sandbox
4. **Week 6**: E2E tests + approval UI
5. **Week 7+**: Phased rollout (10% → 100%)

## API Reference

### Planner Service
- `POST /planner/plan` - Create todo list from NL request
- `GET /planner/todo_list/{id}` - Retrieve todo list

### Orchestrator Service
- `POST /orchestrator/execute` - Start workflow execution
- `GET /orchestrator/status/{workflow_id}` - Get workflow status
- `POST /orchestrator/task/{task_id}/result` - Submit task result
- `POST /orchestrator/approve/{workflow_id}` - Approve checkpoint

### Agent APIs
- `POST /agent/{role}/task` - Dispatch task to agent
- `GET /agent/{role}/status` - Get agent status

## Configuration

### Environment Variables

```ini
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM
GOOGLE_API_KEY=your_api_key
MODEL_NAME=gemini-2.0-flash

# Orchestrator
DB_URL=postgresql://user:pass@localhost/orchestrator
TASK_TIMEOUT=600
MAX_RETRIES=5

# Sandbox
DOCKER_NETWORK=none
SANDBOX_TIMEOUT=300
```

## Examples

See `contracts/sample_todo_list.json` for a complete workflow example.

## Contributing

1. Follow the schema definitions strictly
2. All generated code must pass validation
3. Add unit tests for new components
4. Update documentation for API changes

## License

MIT License - See LICENSE file

## Support

For issues and questions:
- Create GitHub issue
- Check documentation in `docs/`
- Review example workflows in `examples/`

---

**Status**: 🚧 Phase 1 Complete - Core infrastructure ready
**Next**: Implement Planner and Orchestrator services
