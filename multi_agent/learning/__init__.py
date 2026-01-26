"""
Learning and Knowledge Management System

This module provides learning mechanisms for the multi-agent system:
- Error-Fix pattern storage and retrieval
- Context injection for agents
- Performance analytics
"""

from .knowledge_base import KnowledgeBase
from .context_injector import ContextInjector

__all__ = ['KnowledgeBase', 'ContextInjector']
