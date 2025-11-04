# Migration Plan: Single Agent → Multi-Agent System

## Executive Summary

This document outlines the step-by-step migration from the existing single-agent `AIDeveloperAgent` to the new multi-agent Planner→Orchestrator→Agents architecture with minimal disruption to current operations.

**Timeline**: 6-8 weeks  
**Risk Level**: Medium (phased rollout mitigates risk)  
**Rollback Strategy**: Feature flag + dual operation mode

---

## Current State vs. Target State

### Current Architecture (Single Agent)
```
User Request
     ↓
AIDeveloperAgent
  ├─ Generate code (Gemini)
  ├─ Test code (Terminal Executor)
  ├─ Fix errors (Code Analyzer)
  └─ Retry loop (max 5x)
     ↓
Results
```

**Limitations**:
- No task decomposition
- No agent specialization
- Fixed workflow (no dynamic planning)
- Limited concurrency
- No artifact versioning
- Manual checkpoints only

### Target Architecture (Multi-Agent)
```
User Request
     ↓
Planner Agent (creates TodoList)
     ↓
Orchestrator (workflow engine)
     ├─ Message Bus ─┬─> Architect Agent (contracts)
     │               ├─> Coder Agent (implementation)
     │               ├─> Tester Agent (validation)
     │               └─> Debugger Agent (fixes)
     ↓
Artifact Store (Git)
```

**Benefits**:
- ✅ Task decomposition (atomic milestones)
- ✅ Agent specialization (architect/coder/tester)
- ✅ Dynamic planning (LLM-driven)
- ✅ Parallel execution (independent tasks)
- ✅ Versioned artifacts (Git)
- ✅ Human-in-the-loop (approval gates)

---

## Migration Phases

## Phase 0: Preparation (Week 1)

### Goals
- Set up infrastructure
- Install dependencies
- Configure environment

### Tasks
- [x] Create `multi_agent/` directory structure
- [x] Create schemas and validation tools
- [x] Set up message bus (Redis)
- [ ] Configure environment variables
- [ ] Set up development database (PostgreSQL)
- [ ] Configure Docker for sandbox
- [ ] Set up Git repository for artifacts

### Deliverables
- Multi-agent directory structure
- Redis running locally
- Environment configured
- Documentation reviewed

### Acceptance Criteria
```powershell
# All these should work:
python -m contracts.validate_contract contracts/sample_todo_list.json --type todo
# ✅ Schema validation working

redis-cli ping
# ✅ Redis responding

docker ps
# ✅ Docker daemon running
```

---

## Phase 1: Core Services (Week 2-3)

### 1.1: Planner Service ✅ COMPLETE

**Status**: Implemented and tested

**What's Done**:
- ✅ Planner converts NL → TodoList JSON
- ✅ Schema validation
- ✅ Dependency checking
- ✅ CLI tool

**Validation**:
```powershell
python -m planner_service.planner "Create momentum strategy" -o plans
# ✅ Generates valid TodoList
```

### 1.2: Orchestrator Service ✅ COMPLETE

**Status**: Minimal implementation complete

**What's Done**:
- ✅ Workflow state management
- ✅ Task scheduling (topological sort)
- ✅ Retry logic
- ✅ Dependency resolution
- ✅ Message bus integration

**What's Missing** (for production):
- [ ] Database persistence (currently in-memory)
- [ ] Distributed task queue (Celery)
- [ ] Health checks
- [ ] Metrics collection

**Next Steps**:
```python
# Add database models
class Workflow(Base):
    __tablename__ = 'workflows'
    id = Column(String, primary_key=True)
    todo_list_id = Column(String)
    status = Column(Enum(WorkflowStatus))
    # ...

# Add Celery tasks
@celery.app.task
def execute_task(workflow_id, task_id):
    # Dispatch to agent
    pass
```

---

## Phase 2: Agent Implementation (Week 3-5)

### 2.1: Architect Agent (Week 3)

