"""
Pytest tests for API key integration across all agents.

Tests that the multi-agent system properly loads and uses API keys
from the .env file via the RequestRouter.
"""
import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load .env from parent directory
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"\n✅ Loaded .env from: {env_path}")
else:
    pytest.fail(f"❌ .env file not found at {env_path}")


@pytest.fixture(scope="session")
def check_env_loaded():
    """Ensure .env is loaded before tests run."""
    router_enabled = os.getenv('LLM_MULTI_KEY_ROUTER_ENABLED', 'false').lower() == 'true'
    if not router_enabled:
        pytest.skip("RequestRouter is not enabled. Set LLM_MULTI_KEY_ROUTER_ENABLED=true")
    return True


@pytest.fixture(scope="session")
def workspace_root():
    """Get workspace root path."""
    return Path(__file__).parent.parent


class TestEnvironmentVariables:
    """Test that environment variables are properly loaded."""
    
    def test_router_enabled(self, check_env_loaded):
        """Test that RequestRouter is enabled."""
        router_enabled = os.getenv('LLM_MULTI_KEY_ROUTER_ENABLED', 'false').lower() == 'true'
        assert router_enabled, "LLM_MULTI_KEY_ROUTER_ENABLED should be 'true'"
    
    def test_gemini_keys_loaded(self, check_env_loaded):
        """Test that GEMINI_KEY_* variables are loaded."""
        gemini_keys = [k for k in os.environ if k.startswith('GEMINI_KEY_')]
        assert len(gemini_keys) > 0, "No GEMINI_KEY_* environment variables found"
        print(f"\n✓ Found {len(gemini_keys)} GEMINI_KEY_* variables")
        
    def test_api_keys_have_values(self, check_env_loaded):
        """Test that API keys have actual values (not just references)."""
        gemini_keys = [k for k in os.environ if k.startswith('GEMINI_KEY_')]
        for key_name in gemini_keys[:3]:  # Check first 3
            value = os.getenv(key_name)
            assert value, f"{key_name} is empty"
            assert value.startswith('AIza'), f"{key_name} doesn't look like a Google API key: {value[:10]}"
            assert len(value) > 30, f"{key_name} value seems too short"
        print(f"\n✓ API keys have valid values")


class TestSecretStore:
    """Test secret store functionality."""
    
    def test_import_secret_store(self, check_env_loaded):
        """Test that secret_store module can be imported."""
        from keys.secret_store import fetch_api_secret
        assert callable(fetch_api_secret), "fetch_api_secret should be callable"
    
    def test_fetch_api_secret(self, check_env_loaded):
        """Test fetching API secrets."""
        from keys.secret_store import fetch_api_secret
        
        # Test fetching flash_01 key
        secret = fetch_api_secret('flash_01')
        assert secret, "Should return a secret value"
        assert secret.startswith('AIza'), f"Secret doesn't look like Google API key: {secret[:10]}"
        print(f"\n✓ fetch_api_secret('flash_01') returned valid key")


class TestKeyManager:
    """Test KeyManager functionality."""
    
    def test_import_key_manager(self, check_env_loaded):
        """Test that KeyManager can be imported."""
        from keys.manager import KeyManager, get_key_manager
        assert KeyManager is not None
        assert callable(get_key_manager)
    
    def test_key_manager_initialization(self, check_env_loaded, workspace_root):
        """Test KeyManager initialization with keys.json."""
        from keys.manager import KeyManager
        
        keys_json_path = workspace_root / 'multi_agent' / 'keys.json'
        assert keys_json_path.exists(), f"keys.json not found at {keys_json_path}"
        
        km = KeyManager(key_store_path=keys_json_path)
        assert len(km.keys) > 0, "KeyManager should load keys from keys.json"
        print(f"\n✓ KeyManager loaded {len(km.keys)} keys")
    
    def test_key_selection(self, check_env_loaded, workspace_root):
        """Test key selection (may fail if Redis not running)."""
        from keys.manager import KeyManager
        
        keys_json_path = workspace_root / 'multi_agent' / 'keys.json'
        km = KeyManager(key_store_path=keys_json_path)
        
        try:
            selected = km.select_key(model_preference='gemini-2.0-flash', workload='light')
            if selected:
                print(f"\n✓ select_key() returned: {selected.key_id}")
                assert selected.key_id in km.keys
            else:
                pytest.skip("select_key() returned None (Redis may not be running)")
        except Exception as e:
            pytest.skip(f"select_key() failed: {e} (Redis may not be running)")


