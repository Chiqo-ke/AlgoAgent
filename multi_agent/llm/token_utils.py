"""
Token estimation utilities for TPM (tokens per minute) reservations.

Provides conservative estimates for both prompt and completion tokens.
"""
import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def estimate_tokens(
    messages: List[Dict[str, str]],
    expected_completion_tokens: int = 512
) -> int:
    """
    Estimate total tokens for a chat completion request.
    
    Uses conservative heuristic:
    - Input tokens ≈ characters / 4
    - Add expected completion tokens
    - Add overhead for message formatting
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        expected_completion_tokens: Expected tokens in response
        
    Returns:
        Estimated total tokens (input + output)
    """
    # Calculate input tokens
    total_chars = 0
    for msg in messages:
        content = msg.get('content', '')
        total_chars += len(content)
        # Add overhead for role and formatting
        total_chars += 20
    
    # Conservative estimate: 4 chars per token
    # (actual is ~4 for English, less for other languages)
    input_tokens = (total_chars // 4) + 1
    
    # Total estimate
    total_tokens = input_tokens + expected_completion_tokens
    
    logger.debug(
        f"Token estimate: {input_tokens} input + {expected_completion_tokens} "
        f"completion = {total_tokens} total"
    )
    
    return total_tokens


def estimate_tokens_from_text(text: str) -> int:
    """
    Estimate tokens from a single text string.
    
    Args:
        text: Input text
        
    Returns:
        Estimated tokens
    """
    # Conservative estimate: 4 chars per token
    return (len(text) // 4) + 1


def count_actual_tokens(text: str, model: str = "gemini") -> int:
    """
    Count actual tokens using provider tokenizer (if available).
    
    Falls back to estimation if tokenizer not available.
    
    Args:
        text: Input text
        model: Model name to use correct tokenizer
        
    Returns:
        Token count
    """
    # Try to use actual tokenizer
    if model.startswith("gemini"):
        return _count_tokens_gemini(text)
    elif model.startswith("gpt"):
        return _count_tokens_openai(text, model)
    else:
        # Fallback to estimation
        return estimate_tokens_from_text(text)


def _count_tokens_gemini(text: str) -> int:
    """Count tokens using Gemini tokenizer."""
    try:
        import google.generativeai as genai
        
        # Use model to count tokens
        model = genai.GenerativeModel('gemini-pro')
        result = model.count_tokens(text)
        return result.total_tokens
        
    except Exception as e:
        logger.debug(f"Gemini tokenizer unavailable: {e}")
        return estimate_tokens_from_text(text)


def _count_tokens_openai(text: str, model: str) -> int:
    """Count tokens using OpenAI tiktoken."""
    try:
        import tiktoken
        
        # Get encoding for model
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")  # Default for GPT-4
        
        tokens = encoding.encode(text)
        return len(tokens)
        
    except Exception as e:
        logger.debug(f"tiktoken unavailable: {e}")
        return estimate_tokens_from_text(text)


def estimate_completion_tokens(
    task_type: str = "chat",
    max_output_length: int = 2048
) -> int:
    """
    Estimate expected completion tokens based on task type.
    
    Args:
        task_type: Type of task ('chat', 'code', 'long_form', 'analysis')
        max_output_length: Maximum expected output length
        
    Returns:
        Estimated completion tokens
    """
    # Default estimates by task type
    estimates = {
        'chat': 256,
        'code': 1024,
        'long_form': 2048,
        'analysis': 512,
        'summary': 256,
        'debug': 1024
    }
    
    base_estimate = estimates.get(task_type, 512)
    
    # Don't exceed max_output_length
    return min(base_estimate, max_output_length)


def calculate_cost_estimate(
    input_tokens: int,
    output_tokens: int,
    model: str
) -> float:
    """
    Estimate cost for a request.
    
    Args:
        input_tokens: Input token count
        output_tokens: Output token count
        model: Model name
        
    Returns:
        Estimated cost in USD
    """
    # Pricing per 1M tokens (as of Nov 2024)
    pricing = {
        'gemini-2.5-flash': {'input': 0.075, 'output': 0.30},
        'gemini-2.5-pro': {'input': 1.25, 'output': 5.00},
        'gpt-4o': {'input': 2.50, 'output': 10.00},
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50}
    }
    
    # Find matching pricing
    model_pricing = None
    for key, value in pricing.items():
        if model.startswith(key):
            model_pricing = value
            break
    
    if not model_pricing:
        logger.warning(f"Unknown model pricing for {model}, using default")
        model_pricing = {'input': 1.0, 'output': 3.0}
    
    # Calculate cost
    input_cost = (input_tokens / 1_000_000) * model_pricing['input']
    output_cost = (output_tokens / 1_000_000) * model_pricing['output']
    
    return input_cost + output_cost


class TokenBudget:
    """Helper class for tracking token usage within a budget."""
    
    def __init__(self, max_tokens: int):
        """
        Initialize token budget tracker.
        
        Args:
            max_tokens: Maximum tokens allowed
        """
        self.max_tokens = max_tokens
        self.used_tokens = 0
    
    def can_afford(self, tokens: int) -> bool:
        """Check if budget can afford tokens."""
        return self.used_tokens + tokens <= self.max_tokens
    
    def consume(self, tokens: int) -> bool:
        """
        Consume tokens from budget.
        
        Returns:
            True if consumed, False if would exceed budget
        """
        if self.can_afford(tokens):
            self.used_tokens += tokens
            return True
        return False
    
    def remaining(self) -> int:
        """Get remaining token budget."""
        return max(0, self.max_tokens - self.used_tokens)
    
    def usage_percent(self) -> float:
        """Get budget usage as percentage."""
        return (self.used_tokens / self.max_tokens) * 100 if self.max_tokens > 0 else 100.0