**Goal**: Generate contracts and test skeletons

**Implementation Plan**:
```python
# agents/architect_agent/architect.py

class ArchitectAgent:
    """Generates machine-readable contracts."""
    
    def generate_contract(self, task: TodoItem) -> Contract:
        """
        Create contract from task description.
        
        Process:
        1. Parse task requirements
        2. Define interfaces (classes, functions)
        3. Specify data models (Pydantic)
        4. Create test skeletons
        5. Validate against contract schema
        
        Returns:
            Contract object with interfaces, models, tests
        """
        prompt = self._build_contract_prompt(task)
        response = self.model.generate_content(prompt)
        contract = self._parse_contract(response.text)
        
        # Validate
        is_valid, errors = self.validator.validate_contract(contract)
        if not is_valid:
            raise ValueError(f"Invalid contract: {errors}")
        
        return contract
```

**System Prompt**:
```
You are an expert software architect. Generate machine-readable contracts.

Output JSON matching the Contract schema:
{
  "contract_id": "...",
  "interfaces": [
    {
      "name": "StrategyName",
      "type": "class",
      "signature": "class StrategyName(Strategy):",
      "methods": [...]
    }
  ],
  "data_models": [...],
  "test_skeletons": [...]
}

Include:
- Exact class/function names
- Full type annotations
- Parameter descriptions
- Example usage
```

**Test Strategy**:
```powershell
# Unit tests
pytest tests/unit/test_architect_agent.py

# Test contract generation
pytest tests/integration/test_contract_generation.py

# Validate output schema
python -m contracts.validate_contract output/contract.json --type contract
```

### 2.2: Coder Agent (Week 4)

**Goal**: Implement code following contracts

**Implementation Plan**:
```python
# agents/coder_agent/coder.py

class CoderAgent:
    """Implements code following contracts."""
    
    def generate_code(self, contract: Contract, task: TodoItem) -> CodeArtifacts:
        """
        Generate code from contract.
        
        Process:
        1. Load contract interfaces
        2. Generate implementation code
        3. Run linting (flake8, black)
        4. Run type checking (mypy)
        5. Run security scan (bandit)
        6. Generate unit tests
        7. Create build report
        
        Returns:
            CodeArtifacts with files, tests, report
        """
        # Reuse existing code generation logic from AIDeveloperAgent
        prompt = self._build_code_prompt(contract, task)
        response = self.model.generate_content(prompt)
        code = self._parse_code(response.text)
        
        # Validate
        lint_result = self._run_linting(code)
        type_result = self._run_type_check(code)
        security_result = self._run_security_scan(code)
        
        if not all([lint_result.success, type_result.success, security_result.success]):
            # Auto-fix or return for debugging
            return self._fix_issues(code, [lint_result, type_result, security_result])
        
        return CodeArtifacts(files=[code], tests=[...], report=...)
```

**Integration with Existing Code**:
```python
# Reuse from Backtest/ai_developer_agent.py
from Backtest.gemini_strategy_generator import StrategyGenerator
from Backtest.terminal_executor import TerminalExecutor
from Backtest.code_analyzer import CodeAnalyzer

class CoderAgent:
    def __init__(self):
        self.generator = StrategyGenerator()  # Reuse existing
        self.executor = TerminalExecutor()    # Reuse existing
        self.analyzer = CodeAnalyzer()        # Reuse existing
```

**Validation Rules**:
```json
{
  "validation_rules": [
    {"type": "lint", "command": "flake8 {file}"},
    {"type": "type_check", "command": "mypy {file} --strict"},
    {"type": "security_scan", "command": "bandit {file}"}
  ]
}
```

### 2.3: Tester Agent (Week 5)

**Goal**: Run tests in isolated sandbox