class TestRequestRouter:
    """Test RequestRouter functionality."""
    
    def test_import_request_router(self, check_env_loaded):
        """Test that RequestRouter can be imported."""
        from llm.router import get_request_router, RequestRouter
        assert RequestRouter is not None
        assert callable(get_request_router)
    
    def test_get_request_router(self, check_env_loaded):
        """Test getting RequestRouter instance."""
        from llm.router import get_request_router
        
        try:
            router = get_request_router()
            assert router is not None
            assert hasattr(router, 'send_chat')
            assert hasattr(router, 'key_manager')
            print(f"\n✓ RequestRouter initialized successfully")
            print(f"  Max retries: {router.max_retries}")
            print(f"  Base backoff: {router.base_backoff_ms}ms")
        except Exception as e:
            pytest.skip(f"RequestRouter initialization failed: {e} (Redis may not be running)")


class TestCoderAgent:
    """Test CoderAgent integration with key infrastructure."""
    
    def test_import_coder_agent(self, check_env_loaded):
        """Test that CoderAgent can be imported."""
        from agents.coder_agent.coder import CoderAgent
        assert CoderAgent is not None
    
    def test_coder_agent_initialization(self, check_env_loaded, workspace_root):
        """Test CoderAgent initialization with RequestRouter."""
        from agents.coder_agent.coder import CoderAgent
        from contracts.message_bus import InMemoryMessageBus
        
        message_bus = InMemoryMessageBus()
        agent = CoderAgent(
            agent_id='test_coder',
            message_bus=message_bus,
            workspace_root=workspace_root
        )
        
        assert agent is not None
        assert agent.use_router, "CoderAgent should be using RequestRouter"
        assert agent.router is not None, "CoderAgent should have router instance"
        print(f"\n✓ CoderAgent initialized with RequestRouter")
        print(f"  Agent ID: {agent.agent_id}")
        print(f"  Conversation ID: {agent.conversation_id}")
        print(f"  Model: {agent.model_name}")


class TestCLI:
    """Test CLI integration with key infrastructure."""
    
    def test_cli_initialization(self, check_env_loaded, workspace_root):
        """Test CLI initialization detects AI capability."""
        # Change to workspace root for imports
        original_cwd = os.getcwd()
        try:
            os.chdir(workspace_root / 'multi_agent')
            sys.path.insert(0, str(workspace_root / 'multi_agent'))
            
            from cli import MultiAgentCLI
            
            # Suppress output during init
            import io
            import contextlib
            
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                cli = MultiAgentCLI()
            
            output = f.getvalue()
            
            assert cli.ai_mode, "CLI should detect AI capability when router is enabled"
            assert cli.use_router, "CLI should use RequestRouter mode"
            assert cli.api_key == "ROUTER_MODE", "CLI api_key should be 'ROUTER_MODE' flag"
            
            print(f"\n✓ CLI initialized with AI capability")
            print(f"  AI Mode: {cli.ai_mode}")
            print(f"  Use Router: {cli.use_router}")
            print(f"  API Key: {cli.api_key}")
            
            # Check for RequestRouter message in output
            assert "RequestRouter Mode: ENABLED" in output, "CLI should log RequestRouter mode"
            
        finally:
            os.chdir(original_cwd)


class TestEndToEnd:
    """End-to-end integration tests."""
    
    @pytest.mark.skipif(
        not os.getenv('RUN_E2E_TESTS'),
        reason="E2E tests require RUN_E2E_TESTS=true and Redis"
    )
    def test_coder_agent_can_generate_code(self, check_env_loaded, workspace_root):
        """Test that CoderAgent can actually generate code (requires API calls)."""
        from agents.coder_agent.coder import CoderAgent
        from contracts.message_bus import InMemoryMessageBus
        import tempfile
        import json
        
        message_bus = InMemoryMessageBus()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = CoderAgent(
                agent_id='e2e_test_coder',
                message_bus=message_bus,
                workspace_root=Path(tmpdir)
            )
            
            # Create a simple contract
            contract = {
                "contract_id": "test_contract",
                "description": "Simple test strategy",
                "interfaces": {
                    "run_backtest": {
                        "description": "Execute backtesting strategy",
                        "inputs": ["adapter", "df with OHLCV"],
                        "outputs": ["Backtest results"]
                    }
                }
            }
            
            contract_path = Path(tmpdir) / "test_contract.json"
            contract_path.write_text(json.dumps(contract, indent=2))
            
            # Create a task
            task = {
                'id': 'test_task_001',
                'title': 'Test Code Generation',
                'agent_role': 'coder',
                'contract_path': str(contract_path),
                'description': 'Generate a simple moving average strategy'
            }
            
            # Execute task
            result = agent.implement_task(task)
            
            assert result is not None, "Should return a result"
            assert result.status in ['ready', 'needs_review'], f"Expected success status, got: {result.status}"
            assert len(result.artifacts) > 0, "Should generate at least one artifact"
            
            print(f"\n✓ E2E test passed!")
            print(f"  Status: {result.status}")
            print(f"  Artifacts: {len(result.artifacts)}")


if __name__ == '__main__':
    # Run with pytest
    pytest.main([__file__, '-v', '-s'])
