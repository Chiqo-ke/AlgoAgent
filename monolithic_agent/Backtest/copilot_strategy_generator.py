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
            # Fallback comprehensive prompt with API reference
            base_prompt = """
# Trading Strategy Generation Instructions

You are generating a trading strategy for the SimBroker backtesting engine.
Follow these specifications EXACTLY to avoid runtime errors.

## CRITICAL: Import Setup (MUST USE EXACTLY)

```python
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Path setup: codes -> Backtest -> monolithic_agent (3 levels)
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import from Backtest package
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import load_market_data
```

## CRITICAL: Broker Initialization

```python
# Step 1: Create config object
config = BacktestConfig(
    start_cash=100000.0,
    fee_flat=1.0,
    fee_pct=0.001,
    slippage_pct=0.0005
)

# Step 2: Initialize broker with config
broker = SimBroker(config)  # ✅ Pass config object
```

## CRITICAL: Strategy Class Structure

```python
class MyStrategy:
    def __init__(self, broker, symbol="AAPL", strategy_id="my_strat", **params):
        self.broker = broker
        self.symbol = symbol
        self.strategy_id = strategy_id
        # Your parameters here
    
    def on_bar(self, timestamp, data):
        # Process each bar
        symbol_data = data.get(self.symbol)
        if not symbol_data:
            return
        
        # Your trading logic here
        # Call broker.submit_signal() to place trades
```

## CRITICAL: Signal Schema

ALL signals MUST have these EXACT fields:

```python
signal_id = 0  # Initialize counter before loop

# In your trading loop:
signal_id += 1
signal = {
    'signal_id': f'sig_{signal_id:04d}',  # Required: unique ID
    'timestamp': current_timestamp.isoformat(),  # Required: ISO format
    'symbol': 'AAPL',  # Required: symbol string
    'side': 'BUY',  # Required: 'BUY' or 'SELL' (NOT 'LONG'/'SHORT')
    'action': 'ENTRY',  # Required: 'ENTRY' or 'EXIT' (NOT 'BUY'/'SELL')
    'order_type': 'MARKET',  # Required: 'MARKET' or 'LIMIT'
    'size': 100,  # Required: positive integer (NOT 'quantity')
    'meta': {'reason': 'Signal description'}  # Optional: dict (NOT 'reason' key)
}

broker.submit_signal(signal)
```

## CRITICAL: Market Data Format

```python
# Correct: nested dict with symbol as key
market_data = {
    'AAPL': {  # Symbol level
        'open': 150.0,
        'high': 151.5,
        'low': 149.5,
        'close': 150.5,
        'volume': 1000000
    }
}

broker.step_to(timestamp, market_data)
```

## CRITICAL: Valid Enum Values

```python
# OrderSide (use these EXACT values)
'BUY'   # ✅ Correct
'SELL'  # ✅ Correct

# OrderAction (use these EXACT values)
'ENTRY'  # ✅ Open position
'EXIT'   # ✅ Close position

# FORBIDDEN values (will fail validation):
'LONG', 'SHORT', 'CLOSE', 'OPEN'  # ❌ These will cause errors
```

## CRITICAL: Broker Methods

```python
# Get performance statistics
stats = broker.get_statistics()  # ✅ Correct method name
# NOT broker.get_metrics()  ❌ This method does NOT exist

# Available statistics
total_trades = stats.get('trade_count', 0)
win_rate = stats.get('win_rate', 0.0)
total_return = stats.get('total_return', 0.0)
sharpe_ratio = stats.get('sharpe_ratio', 0.0)
max_drawdown = stats.get('max_drawdown', 0.0)
final_equity = stats.get('equity', config.start_cash)
```

## Common Mistakes to AVOID

1. ❌ Using old API: `broker = SimBroker(symbol="AAPL", ...)` 
   ✅ Use config: `broker = SimBroker(config)`

2. ❌ Wrong import: `from Backtest.simbroker import SimBroker`
   ✅ Correct: `from Backtest.sim_broker import SimBroker`

3. ❌ Wrong signal field: `'quantity': 100`
   ✅ Correct: `'size': 100`

4. ❌ Wrong signal side: `'side': 'LONG'`
   ✅ Correct: `'side': 'BUY'`

5. ❌ Wrong signal action: `'action': 'BUY'`
   ✅ Correct: `'action': 'ENTRY'`

6. ❌ Missing signal_id: Signal dict without 'signal_id' field
   ✅ Always include: `'signal_id': f'sig_{counter:04d}'`

7. ❌ Wrong method: `broker.get_metrics()`
   ✅ Correct: `broker.get_statistics()`

8. ❌ Flat market data: `market_data = {'open': 150, ...}`
   ✅ Nested: `market_data = {'AAPL': {'open': 150, ...}}`

## REQUIRED: Strategy Structure

Your generated code MUST follow this structure:

```python
#!/usr/bin/env python3
\"\"\"
[Strategy Name]
[Brief description]
\"\"\"

# Imports (see above)
import sys
from pathlib import Path
from datetime import datetime, timedelta
import os

parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import OrderSide, OrderAction

def main():
    # 1. Create config
    config = BacktestConfig(...)
    
    # 2. Initialize broker
    broker = SimBroker(config)
    
    # 3. Load/generate market data
    # ... your data loading logic
    
    # 4. Initialize strategy state
    signal_id = 0
    position = 0
    
    # 5. Main trading loop
    for bar in market_data:
        # Step broker forward
        broker.step_to(timestamp, market_data_dict)
        
        # Your strategy logic
        # ...
        
        # Generate signals with CORRECT schema
        if buy_condition:
            signal_id += 1
            signal = {
                'signal_id': f'sig_{signal_id:04d}',
                'timestamp': timestamp.isoformat(),
                'symbol': config.symbol,
                'side': 'BUY',
                'action': 'ENTRY',
                'order_type': 'MARKET',
                'size': shares,
                'meta': {'reason': 'Buy reason'}
            }
            broker.submit_signal(signal)
    
    # 6. Get and display results
    stats = broker.get_statistics()
    print(f"Total Trades: {stats.get('trade_count', 0)}")
    print(f"Total Return: {stats.get('total_return', 0):.2f}%")
    # ... other metrics

if __name__ == "__main__":
    main()
```

## Full API Documentation

For complete API reference including all methods, parameters, and examples,
see: Backtest/SIMBROKER_API_REFERENCE.md

CRITICAL RULES:
1. Use EXACT import patterns shown above
2. Initialize broker with BacktestConfig object
3. Use canonical signal schema with ALL required fields
4. Use correct enum values for side ('BUY'/'SELL') and action ('ENTRY'/'EXIT')
5. Call broker.get_statistics() NOT get_metrics()
6. Format market data as nested dict: {symbol: {price_data}}
7. Include proper error handling
8. Generate complete, executable Python code
"""
        
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
            if e.response.status_code == 401:
                # Token expired or invalid
                logger.error("Copilot authentication failed - token may be expired")
                raise CopilotAuthError("Authentication failed. Please re-authenticate.")
            elif e.response.status_code == 429:
                # Rate limit
                logger.error("Copilot API rate limit exceeded")
                raise CopilotAuthError("Rate limit exceeded. Please try again later.")
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
Generate a complete, executable trading strategy based on this description:

