"""
GitHub Copilot Strategy Generator for SimBroker
================================================

Integrates GitHub Copilot AI to generate trading strategies that use the SimBroker API.
Replaces Gemini with direct HTTP requests to GitHub Copilot API.

Features:
- Generate strategy code from natural language descriptions using GitHub Copilot
- Ensures generated code uses stable SimBroker API
- Validates generated strategies
- Single account authentication (no key rotation needed)
- Direct HTTP API integration

Last updated: 2026-01-20
Version: 2.0.0
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "Strategy"))

# Django integration for template access
try:
    import django
    if not django.apps.apps.ready:
        django.setup()
    from strategy_api.models import StrategyTemplate, CopilotAuth
    DJANGO_AVAILABLE = True
except (ImportError, RuntimeError):
    DJANGO_AVAILABLE = False
    StrategyTemplate = None
    CopilotAuth = None
    logger.warning("Django not available - template fallback and auth disabled")

from dotenv import load_dotenv

# Import Copilot auth manager
try:
    import sys
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    from algoagent_api.copilot_auth import get_auth_manager, CopilotAuthError
    COPILOT_AUTH_AVAILABLE = True
except ImportError as e:
    COPILOT_AUTH_AVAILABLE = False
    logger.warning(f"Copilot auth not available: {e}")

# Import bot executor module
try:
    from bot_executor import BotExecutor, get_bot_executor
    BOT_EXECUTOR_AVAILABLE = True
except ImportError:
    try:
        import sys
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        from bot_executor import BotExecutor, get_bot_executor
        BOT_EXECUTOR_AVAILABLE = True
    except ImportError:
        BOT_EXECUTOR_AVAILABLE = False
        logger.warning("Bot executor not available")

# Import indicator registry
try:
    from indicator_registry import format_registry_for_prompt
    INDICATOR_REGISTRY_AVAILABLE = True
except ImportError:
    INDICATOR_REGISTRY_AVAILABLE = False
    def format_registry_for_prompt():
        return ""

# Import bot error fixer
try:
    from bot_error_fixer import BotErrorFixer
    BOT_ERROR_FIXER_AVAILABLE = True
except ImportError:
    BOT_ERROR_FIXER_AVAILABLE = False
    logger.warning("Bot error fixer not available")


class CopilotStrategyGenerator:
    """
    Generates SimBroker-compatible trading strategies using GitHub Copilot AI
    
    Uses direct HTTP requests to GitHub Copilot API with OAuth authentication.
    No key rotation needed - uses single GitHub Copilot account.
    """
    
    # GitHub Copilot API endpoint
    COPILOT_API_URL = "https://api.githubcopilot.com/chat/completions"
    
    def __init__(
        self,
        model_name: str = 'claude-sonnet-4.5',
        use_template_fallback: bool = True
    ):
        """
        Initialize Copilot Strategy Generator
        
        Args:
            model_name: Copilot model name (claude-sonnet-4.5, gpt-5.2-codex, gpt-5.1-codex, claude-opus-4.5, etc.)
            use_template_fallback: If True, fallback to database templates when API unavailable
        """
        load_dotenv()
        
        self.model_name = model_name
        self.use_template_fallback = use_template_fallback
        self.auth_manager = get_auth_manager() if COPILOT_AUTH_AVAILABLE else None
        
        logger.info(f"CopilotStrategyGenerator initialized (Model: {self.model_name})")
        
        if self.use_template_fallback and DJANGO_AVAILABLE:
            logger.info("Template fallback enabled - will use database templates if API fails")
        elif self.use_template_fallback and not DJANGO_AVAILABLE:
            logger.warning("Template fallback requested but Django unavailable")
        
        self.use_backtesting_py = False
        self.system_prompt = self._load_system_prompt(use_backtesting_py=self.use_backtesting_py)
    
    def _load_system_prompt(self, use_backtesting_py: bool = True) -> str:
        """
        Load the system prompt for strategy generation
        
        Args:
            use_backtesting_py: If True, use backtesting.py framework (default)
                              If False, use legacy SimBroker framework
        """
        if use_backtesting_py:
            prompt_file = Path(__file__).parent / "SYSTEM_PROMPT_BACKTESTING_PY.md"
        else:
            prompt_file = Path(__file__).parent / "SYSTEM_PROMPT.md"
        
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                base_prompt = f.read()
        else:
            # SYSTEM_PROMPT.md is required — no stale fallback
            raise FileNotFoundError(
                f"System prompt file not found: {prompt_file}\n"
                "This file is required for strategy generation. "
                "Check that Backtest/SYSTEM_PROMPT.md exists in the monolithic_agent directory."
            )
        
        # Add indicator registry if available
        if INDICATOR_REGISTRY_AVAILABLE:
            indicator_docs = format_registry_for_prompt()
            if indicator_docs:
                base_prompt += "\n\n## Available Indicators\n\n" + indicator_docs
        
        return base_prompt
    
    def _get_access_token(self) -> str:
        """
        Get valid GitHub Copilot access token
        
        Returns:
            Valid access token
            
        Raises:
            CopilotAuthError: If no valid token available
        """
        if not DJANGO_AVAILABLE:
            raise CopilotAuthError("Django not available - cannot retrieve token from database")
        
        # Get stored token from database
        token_data = CopilotAuth.get_latest_token()
        
        # Get valid token (will refresh if needed)
        if self.auth_manager:
            try:
                access_token = self.auth_manager.get_valid_token(token_data)
                return access_token
            except CopilotAuthError:
                logger.error("No valid Copilot token available. Please authenticate.")
                raise
        else:
            raise CopilotAuthError("Copilot auth manager not available")
    
    def _call_copilot_api(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8000
    ) -> str:
        """
        Make HTTP request to GitHub Copilot API
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (defaults to self.system_prompt)
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text from Copilot
            
        Raises:
            CopilotAuthError: If authentication fails
            requests.RequestException: If API call fails
        """
        # Get valid access token
        access_token = self._get_access_token()
        
        # Prepare messages
        messages = []
        
        if system_prompt or self.system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt or self.system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "AlgoAgent/2.0",
            "X-Initiator": "user",
            "Openai-Intent": "conversation-edits"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        logger.info(f"Calling Copilot API with model: {self.model_name}")
        
        # DEBUG: Log the full prompt and system prompt
        logger.info("="*80)
        logger.info("[DEBUG] COPILOT API REQUEST")
        logger.info("="*80)
        logger.info(f"System Prompt Length: {len(system_prompt or self.system_prompt)} chars")
        logger.info(f"System Prompt Preview: {(system_prompt or self.system_prompt)[:200]}...")
        logger.info("-"*80)
        logger.info(f"User Prompt Length: {len(prompt)} chars")
        logger.info(f"User Prompt:\n{prompt[:500]}...") if len(prompt) > 500 else logger.info(f"User Prompt:\n{prompt}")
        logger.info("="*80)
        
        try:
            response = requests.post(
                self.COPILOT_API_URL,
                headers=headers,
                json=payload,
                timeout=120  # Increased timeout for complex code generation
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract generated text
            if "choices" in data and len(data["choices"]) > 0:
                generated_text = data["choices"][0]["message"]["content"]
                logger.info(f"✓ Copilot API call successful ({len(generated_text)} chars)")
                
                # DEBUG: Log raw response preview
                logger.info("="*80)
                logger.info("[DEBUG] COPILOT API RESPONSE")
                logger.info("="*80)
                logger.info(f"Response Length: {len(generated_text)} chars")
                logger.info(f"First 800 chars:\n{generated_text[:800]}")
                logger.info(f"Last 400 chars:\n{generated_text[-400:]}")
                logger.info("="*80)
                
                return generated_text
            else:
                raise ValueError("Invalid response format from Copilot API")
                
        except requests.exceptions.HTTPError as e:
            response_text = ""
            if e.response is not None:
                try:
                    response_text = (e.response.text or "")[:1000]
                except Exception:
                    response_text = ""
            if e.response.status_code == 401:
                # Token expired or invalid
                logger.error("Copilot authentication failed - token may be expired")
                raise CopilotAuthError("Authentication failed. Please re-authenticate.")
            elif e.response.status_code == 429:
                # Rate limit
                logger.error("Copilot API rate limit exceeded")
                raise CopilotAuthError("Rate limit exceeded. Please try again later.")
            elif e.response.status_code == 400 and "Personal Access Tokens are not supported" in response_text:
                logger.error(f"Copilot API rejected PAT token: {response_text}")
                raise CopilotAuthError(
                    "PAT tokens are not supported by api.githubcopilot.com/chat/completions. "
                    "Use OAuth device auth via `python manage.py copilot_auth` and remove "
                    "GITHUB_COPILOT_PAT/GH_TOKEN from this service environment."
                )
            else:
                if response_text:
                    logger.error(f"Copilot API error: {e} | body: {response_text}")
                else:
                    logger.error(f"Copilot API error: {e}")
                raise
        except requests.RequestException as e:
            logger.error(f"Failed to call Copilot API: {e}")
            raise
    
    def generate_chat_response(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Generate a conversational response using GitHub Copilot for chat interactions
        
        Args:
            prompt: User's message or question  
            temperature: Response creativity (0.0-1.0), default 0.7 for chat
            
        Returns:
            AI response as string
            
        Raises:
            CopilotAuthError: If authentication fails
            requests.RequestException: If API request fails
        """
        try:
            # Get access token
            token = self._get_access_token()
            
            # Prepare chat request
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Editor-Version": "vscode/1.95.0",
                "Editor-Plugin-Version": "copilot-chat/0.22.0",
                "User-Agent": "GitHubCopilotChat/0.22.0"
            }
            
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert trading strategy advisor. Help users develop and refine their trading strategies by asking clarifying questions, suggesting approaches, and explaining concepts."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "model": self.model_name,
                "temperature": temperature,
                "max_tokens": 2048,
                "stream": False
            }
            
            # Call API
            response = requests.post(
                self.COPILOT_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                chat_response = result['choices'][0]['message']['content']
                logger.info(f"Chat response generated ({len(chat_response)} chars)")
                return chat_response
            else:
                error_msg = f"Copilot API returned status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise CopilotAuthError(error_msg)
                
        except CopilotAuthError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate chat response: {e}")
            raise CopilotAuthError(f"Chat generation failed: {str(e)}")
    
    def generate_strategy_code(self, description: str) -> str:
        """
        Generate strategy code from description using GitHub Copilot
        
        Args:
            description: Natural language strategy description
            
        Returns:
            Generated Python strategy code
        """
        # Enhance prompt with context
        enhanced_prompt = f"""
=========================================================
USER STRATEGY SPECIFICATION — IMPLEMENT THIS EXACTLY
=========================================================
{description}
=========================================================
END OF USER STRATEGY SPECIFICATION
=========================================================

IMPORTANT: Implement the user's strategy specification EXACTLY as written above.
- Do NOT invent a different strategy or substitute simpler conditions.
- Do NOT replace the specified indicators with different ones.
- Every entry condition, exit condition, and risk rule listed above MUST be coded.

=========================================================
TECHNICAL REQUIREMENTS (framework rules — do not skip)
=========================================================

RULE 1 — ASCII ONLY
- NO Unicode/emoji in any print() statement.
- Use [OK], [PASS], [FAIL], [BUY], [SELL] instead of ✓, ✗, ❌, etc.

RULE 2 — CORRECT BROKER API (SimBroker — MANDATORY)
SimBroker does NOT have buy(), sell(), or has_position() methods.
ALL trades MUST use create_signal() + broker.submit_signal():

```python
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType

# ENTRY (long):
signal = create_signal(
    signal_id=f"entry_{{timestamp}}",
    timestamp=timestamp,
    symbol=self.symbol,
    side=OrderSide.BUY,
    action=OrderAction.ENTRY,
    order_type=OrderType.MARKET,
    size=size,
    price=close,
    reason="reason string here"
)
order_id = self.broker.submit_signal(signal.to_dict())
if order_id:
    self.in_position = True
    self.position_size = size
    self.entry_price = close

# EXIT (long):
signal = create_signal(
    signal_id=f"exit_{{timestamp}}",
    timestamp=timestamp,
    symbol=self.symbol,
    side=OrderSide.SELL,
    action=OrderAction.EXIT,
    order_type=OrderType.MARKET,
    size=self.position_size,
    price=close,
    reason="exit reason"
)
order_id = self.broker.submit_signal(signal.to_dict())
if order_id:
    self.in_position = False
    self.position_size = 0
    self.entry_price = None
```

FORBIDDEN — these methods DO NOT EXIST on SimBroker:
  broker.buy()          # Does not exist
  broker.sell()         # Does not exist
  broker.has_position() # Does not exist
  broker.cash           # Does not exist — use broker.get_account_snapshot()['cash']

RULE 3 — INDICATOR NAMING
Use multi-period format in the indicators dict (preferred):
```python
indicators = {{
    'EMA': {{'periods': [9, 21]}},   # Creates EMA_9 and EMA_21
    'RSI': {{'periods': [14]}},      # Creates RSI_14
    'ADX': {{'periods': [14]}},      # Creates ADX_14
    'ATR': {{'periods': [14]}},      # Creates ATR_14
}}
```
Access in market_data using UPPERCASE keys: symbol_data.get('EMA_9'), symbol_data.get('RSI_14'), etc.

RULE 4 — REQUIRED IMPORTS (exact form):
```python
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent.parent   # codes -> Backtest -> monolithic_agent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import load_market_data
from Backtest.pattern_logger import PatternLogger
from Backtest.signal_logger import SignalLogger
```

FORBIDDEN IMPORTS:
  from sim_broker import SimBroker   # Wrong — need Backtest prefix
  import yfinance, requests          # No external data APIs
  parent.parent                      # Wrong — need 3 levels

RULE 5 — POSITION SIZING
Use broker.get_account_snapshot()['cash'] for available cash.
Never access broker.cash directly.

RULE 6 — DATA LOADING
```python
data_stream = load_market_data(
    ticker=test_symbol,
    indicators=indicators,
    period='max',
    interval='1d',
    stream=True
)
for timestamp, market_data, progress_pct in data_stream:
    strategy.on_bar(timestamp, market_data)
    broker.step_to(timestamp, market_data)
```

RULE 7 — MULTI-SYMBOL LOOP
```python
test_symbols = os.environ.get('BACKTEST_SYMBOLS', 'AAPL,TSLA,MSFT').split(',')
```

RULE 8 — REQUIRED OUTPUT FORMAT (bot_executor parses this)
```python
print(f"Total Trades: {{metrics['total_trades']}}")
print(f"Return: {{metrics['total_return_pct']:.2f}}%")
if metrics['total_trades'] > 0:
    print(f"Win Rate: {{metrics['win_rate'] * 100:.1f}}%")
print("[PASS] Strategy generated trades successfully")  # only if trades > 0
```

RULE 9 — CODE STRUCTURE
Must include:
  - Strategy class with __init__(self, broker, symbol, strategy_id, **params) and on_bar(self, timestamp, data)
  - run_backtest() function
  - if __name__ == '__main__': block calling run_backtest()
  - strategy.finalize() after the symbol loop
  - metrics = broker.compute_metrics() for results

=========================================================
Generate the COMPLETE, EXECUTABLE strategy code now.
Implement the user's strategy specification from the top of this prompt.
=========================================================
"""
        
        try:
            # Call Copilot API
            logger.info("[DEBUG] Calling Copilot API with enhanced prompt...")
            generated_code = self._call_copilot_api(enhanced_prompt)
            
            # Extract code from markdown if present
            logger.info("[DEBUG] Extracting code from response...")
            code = self._extract_code_from_response(generated_code)
            
            # DEBUG: Log extraction results
            logger.info("="*80)
            logger.info("[DEBUG] CODE EXTRACTION RESULTS")
            logger.info("="*80)
            logger.info(f"Extracted Code Length: {len(code)} chars")
            logger.info(f"Contains 'broker.buy': {'broker.buy' in code}")
            logger.info(f"Contains 'broker.sell': {'broker.sell' in code}")
            logger.info(f"Contains 'def ' (functions): {code.count('def ')} function definitions")
            logger.info(f"Contains 'if ' (conditionals): {code.count('if ')} if statements")
            logger.info(f"First 600 chars of code:\n{code[:600]}")
            logger.info("="*80)
            
            return code
            
        except (CopilotAuthError, requests.RequestException) as e:
            logger.error(f"Failed to generate strategy with Copilot: {e}")
            
            # Fallback to template if enabled
            if self.use_template_fallback and DJANGO_AVAILABLE:
                logger.info("Falling back to database template")
                return self._fallback_to_template(description)
            else:
                raise
    
    def _extract_code_from_response(self, response: str) -> str:
        """
        Extract Python code from API response (handles markdown code blocks)
        
        Args:
            response: Raw API response
            
        Returns:
            Extracted Python code
        """
        # Remove markdown code blocks if present
        if "```python" in response:
            parts = response.split("```python")
            if len(parts) > 1:
                code_part = parts[1].split("```")[0]
                return code_part.strip()
        elif "```" in response:
            parts = response.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        
        # Return as-is if no markdown blocks found
        return response.strip()
    
    def _fallback_to_template(self, description: str) -> str:
        """
        Fallback to database template when API is unavailable
        
        Args:
            description: Strategy description
            
        Returns:
            Template code
        """
        if not DJANGO_AVAILABLE:
            raise RuntimeError("Cannot fallback to template - Django not available")
        
        # Get most appropriate template (simple heuristic)
        templates = StrategyTemplate.objects.filter(is_active=True)
        
        if templates.exists():
            # Use first template for now (could be improved with better matching)
            template = templates.first()
            logger.info(f"Using template: {template.name}")
            return template.template_code
        else:
            raise RuntimeError("No templates available for fallback")
    
    def generate_and_save(
        self,
        description: str,
        output_dir: Optional[str] = None,
        strategy_name: Optional[str] = None,
        execute_after_generation: bool = False
    ) -> Tuple[str, Optional[Any]]:
        """
        Generate strategy code and save to file
        
        Args:
            description: Natural language strategy description
            output_dir: Directory to save strategy (default: Backtest/codes/)
            strategy_name: Strategy file name (auto-generated if None)
            execute_after_generation: If True, execute bot after generation
            
        Returns:
            Tuple of (file_path, execution_result or None)
        """
        # Generate code
        logger.info(f"Generating strategy: {description[:100]}...")
        code = self.generate_strategy_code(description)
        
        # Determine output path
        if output_dir is None:
            output_dir = Path(__file__).parent / "codes"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate strategy name
        if strategy_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            strategy_name = f"strategy_{timestamp}.py"
        elif not strategy_name.endswith('.py'):
            strategy_name += '.py'
        
        output_path = output_dir / strategy_name
        
        # VALIDATION: Check code before saving
        try:
            from pre_execution_validator import validate_generated_code
            is_valid, validation_errors = validate_generated_code(code)
            
            if not is_valid:
                logger.warning(f"Generated code has validation errors:")
                for error in validation_errors:
                    logger.warning(f"  - {error}")
                
                # You can choose to:
                # 1. Raise error (strict mode)
                # raise ValueError(f"Generated code failed validation: {validation_errors}")
                
                # 2. Save with warning (permissive mode - current)
                logger.warning("Saving code despite validation errors - may fail at runtime")
            else:
                logger.info("✓ Code passed pre-execution validation")
        
        except ImportError:
            logger.warning("Pre-execution validator not available - skipping validation")
        except Exception as e:
            logger.warning(f"Validation error (non-fatal): {e}")
        
        # Save code
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        logger.info(f"✓ Strategy saved to: {output_path}")
        
        # Execute if requested
        execution_result = None
        if execute_after_generation and BOT_EXECUTOR_AVAILABLE:
            logger.info("Executing generated strategy...")
            try:
                executor = get_bot_executor()
                execution_result = executor.execute_bot(strategy_file=str(output_path))
                
                if execution_result.success:
                    logger.info(f"✓ Execution successful: {execution_result.return_pct}% return")
                else:
                    logger.warning(f"✗ Execution failed: {execution_result.error_message}")
            except Exception as e:
                logger.error(f"Execution error: {e}")
        
        return str(output_path), execution_result
    
    def fix_bot_errors_iteratively(
        self,
        strategy_file: str,
        max_iterations: int = 3,
        learning_system=None,
        error_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, List[Any]]:
        """
        Fix bot errors iteratively using Copilot AI
        
        Args:
            strategy_file: Path to strategy file with errors
            max_iterations: Maximum fix attempts
            learning_system: Optional ErrorLearningSystem for feedback loop
            error_context: Additional context for debugging (e.g., no trades issue)
            
        Returns:
            Tuple of (success, final_file_path, fix_history)
        """
        if not BOT_ERROR_FIXER_AVAILABLE:
            logger.error("Bot error fixer not available")
            return False, strategy_file, []
        
        try:
            # Use Copilot-based error fixer with learning system
            # Pass self as strategy_generator so fixer can generate fixes
            fixer = BotErrorFixer(
                strategy_generator=self,  # Pass this CopilotStrategyGenerator instance
                llm_backend='copilot',
                learning_system=learning_system
            )
            
            # If no-trades issue, add context to guide AI debugging
            if error_context and error_context.get('is_no_trades'):
                logger.info("⚠️  NO TRADES ISSUE - AI will debug why strategy didn't place trades")
                logger.info(f"   Trades count: {error_context.get('trades_count')}")
                logger.info(f"   Error: {error_context.get('execution_error')}")
            
            # Use BotErrorFixer.iterative_fix method
            from Backtest.bot_executor import get_bot_executor
            executor = get_bot_executor()
            
            success, final_code, history = fixer.iterative_fix(
                bot_file=Path(strategy_file),
                bot_executor=executor,
                max_attempts=max_iterations
            )
            
            # Return path instead of code
            final_path = strategy_file
            return success, final_path, history
        except Exception as e:
            logger.error(f"Error fixing bot errors: {e}")
            return False, strategy_file, []


# Singleton instance
_copilot_generator: Optional[CopilotStrategyGenerator] = None


def get_copilot_generator() -> CopilotStrategyGenerator:
    """Get singleton CopilotStrategyGenerator instance"""
    global _copilot_generator
    if _copilot_generator is None:
        _copilot_generator = CopilotStrategyGenerator()
    return _copilot_generator
