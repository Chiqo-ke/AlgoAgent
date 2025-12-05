"""
Chat Intent Classifier for Trading Strategy Conversations
=========================================================

Detects user intent from chat messages to enable continuous flow editing.

Supported Intents:
- CREATE: User wants to create a new strategy
- EDIT: User wants to modify an existing strategy  
- QUESTION: User is asking about strategies or trading
- CLARIFY: User is providing clarification to a previous question

Usage:
    classifier = ChatIntentClassifier(use_gemini=True)
    result = classifier.classify("Set stop loss to 10 pips", conversation_history)
    
    if result['intent'] == 'EDIT':
        # Apply modifications
        ...
"""

import os
import json
import re
import logging
from typing import Dict, List, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class ChatIntentClassifier:
    """Classifies user intent in trading strategy conversations"""
    
    # Keywords for intent detection
    EDIT_KEYWORDS = [
        'set', 'change', 'update', 'modify', 'adjust', 'add', 'remove',
        'increase', 'decrease', 'use', 'apply', 'switch', 'replace'
    ]
    
    CREATE_KEYWORDS = [
        'create', 'make', 'build', 'generate', 'new strategy', 'start'
    ]
    
    QUESTION_KEYWORDS = [
        'what', 'how', 'why', 'when', 'where', 'which', 'who',
        'explain', 'tell me', 'show me', 'can you', 'could you'
    ]
    
    def __init__(self, use_gemini: bool = True):
        """
        Initialize intent classifier
        
        Args:
            use_gemini: Whether to use Gemini AI for classification (more accurate)
                       If False, uses rule-based classification
        """
        self.use_gemini = use_gemini
        
        if use_gemini:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logger.warning("GEMINI_API_KEY not found, falling back to rule-based classification")
                self.use_gemini = False
            else:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                logger.info("Initialized ChatIntentClassifier with Gemini")
        
        if not self.use_gemini:
            logger.info("Initialized ChatIntentClassifier with rule-based classification")
    
    def classify(self, message: str, conversation_history: List[Dict]) -> Dict:
        """
        Classify user intent from message and conversation context
        
        Args:
            message: The user's latest message
            conversation_history: Previous messages in conversation
                Format: [{'role': 'user'|'assistant', 'content': '...'}, ...]
        
        Returns:
            {
                'intent': 'CREATE' | 'EDIT' | 'QUESTION' | 'CLARIFY',
                'confidence': 0.0-1.0,
                'reasoning': 'Why this classification was chosen',
                'entities': {
                    'parameters': {},  # e.g. {'stop_loss': '10 pips', 'take_profit': '50 pips'}
                    'indicators': {},  # e.g. {'ema_short': 30, 'ema_long': 60}
                    'conditions': []   # New entry/exit conditions
                }
            }
        """
        if self.use_gemini:
            return self._classify_with_gemini(message, conversation_history)
        else:
            return self._classify_rule_based(message, conversation_history)
    
    def _classify_with_gemini(self, message: str, history: List[Dict]) -> Dict:
        """Use Gemini AI for accurate intent classification"""
        
        # Format conversation history
        history_text = self._format_history(history[-10:])  # Last 10 messages for context
        
        prompt = f"""
You are an expert at understanding trading strategy conversations.

CONVERSATION HISTORY:
{history_text}

LATEST USER MESSAGE:
"{message}"

Analyze the user's intent and classify as ONE of these:

1. **CREATE** - User wants to create a completely NEW strategy
   Examples: "Create an EMA crossover strategy", "Make a bot that...", "Build a new strategy"

2. **EDIT** - User wants to MODIFY an existing strategy being discussed
   Examples: "Set stop loss to 10 pips", "Change the EMA period to 50", "Add RSI condition"
   
3. **QUESTION** - User is asking ABOUT strategies, not creating/editing
   Examples: "How does EMA work?", "What's a stop loss?", "Why did you recommend that?"
   
4. **CLARIFY** - User is providing MORE INFO in response to a question
   Examples: Answering AI's question, providing missing parameters

CRITICAL RULES:
- If conversation has existing strategy AND user mentions modifying parameters → EDIT
- If user says "create" or "make" without prior strategy → CREATE  
- If user asks "what", "how", "why" → QUESTION
- Look at conversation history to understand context

Extract any trading parameters mentioned:
- Risk management: stop_loss, take_profit, risk_per_trade
- Indicators: ema, sma, rsi, macd, bollinger_bands, etc.
- Conditions: entry_conditions, exit_conditions
- Timeframe: timeframe, data_frequency

Return ONLY valid JSON (no markdown, no code blocks):
{{
    "intent": "CREATE" | "EDIT" | "QUESTION" | "CLARIFY",
    "confidence": 0.85,
    "reasoning": "Brief explanation of why",
    "entities": {{
        "parameters": {{}},
        "indicators": {{}},
        "conditions": []
    }}
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            response_text = re.sub(r'^```json\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            logger.info(f"Intent classified: {result['intent']} (confidence: {result['confidence']})")
            logger.debug(f"Reasoning: {result['reasoning']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error classifying intent with Gemini: {e}")
            logger.error(f"Response text: {response.text if 'response' in locals() else 'N/A'}")
            # Fallback to rule-based
            return self._classify_rule_based(message, history)
    
    def _classify_rule_based(self, message: str, history: List[Dict]) -> Dict:
        """Simple rule-based classification as fallback"""
        
        message_lower = message.lower()
        
        # Check for CREATE intent
        if any(keyword in message_lower for keyword in self.CREATE_KEYWORDS):
            return {
                'intent': 'CREATE',
                'confidence': 0.7,
                'reasoning': 'Message contains create keywords',
                'entities': self._extract_entities_simple(message)
            }
        
        # Check for EDIT intent
        if any(keyword in message_lower for keyword in self.EDIT_KEYWORDS):
            # Check if there's a strategy in conversation context
            has_strategy_context = any(
                'strategy' in msg.get('content', '').lower() 
                for msg in history[-5:]  # Last 5 messages
            )
            
            if has_strategy_context:
                return {
                    'intent': 'EDIT',
                    'confidence': 0.8,
                    'reasoning': 'Message contains edit keywords and strategy exists in context',
                    'entities': self._extract_entities_simple(message)
                }
        
        # Check for QUESTION intent
        if any(keyword in message_lower for keyword in self.QUESTION_KEYWORDS):
            return {
                'intent': 'QUESTION',
                'confidence': 0.7,
                'reasoning': 'Message contains question keywords',
                'entities': {'parameters': {}, 'indicators': {}, 'conditions': []}
            }
        
        # Default: CLARIFY if can't determine
        return {
            'intent': 'CLARIFY',
            'confidence': 0.5,
            'reasoning': 'Unable to determine clear intent',
            'entities': self._extract_entities_simple(message)
        }
    
    def _extract_entities_simple(self, message: str) -> Dict:
        """Simple entity extraction from message"""
        
        entities = {
            'parameters': {},
            'indicators': {},
            'conditions': []
        }
        
        message_lower = message.lower()
        
        # Extract stop loss
        stop_loss_match = re.search(r'stop\s*loss\s*(?:of|to|at)?\s*(\d+)\s*(pips?|%|percent|points?)', message_lower)
        if stop_loss_match:
            entities['parameters']['stop_loss'] = f"{stop_loss_match.group(1)} {stop_loss_match.group(2)}"
        
        # Extract take profit  
        tp_match = re.search(r'take\s*profit\s*(?:of|to|at)?\s*(\d+)\s*(pips?|%|percent|points?)', message_lower)
        if tp_match:
            entities['parameters']['take_profit'] = f"{tp_match.group(1)} {tp_match.group(2)}"
        
        # Extract EMA periods
        ema_matches = re.findall(r'(\d+)\s*(?:period|day)?\s*ema', message_lower)
        if len(ema_matches) >= 2:
            entities['indicators']['ema_short'] = int(ema_matches[0])
            entities['indicators']['ema_long'] = int(ema_matches[1])
        elif len(ema_matches) == 1:
            entities['indicators']['ema_period'] = int(ema_matches[0])
        
        # Extract RSI
        rsi_match = re.search(r'rsi\s*(?:<|>|below|above)\s*(\d+)', message_lower)
        if rsi_match:
            entities['indicators']['rsi_level'] = int(rsi_match.group(1))
        
        return entities
    
    def _format_history(self, history: List[Dict]) -> str:
        """Format conversation history for prompt"""
        
        if not history:
            return "(No previous conversation)"
        
        formatted = []
        for msg in history:
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')[:200]  # Truncate long messages
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)


# Convenience function
def classify_intent(message: str, conversation_history: List[Dict] = None, use_gemini: bool = True) -> Dict:
    """
    Convenience function to classify intent without instantiating class
    
    Args:
        message: User's message
        conversation_history: Previous messages (optional)
        use_gemini: Use Gemini AI (default: True)
    
    Returns:
        Intent classification result
    """
    classifier = ChatIntentClassifier(use_gemini=use_gemini)
    return classifier.classify(message, conversation_history or [])


if __name__ == "__main__":
    # Test cases
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Testing Intent Classifier")
    print("=" * 60)
    
    # Test 1: EDIT intent
    print("\nTest 1: EDIT intent")
    result = classify_intent(
        "Set stop loss to 10 pips below entry",
        conversation_history=[
            {'role': 'user', 'content': 'Create an EMA crossover strategy'},
            {'role': 'assistant', 'content': 'Strategy created successfully!'}
        ]
    )
    print(f"Intent: {result['intent']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Entities: {json.dumps(result['entities'], indent=2)}")
    
    # Test 2: CREATE intent
    print("\nTest 2: CREATE intent")
    result = classify_intent(
        "Create a simple moving average crossover strategy with 30 and 60 period EMAs"
    )
    print(f"Intent: {result['intent']}")
    print(f"Confidence: {result['confidence']}")
    
    # Test 3: QUESTION intent
    print("\nTest 3: QUESTION intent")
    result = classify_intent(
        "How does exponential moving average work?"
    )
    print(f"Intent: {result['intent']}")
    print(f"Confidence: {result['confidence']}")
    
    print("\n" + "=" * 60)