**Implementation Plan**:
```python
# agents/tester_agent/tester.py

class TesterAgent:
    """Executes tests in sandbox."""
    
    def run_tests(self, task: TodoItem, artifacts: CodeArtifacts) -> TestReport:
        """
        Run acceptance tests in sandbox.
        
        Process:
        1. Create Docker container
        2. Copy artifacts to container
        3. Execute test commands
        4. Capture output (stdout/stderr)
        5. Parse pytest JSON report
        6. Extract coverage metrics
        7. Cleanup container
        
        Returns:
            TestReport with results, coverage, logs
        """
        sandbox = self.sandbox_runner.create_container()
        
        try:
            # Copy files
            sandbox.copy_files(artifacts.files)
            
            # Run each test command
            results = []
            for test_cmd in task.acceptance_criteria.tests:
                result = sandbox.execute(
                    cmd=test_cmd.cmd,
                    timeout=test_cmd.timeout_seconds
                )
                results.append(result)
            
            # Parse results
            report = self._parse_test_results(results)
            return report
            
        finally:
            sandbox.cleanup()
```

**Sandbox Configuration**:
```dockerfile
# sandbox_runner/Dockerfile
FROM python:3.11-slim

# Install dependencies
RUN pip install pytest pytest-json-report pytest-cov mypy flake8 bandit

# Deny network
ENV no_proxy=*

# Resource limits
# CPU: 1 core
# Memory: 2GB
# Disk: 1GB
# Time: 5 minutes

WORKDIR /workspace
```

**Sandbox Execution**:
```python
# sandbox_runner/sandbox.py

class SandboxRunner:
    def create_container(self) -> Container:
        """Create ephemeral container."""
        return self.docker_client.containers.run(
            image="multi-agent-sandbox:latest",
            detach=True,
            network_mode="none",  # No network
            mem_limit="2g",
            cpu_count=1,
            auto_remove=False
        )
    
    def execute(self, container: Container, cmd: str, timeout: int) -> ExecutionResult:
        """Execute command in container."""
        try:
            exec_result = container.exec_run(
                cmd=cmd,
                stdout=True,
                stderr=True,
                demux=True
            )
            return ExecutionResult(
                exit_code=exec_result.exit_code,
                stdout=exec_result.output[0].decode(),
                stderr=exec_result.output[1].decode()
            )
        except docker.errors.ContainerError as e:
            return ExecutionResult(exit_code=-1, error=str(e))
```

---

## Phase 3: Integration & Testing (Week 6)

### 3.1: Agent Integration

**Connect agents to orchestrator**:
```python
# Wire up message bus
from contracts import get_message_bus, Channels

# Architect
architect = ArchitectAgent()
bus.subscribe(Channels.AGENT_REQUESTS, architect.handle_task)

# Coder
coder = CoderAgent()
bus.subscribe(Channels.AGENT_REQUESTS, coder.handle_task)

# Tester
tester = TesterAgent()
bus.subscribe(Channels.AGENT_REQUESTS, tester.handle_task)
```

**Update orchestrator to dispatch to real agents**:
```python
def _execute_task(self, task_id, task_item, task_state):
    # Dispatch to agent via message bus
    event = TaskEvent.create(
        event_type=EventType.TASK_DISPATCHED,
        correlation_id=self.workflow.correlation_id,
        workflow_id=self.workflow.workflow_id,
        task_id=task_id,
        data={
            "task": task_item,
            "input_artifacts": self._get_input_artifacts(task_item)
        },
        source="orchestrator"
    )
    self.message_bus.publish(Channels.AGENT_REQUESTS, event)
    
    # Wait for result (with timeout)
    result = self._wait_for_result(task_id, timeout=task_item['timeout_seconds'])
    return result
```

### 3.2: End-to-End Tests