{description}

CRITICAL: USE ONLY ASCII CHARACTERS
- NO Unicode characters (checkmarks, emoji, special symbols)
- Use plain text: [OK], [PASS], [FAIL], [X] instead of ✓, ✗, ❌, etc.
- Ensure all print statements use ASCII-safe strings
- Use standard ASCII punctuation only

CRITICAL: INDICATOR NAMING CONVENTION (MUST FOLLOW EXACTLY)
When using indicators, the dictionary key must START with the uppercase indicator name from the registry, followed by underscore and parameters:

✅ CORRECT - Keys start with uppercase indicator name:
```python
# Define indicators with keys that start with UPPERCASE indicator name
indicators = {{
    'EMA_12': {{'name': 'EMA', 'timeperiod': 12}},  # Key starts with 'EMA'
    'EMA_26': {{'name': 'EMA', 'timeperiod': 26}}   # Key starts with 'EMA'
}}

# Access in market_data using LOWERCASE version of the key
ema_fast = data.get('EMA_12')  # ✅ Matches key
ema_slow = data.get('EMA_26')  # ✅ Matches key
```

OR use multi-period format (PREFERRED for multiple periods):
```python
# Multi-period format - single indicator with multiple periods
indicators = {{
    'EMA': {{'periods': [12, 26]}}  # Creates 'EMA_12' and 'EMA_26'
}}

# Access with period suffix
ema_fast = data.get('EMA_12')  # ✅ Auto-generated key
ema_slow = data.get('EMA_26')  # ✅ Auto-generated key
```

