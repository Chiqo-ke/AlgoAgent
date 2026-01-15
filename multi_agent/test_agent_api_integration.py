"""
Integration test for agent API key usage through RequestRouter
Tests that all agents can properly use API keys from the .env file
"""
import sys
import os
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
print(f"✅ Loaded .env from {env_path}")


class TestAgentAPIIntegration:
    """Test API key integration across all agents"""
    
    def test_environment_setup(self):
        """Verify .env file is loaded correctly"""
        assert os.getenv('LLM_MULTI_KEY_ROUTER_ENABLED') == 'true', "Router should be enabled"
        
        # Count GEMINI_KEY_* variables
        gemini_keys = [k for k in os.environ if k.startswith('GEMINI_KEY_')]
        print(f"✅ Found {len(gemini_keys)} GEMINI_KEY_* variables")
        assert len(gemini_keys) > 0, "Should have at least one GEMINI_KEY_* variable"
        
        # Verify keys have actual values (not just key names)
        for key_name in gemini_keys:
            key_value = os.getenv(key_name)
            assert key_value.startswith('AIza'), f"{key_name} should start with 'AIza'"
            print(f"  ✓ {key_name}: {key_value[:10]}...")
    
    def test_request_router_initialization(self):
        """Test RequestRouter can initialize and load keys"""
        from llm.router import get_request_router
        
        router = get_request_router()
        assert router is not None, "Router should initialize"
        print(f"✅ RequestRouter initialized")
        
        # Check router has keys loaded
        key_manager = router.key_manager
        assert len(key_manager.keys) > 0, "KeyManager should have keys"
        print(f"✅ KeyManager has {len(key_manager.keys)} keys loaded")
    
    def test_coder_agent_initialization(self):
        """Test CoderAgent can initialize with RequestRouter"""
        from agents.coder_agent.coder import CoderAgent
        from message_bus import MessageBus
        
        message_bus = MessageBus()
        workspace_root = Path(__file__).parent
        
        agent = CoderAgent(
            agent_id="test_coder",
            message_bus=message_bus,
            workspace_root=workspace_root
        )
        
        assert agent is not None, "CoderAgent should initialize"
        assert agent.use_router is True, "CoderAgent should use router"
        print(f"✅ CoderAgent initialized with router mode")
    
    def test_coder_agent_can_access_llm(self):
        """Test CoderAgent can make LLM calls"""
        from agents.coder_agent.coder import CoderAgent
        from message_bus import MessageBus
        
        message_bus = MessageBus()
        workspace_root = Path(__file__).parent
        
        agent = CoderAgent(
            agent_id="test_coder",
            message_bus=message_bus,
            workspace_root=workspace_root
        )
        
        # Test a simple LLM call
        try:
            response = agent._call_gemini_with_router(
                prompt="Say 'Hello' in one word",
                temperature=0.1,
                max_output_tokens=10
            )
            assert response is not None, "Should get response from LLM"
            assert len(response) > 0, "Response should not be empty"
            print(f"✅ CoderAgent successfully called LLM: '{response[:50]}...'")
        except Exception as e:
            pytest.fail(f"LLM call failed: {e}")
    
    def test_cli_detects_ai_mode(self):
        """Test CLI properly detects AI mode when router is enabled"""
        # Import CLI to trigger initialization
        from cli import MultiAgentCLI
        
        cli = MultiAgentCLI()
        
        # After fix, CLI should detect AI capability through router
        assert cli.use_router is True, "CLI should use router mode"
        print(f"✅ CLI detected router mode")
        print(f"   AI Mode: {cli.has_ai_capability()}")
        print(f"   Use Router: {cli.use_router}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