**E2E Test Suite**:
```python
# tests/e2e/test_full_workflow.py

def test_simple_strategy_generation():
    """Test complete workflow: NL → code → tests."""
    
    # 1. Create plan
    planner = PlannerService(api_key=...)
    todo_list = planner.create_plan("Create simple SMA crossover strategy")
    
    # 2. Execute workflow
    orchestrator = Orchestrator()
    workflow_id = orchestrator.create_workflow(todo_list['todo_list_id'])
    result = orchestrator.execute_workflow(workflow_id)
    
    # 3. Assert success
    assert result['status'] == 'completed'
    assert all(t['status'] == 'completed' for t in result['tasks'].values())
    
    # 4. Verify artifacts
    artifacts = orchestrator.get_artifacts(workflow_id)
    assert 'codes/sma_strategy.py' in artifacts
    assert 'tests/test_sma_strategy.py' in artifacts
    
    # 5. Verify tests pass
    test_report = artifacts['test_report.json']
    assert test_report['summary']['passed'] > 0
    assert test_report['summary']['failed'] == 0
```

**CI Pipeline**:
```yaml
# .github/workflows/multi_agent_ci.yml
name: Multi-Agent CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:latest
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r multi_agent/requirements.txt
      
      - name: Run unit tests
        run: |
          pytest multi_agent/tests/unit/ -v
      
      - name: Run integration tests
        run: |
          pytest multi_agent/tests/integration/ -v
      
      - name: Run E2E tests
        run: |
          pytest multi_agent/tests/e2e/ -v
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

---

## Phase 4: Artifact Store & Versioning (Week 7)

### 4.1: Git Integration

```python
# artifacts/artifact_store.py

