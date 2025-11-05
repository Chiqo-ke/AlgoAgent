"""
Multi-Agent System - Agent Implementations

This package contains implementations of specialized agents:

- DebuggerAgent: Analyzes failures and creates branch todos
- ArchitectAgent: Designs contracts and test skeletons
- CoderAgent: Implements code following contracts
- TesterAgent: Executes tests in sandbox
- OptimizerAgent: Performance improvements (future)
"""

from .debugger_agent.debugger import DebuggerAgent

__all__ = ['DebuggerAgent']
