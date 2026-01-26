"""
Context Injector for Agent Learning

Provides context from past learnings to agents during code generation
and debugging, helping them avoid repeating mistakes.
"""

from typing import Dict, List, Optional, Any
from .knowledge_base import KnowledgeBase, ErrorPattern


class ContextInjector:
    """
    Injects learning context into agent prompts.
    
    Uses knowledge base to provide relevant past learnings
    that help agents make better decisions.
    """
    
    def __init__(self, knowledge_base: KnowledgeBase):
        """
        Initialize context injector.
        
        Args:
            knowledge_base: KnowledgeBase instance to pull learnings from
        """
        self.kb = knowledge_base
    
    def get_error_context(
        self,
        error_message: str,
        error_type: Optional[str] = None
    ) -> str:
        """
        Generate context about similar errors and their fixes.
        
        Args:
            error_message: Current error message
            error_type: Optional error type
            
        Returns:
            Formatted context string to inject into prompt
        """
        similar = self.kb.search_similar_errors(error_message, error_type, limit=3)
        
        if not similar:
            return ""
        
        context_parts = [
            "\n## 💡 LEARNING FROM PAST ITERATIONS\n",
            "The system has encountered similar errors before. Here are proven solutions:\n"
        ]
        
        for i, pattern in enumerate(similar, 1):
            context_parts.append(f"\n### Similar Error #{i} (✓ Fixed {pattern.success_count}x)")
            context_parts.append(f"**Error Type:** {pattern.error_type}")
            context_parts.append(f"**Pattern:** {pattern.error_message[:200]}...")
            context_parts.append(f"\n**Successful Fix:**")
            context_parts.append(f"{pattern.fix_description}")
            
            if pattern.fix_code_snippet:
                context_parts.append(f"\n**Code Example:**")
                context_parts.append(f"```python\n{pattern.fix_code_snippet}\n```")
            
            if pattern.tags:
                context_parts.append(f"**Tags:** {', '.join(pattern.tags)}")
        
        context_parts.append("\n**IMPORTANT:** Apply these learnings to avoid repeating the same mistakes.\n")
        
        return "\n".join(context_parts)
    
    def get_general_context(self, strategy_type: Optional[str] = None) -> str:
        """
        Get general best practices context from knowledge base.
        
        Args:
            strategy_type: Optional strategy type to filter by
            
        Returns:
            Formatted context string
        """
        top_fixes = self.kb.get_top_fixes(limit=5)
        
        if not top_fixes:
            return ""
        
        context_parts = [
            "\n## 🎯 COMMON PITFALLS TO AVOID\n",
            "Based on past iterations, these are the most common issues and their fixes:\n"
        ]
        
        for i, pattern in enumerate(top_fixes, 1):
            context_parts.append(
                f"{i}. **{pattern.error_type}** (occurred {pattern.success_count}x)"
            )
            context_parts.append(f"   Fix: {pattern.fix_description}")
        
        return "\n".join(context_parts)
    
    def get_debugging_context(
        self,
        error_message: str,
        target_file: str,
        workflow_id: str
    ) -> str:
        """
        Get comprehensive debugging context for debugger agent.
        
        Args:
            error_message: Current error
            target_file: File being debugged
            workflow_id: Current workflow
            
        Returns:
            Complete debugging context
        """
        parts = []
        
        # Get error-specific context
        error_context = self.get_error_context(error_message)
        if error_context:
            parts.append(error_context)
        
        # Get stats
        stats = self.kb.get_stats()
        if stats['total_patterns'] > 0:
            parts.append(f"\n📊 **Knowledge Base Stats:**")
            parts.append(f"- Total known patterns: {stats['total_patterns']}")
            parts.append(f"- Total successful fixes: {stats['total_successes']}")
            parts.append(f"- Error types tracked: {', '.join(stats['error_types'].keys())}")
        
        return "\n".join(parts) if parts else ""
    
    def get_coder_context(
        self,
        task_description: str,
        is_fix_task: bool = False,
        error_message: Optional[str] = None
    ) -> str:
        """
        Get context for coder agent.
        
        Args:
            task_description: Task description
            is_fix_task: Whether this is a fix task
            error_message: Optional error message if fixing
            
        Returns:
            Coder-specific context
        """
        parts = []
        
        if is_fix_task and error_message:
            # Get specific error context
            error_context = self.get_error_context(error_message)
            if error_context:
                parts.append(error_context)
        else:
            # Get general best practices
            general_context = self.get_general_context()
            if general_context:
                parts.append(general_context)
        
        return "\n".join(parts) if parts else ""
    
    def format_for_prompt(
        self,
        base_prompt: str,
        context: str,
        position: str = "before"
    ) -> str:
        """
        Insert context into base prompt.
        
        Args:
            base_prompt: Original prompt
            context: Learning context to inject
            position: Where to inject ('before' or 'after')
            
        Returns:
            Enhanced prompt with context
        """
        if not context:
            return base_prompt
        
        separator = "\n" + "="*70 + "\n"
        
        if position == "before":
            return f"{context}{separator}{base_prompt}"
        else:
            return f"{base_prompt}{separator}{context}"