❌ WRONG (Validation will fail - indicator base name not recognized):
```python
# DON'T use all-lowercase keys
indicators = {{
    'ema_12': {{'name': 'EMA', 'timeperiod': 12}},  # ❌ 'ema_12' not recognized
    'ema_26': {{'name': 'EMA', 'timeperiod': 26}}   # ❌ 'ema_26' not recognized
}}
```

❌ ALSO WRONG (Duplicate keys in dict - Python will only keep last one):
```python
indicators = {{
    'EMA': {{'timeperiod': 12}},  # ❌ Will be overwritten
    'EMA': {{'timeperiod': 26}}   # ❌ Duplicate key - only this one kept
}}
```

INDICATOR NAMING RULES:
1. Key MUST start with UPPERCASE indicator name from registry (EMA, RSI, MACD, etc.)
2. For single period: 'EMA_12' with {{'name': 'EMA', 'timeperiod': 12}}
3. For multiple periods: 'EMA' with {{'periods': [12, 26]}} - creates 'EMA_12' and 'EMA_26'
4. Access using the EXACT key name: data.get('EMA_12')
5. Common indicators: EMA, SMA, RSI, MACD, BBANDS, ATR, STOCH, ADX

CRITICAL IMPORT REQUIREMENTS (MUST FOLLOW EXACTLY):
```python
import sys
from pathlib import Path

# Add parent directory to path (codes -> Backtest -> monolithic_agent)
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import from Backtest package:
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import load_market_data
from Backtest.pattern_logger import PatternLogger
from Backtest.signal_logger import SignalLogger
```

FORBIDDEN IMPORTS (will cause errors):
❌ from sim_broker import SimBroker  # Wrong - need Backtest prefix
❌ from config import BacktestConfig  # Wrong - need Backtest prefix
❌ import simbroker  # Wrong module name
❌ parent.parent  # Wrong - need 3 levels not 2

Requirements:
1. Use the SimBroker API as defined in the system prompt
2. Include proper imports EXACTLY as shown above
3. Include proper error handling
4. Generate complete, runnable Python code
5. Follow best practices for trading strategies
6. Use available indicators when appropriate

CRITICAL TRADING LOGIC REQUIREMENTS (MUST IMPLEMENT):
⚠️ The strategy MUST contain actual trading logic that places trades:
1. MUST call broker.buy() when buy conditions are met
2. MUST call broker.sell() when sell conditions are met
3. MUST have clear if/else conditional logic that evaluates market data
4. MUST implement entry AND exit conditions
5. DO NOT generate placeholder code - generate REAL trading conditions

Example of REQUIRED trading logic pattern:
```python
def my_strategy(broker, market_data):
    data = market_data.get('data', [])
    if not data:
        return
    
    # Get indicator values
    ema_fast = data[-1].get('EMA_12')
    ema_slow = data[-1].get('EMA_26')
    
    # ACTUAL trading conditions (not placeholders)
    if ema_fast is not None and ema_slow is not None:
        # Buy when fast EMA crosses above slow EMA
        if ema_fast > ema_slow and not broker.has_position():
            broker.buy(size=100)  # ✅ REAL buy call
        
        # Sell when fast EMA crosses below slow EMA
        elif ema_fast < ema_slow and broker.has_position():
            broker.sell(size=100)  # ✅ REAL sell call
```

❌ DO NOT generate code like this (no actual trading):
```python
def my_strategy(broker, market_data):
    # TODO: Implement trading logic  # ❌ Placeholder
    pass  # ❌ No trading
```

CRITICAL OUTPUT REQUIREMENTS:
1. Return COMPLETE Python code including ALL required components
2. MUST include: imports, Strategy class with __init__ and on_bar methods, run_backtest function
3. DO NOT return partial code, summaries, or explanations
4. The code must be immediately executable without modifications
5. Include docstrings and comments for clarity

Generate the COMPLETE, EXECUTABLE strategy code now:
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