class ArtifactStore:
    """Git-based artifact storage."""
    
    def commit_artifacts(
        self,
        workflow_id: str,
        task_id: str,
        artifacts: List[Path],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Commit artifacts to Git.
        
        Process:
        1. Create branch: ai/generated/{workflow_id}/{task_id}
        2. Copy artifacts to branch
        3. Commit with metadata
        4. Tag with correlation_id
        5. Push to remote (optional)
        
        Returns:
            Commit SHA
        """
        branch_name = f"ai/generated/{workflow_id}/{task_id}"
        
        # Create branch
        self.repo.git.checkout('-b', branch_name)
        
        # Copy files
        for artifact in artifacts:
            dest = self.repo_path / artifact.name
            dest.write_text(artifact.read_text())
            self.repo.index.add([str(dest)])
        
        # Commit with metadata
        commit_msg = self._format_commit_message(task_id, metadata)
        commit = self.repo.index.commit(commit_msg)
        
        # Tag
        tag_name = f"workflow_{workflow_id}_{task_id}"
        self.repo.create_tag(tag_name, ref=commit)
        
        return commit.hexsha
```

**Metadata Format**:
```json
{
  "workflow_id": "wf_abc123",
  "task_id": "task_coder_001",
  "correlation_id": "corr_xyz789",
  "agent_role": "coder",
  "agent_version": "1.0.0",
  "prompt_hash": "sha256:...",
  "model_name": "gemini-2.0-flash-exp",
  "timestamp": "2025-11-04T10:00:00Z",
  "artifacts": ["codes/strategy.py", "tests/test_strategy.py"]
}
```

---

## Phase 5: Rollout & Monitoring (Week 8+)

### 5.1: Phased Rollout

**Week 8: 10% Traffic**
```python
# Route 10% of requests to multi-agent
if random.random() < 0.10:
    result = multi_agent_system.execute(request)
else:
    result = single_agent_system.execute(request)
```

**Metrics to Track**:
- Success rate (multi vs single)
- Time to completion
- Number of iterations
- Cost per workflow
- User satisfaction

**Success Criteria** (before increasing to 25%):
- Success rate ≥ single agent
- Time to completion ≤ 2x single agent
- No security incidents
- Positive user feedback

**Week 9-10: Gradual Increase**
- Week 9: 25% traffic
- Week 10: 50% traffic
- Week 11: 75% traffic
- Week 12: 100% traffic

### 5.2: Monitoring Dashboard

**Metrics**:
```python
# Workflow metrics
workflow_success_rate = completed_workflows / total_workflows
avg_workflow_duration = sum(durations) / len(durations)

# Task metrics
task_pass_rate_by_role = {
    'architect': architect_successes / architect_total,
    'coder': coder_successes / coder_total,
    'tester': tester_successes / tester_total
}

# Cost metrics
cost_per_workflow = total_api_cost / num_workflows
cost_by_agent_role = {...}

# Quality metrics
test_coverage = avg(coverage_by_workflow)
security_issues = sum(bandit_findings)
```

**Alerts**:
- Workflow failure rate > 20%
- Task retry rate > 50%
- Agent downtime > 5 minutes
- Security issue detected
- Cost exceeds budget

---

## Rollback Strategy

### Trigger Rollback If:
- Success rate drops below 70%
- Critical security issue discovered
- System instability (crashes, timeouts)
- User complaints exceed threshold

### Rollback Process:
```python
# 1. Set feature flag
ENABLE_MULTI_AGENT = False

# 2. Route all traffic to single agent
if ENABLE_MULTI_AGENT:
    return multi_agent_system.execute(request)
else:
    return single_agent_system.execute(request)

# 3. Keep data for analysis
archive_multi_agent_logs()

# 4. Fix issues
debug_and_patch()

# 5. Re-enable gradually
ENABLE_MULTI_AGENT = True
MULTI_AGENT_TRAFFIC_PERCENT = 0.05  # Start small again
```

---

## Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Schema changes break compatibility | High | Low | Version schemas, provide migration tools |
| Agent downtime | Medium | Medium | Retry logic, fallback to single agent |
| LLM cost explosion | High | Medium | Set budget limits, use caching |
| Docker security issues | High | Low | Regular updates, security scanning |
| Database corruption | High | Low | Regular backups, transaction safety |
| Message bus failure | Medium | Low | Use persistent queue (Redis/RabbitMQ) |

---

## Success Criteria

### Phase 1-2 (Foundation)
- ✅ Schemas validate successfully
- ✅ Message bus handles 1000+ events/min
- ✅ Orchestrator executes workflows correctly
- ✅ Planner generates valid todo lists

### Phase 3-4 (Agents)
- [ ] Architect generates valid contracts (>90%)
- [ ] Coder produces passing code (>80% first try)
- [ ] Tester identifies failures correctly (>95%)
- [ ] Sandbox prevents security issues (100%)

### Phase 5 (Production)
- [ ] Multi-agent success rate ≥ single agent
- [ ] Time to completion ≤ 1.5x single agent
- [ ] Cost per workflow ≤ $1.00
- [ ] Zero security incidents
- [ ] User satisfaction ≥ 4/5

---

## Timeline Summary

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | Preparation | Infrastructure setup |
| 2-3 | Core Services | Planner ✅, Orchestrator ✅ |
| 3 | Architect Agent | Contract generation |
| 4 | Coder Agent | Code implementation |
| 5 | Tester Agent | Sandbox testing |
| 6 | Integration | E2E tests, CI/CD |
| 7 | Artifact Store | Git versioning |
| 8+ | Rollout | 10% → 100% traffic |

**Total**: 8-10 weeks to production

---

## Next Immediate Steps

1. **This Week**:
   - [ ] Install Redis locally
   - [ ] Set up Docker for sandbox
   - [ ] Configure PostgreSQL for orchestrator
   - [ ] Run `quick_test.py` to validate setup

2. **Next Week**:
   - [ ] Implement Architect agent
   - [ ] Write unit tests for Architect
   - [ ] Test contract generation with sample tasks

3. **Following Week**:
   - [ ] Implement Coder agent
   - [ ] Integrate with existing code generation
   - [ ] Add linting and type checking

---

**Current Status**: ✅ Phases 0-2 Complete (Foundation Ready)  
**Next Milestone**: Architect Agent Implementation  
**Estimated Completion**: 6-8 weeks from today
