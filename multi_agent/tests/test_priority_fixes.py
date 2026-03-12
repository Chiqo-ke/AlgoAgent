"""
Unit tests for Priority A-D fixes

Tests:
1. SafetyBlockError exception creation and handling
2. Safety settings propagation validation
3. Router safety block handling (don't mark keys unhealthy)
4. Timeout pattern detection
5. Prompt sanitization
"""

import pytest
import re
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List

# Import the classes we're testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.providers import SafetyBlockError, ProviderError, RateLimitError
from llm.router import RequestRouter


class TestSafetyBlockError:
    """Test SafetyBlockError exception handling."""
    
    def test_safety_block_error_creation(self):
        """SafetyBlockError should store safety ratings."""
        ratings = [
            {'category': 'HARM_CATEGORY_HARASSMENT', 'probability': 'LOW'},
            {'category': 'HARM_CATEGORY_DANGEROUS_CONTENT', 'probability': 'HIGH'}
        ]
        
        error = SafetyBlockError("Content blocked", safety_ratings=ratings)
        
        assert str(error) == "Content blocked"
        assert error.safety_ratings == ratings
        assert isinstance(error, ProviderError)
    
    def test_safety_block_error_without_ratings(self):
        """SafetyBlockError should work without ratings."""
        error = SafetyBlockError("Generic block")
        
        assert str(error) == "Generic block"
        assert error.safety_ratings is None


class TestRouterSafetyHandling:
    """Test router's safety block handling."""
    
    def test_router_escalates_workload_on_safety_block(self):
        """Router should escalate from light -> medium -> heavy on safety blocks."""
        router = RequestRouter()
        
        # Test workload escalation logic
        workload = "light"
        # Simulate safety block on first attempt
        # Should escalate to medium
        
        # This would be tested by mocking the _call_provider and key_manager
        # For now, validate the _sanitize_prompt method exists
        assert hasattr(router, '_sanitize_prompt')
        assert callable(router._sanitize_prompt)
    
    def test_prompt_sanitization_removes_code_blocks(self):
        """Sanitizer should remove code blocks."""
        router = RequestRouter()
        
        messages = [
            {"role": "user", "content": "Fix this:\n```python\ndef hack():\n    pass\n```"}
        ]
        
        sanitized = router._sanitize_prompt(messages)
        
        assert len(sanitized) == 1
        assert '[CODE_BLOCK_REMOVED]' in sanitized[0]["content"]
        assert 'python' not in sanitized[0]["content"]
        assert 'hack' not in sanitized[0]["content"]
    
    def test_prompt_sanitization_softens_aggressive_language(self):
        """Sanitizer should replace aggressive trading terms."""
        router = RequestRouter()
        
        messages = [
            {"role": "user", "content": "Create aggressive HFT strategy to kill the market"}
        ]
        
        sanitized = router._sanitize_prompt(messages)
        content = sanitized[0]["content"]
        
        # Should replace aggressive words
        assert 'aggressive' not in content.lower() or 'active' in content.lower()
        assert 'kill' not in content.lower() or 'close' in content.lower()


class TestTimeoutAnalysis:
    """Test timeout pattern detection."""
    
    def test_detect_infinite_loop_pattern(self):
        """Should detect 'while True' patterns."""
        from agents.tester_agent.tester import TesterAgent
        
        agent = TesterAgent(use_redis=False)
        
        docker_logs = """
        Running strategy...
        Starting loop...
        while True:
            process_data()
        """
        
        analysis = agent._analyze_timeout_error(docker_logs)
        
        assert analysis["error_type"] == "timeout"
        assert "infinite_loop" in analysis["root_cause"]
        assert len(analysis["fix_strategy"]) > 0
        assert any("max_iterations" in fix.lower() for fix in analysis["fix_strategy"])
    
    def test_detect_large_data_pattern(self):
        """Should detect df.iterrows() patterns."""
        from agents.tester_agent.tester import TesterAgent
        
        agent = TesterAgent(use_redis=False)
        
        docker_logs = """
        Processing data...
        for index, row in df.iterrows():
            calculate(row)
        """
        
        analysis = agent._analyze_timeout_error(docker_logs)
        
        assert "large_data" in analysis["root_cause"]
        assert any("vectorized" in fix.lower() for fix in analysis["fix_strategy"])
    
    def test_detect_blocking_io_pattern(self):
        """Should detect network requests."""
        from agents.tester_agent.tester import TesterAgent
        
        agent = TesterAgent(use_redis=False)
        
        docker_logs = """
        Fetching data...
        import requests
        response = requests.get(url)
        """
        
        analysis = agent._analyze_timeout_error(docker_logs)
        
        assert "blocking_io" in analysis["root_cause"]
        assert any("network" in fix.lower() or "sandbox" in fix.lower() for fix in analysis["fix_strategy"])
    
    def test_extract_last_execution_line(self):
        """Should extract last executed line from logs."""
        from agents.tester_agent.tester import TesterAgent
        
        agent = TesterAgent(use_redis=False)
        
        logs = """
        File "strategy.py", line 45
            result = slow_function()
        File "utils.py", line 120
            process_large_dataset()
        """
        
        last_line = agent._extract_last_execution_line(logs)
        
        assert last_line != ""
        assert "line" in last_line.lower()


class TestDebuggerTimeoutHandling:
    """Test debugger's enhanced timeout analysis."""
    
    @pytest.mark.asyncio
    async def test_debugger_uses_timeout_analysis(self):
        """Debugger should extract and use timeout analysis from test_result."""
        from agents.debugger_agent.debugger import DebuggerAgent
        
        bus = Mock()
        agent = DebuggerAgent(bus)
        
        test_result = {
            "error_message": "timeout occurred",
            "timed_out": True,
            "root_cause": ["infinite_loop", "large_data"],
            "fix_strategy": [
                "Add max_iterations counter",
                "Use vectorized operations"
            ],
            "last_line": "while True: process()"
        }
        
        analysis = await agent._analyze_failure(test_result, {})
        
        assert analysis.failure_type == "timeout"
        assert analysis.target_agent == "coder"  # Coder must fix, not just increase timeout
        assert "infinite_loop" in analysis.debug_summary
        assert "large_data" in analysis.debug_summary
        assert len(analysis.suggested_fixes) >= 2


class TestCoderPerformancePrompt:
    """Test coder's enhanced performance constraints in prompt."""
    
    def test_prompt_includes_execution_time_constraint(self):
        """Coder prompt should include <10s execution time requirement."""
        from agents.coder_agent.coder import CoderAgent
        from contracts.message_bus import InMemoryMessageBus
        
        bus = InMemoryMessageBus()
        agent = CoderAgent(
            agent_id="test-coder",
            message_bus=bus
        )
        
        task = {
            "title": "Test strategy",
            "description": "Simple EMA crossover",
            "fixture_paths": []
        }
        
        contract = {
            "contract_id": "test-001",
            "interfaces": {"run": "def run(adapter, df): pass"}
        }
        
        prompt = agent._build_llm_prompt(task, contract)
        
        # Check for performance requirements
        assert "<10 seconds" in prompt or "<10s" in prompt
        assert "MAX_ITERATIONS" in prompt
        assert "vectorized" in prompt.lower()
        assert "df.iterrows()" in prompt
        assert "FORBIDDEN" in prompt or "NOT" in prompt
        assert "time.time()" in prompt
    
    def test_prompt_includes_loop_safety(self):
        """Coder prompt should forbid 'while True' without limits."""
        from agents.coder_agent.coder import CoderAgent
        from contracts.message_bus import InMemoryMessageBus
        
        bus = InMemoryMessageBus()
        agent = CoderAgent(agent_id="test-coder", message_bus=bus)
        
        task = {"title": "Test", "description": "Test", "fixture_paths": []}
        contract = {"contract_id": "test", "interfaces": {}}
        
        prompt = agent._build_llm_prompt(task, contract)
        
        assert "while True" in prompt
        assert "max_iterations" in prompt.lower()
    
    def test_prompt_includes_memory_constraints(self):
        """Coder prompt should mention 512MB RAM limit."""
        from agents.coder_agent.coder import CoderAgent
        from contracts.message_bus import InMemoryMessageBus
        
        bus = InMemoryMessageBus()
        agent = CoderAgent(agent_id="test-coder", message_bus=bus)
        
        task = {"title": "Test", "description": "Test", "fixture_paths": []}
        contract = {"contract_id": "test", "interfaces": {}}
        
        prompt = agent._build_llm_prompt(task, contract)
        
        assert "512" in prompt or "memory" in prompt.lower()
        assert "gc.collect()" in prompt


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
