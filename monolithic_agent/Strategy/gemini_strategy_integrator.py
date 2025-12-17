"""
Gemini Strategy Integrator - AI-powered strategy analysis using Gemini API
Enhances strategy validation with natural language understanding and recommendations.
Now includes conversation memory using LangChain for contextual interactions.
"""

import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GeminiStrategyIntegrator:
    """
    Integrates Gemini API for intelligent strategy analysis and recommendations.
    Now supports conversation context and memory.
    """
    
    def __init__(self, api_key: str = None, session_id: str = None, user=None):
        """
        Initialize Gemini integrator with API key and optional conversation session.
        
        Args:
            api_key: Gemini API key (defaults to environment variable or key rotation)
            session_id: Optional chat session ID for conversation memory
            user: Optional Django user object
        """
        # Try key rotation first if enabled
        self.api_key = None
        self.selected_key_id = 'default'
        
        if not api_key and os.getenv('ENABLE_KEY_ROTATION', 'false').lower() == 'true':
            try:
                from Backtest.key_rotation import get_key_manager
                key_manager = get_key_manager()
                if key_manager.enabled:
                    key_info = key_manager.select_key(
                        model_preference='gemini-2.0-flash',
                        tokens_needed=5000
                    )
                    if key_info:
                        self.api_key = key_info['secret']
                        self.selected_key_id = key_info['key_id']
                        print(f"✓ Using key rotation (selected key: {self.selected_key_id})")
            except Exception as e:
                print(f"⚠ Key rotation failed: {e}")
        
        # Fallback to single API key
        if not self.api_key:
            self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        self.client = None
        self.model = None
        self.use_mock = False
        self.session_id = session_id
        self.user = user
        self.conversation_manager = None
        
        # Initialize Gemini API
        if self.api_key and self.api_key != 'your_gemini_api_key_here':
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                # Use gemini-2.5-flash for fast, efficient responses
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                self.client = genai
                self.allow_custom_formatting = True  # AI can provide formatted_response
                print("✓ Gemini API initialized successfully (custom formatting enabled)")
            except ImportError:
                print("⚠ google-generativeai not installed. Run: pip install google-generativeai")
                self.use_mock = True
            except Exception as e:
                print(f"⚠ Gemini API initialization failed: {e}")
                self.use_mock = True
        else:
            print("⚠ No Gemini API key found. Using mock responses.")
            self.use_mock = True
        
        # Initialize conversation manager if session_id provided
        if session_id:
            self._init_conversation_manager()
    
    def _init_conversation_manager(self):
        """Initialize the conversation manager for this session"""
        try:
            from Strategy.conversation_manager import ConversationManager
            self.conversation_manager = ConversationManager(
                session_id=self.session_id,
                user=self.user
            )
            print(f"✓ Conversation manager initialized for session {self.session_id}")
        except Exception as e:
            print(f"⚠ Could not initialize conversation manager: {e}")
            self.conversation_manager = None
    
    def set_session(self, session_id: str, user=None):
        """
        Set or change the conversation session.
        
        Args:
            session_id: Chat session ID
            user: Optional Django user object
        """
        self.session_id = session_id
        self.user = user
        self._init_conversation_manager()
    
    def _get_conversation_context(self, max_messages: int = 10) -> str:
        """
        Get recent conversation history as context for the AI.
        
        Args:
            max_messages: Maximum number of recent messages to include
            
        Returns:
            Formatted conversation history string
        """
        if not self.conversation_manager:
            return ""
        
        history = self.conversation_manager.get_context_window(max_messages=max_messages)
        
        if not history:
            return ""
        
        context_str = "\n\nPREVIOUS CONVERSATION:\n"
        for msg in history:
            role = msg['role'].upper()
            content = msg['content'][:200]  # Truncate long messages
            context_str += f"{role}: {content}\n"
        
        return context_str
    
    def analyze_strategy_text(self, strategy_text: str, use_context: bool = True) -> Dict[str, Any]:
        """
        Analyze raw strategy text using Gemini to extract structure and insights.
        Now includes conversation context for better understanding.
        
        Args:
            strategy_text: Raw strategy description from user
            use_context: Whether to include conversation history in the analysis
            
        Returns:
            Analysis including extracted steps, type, risk level, and suggestions
        """
        # Store user message in conversation
        if self.conversation_manager:
            self.conversation_manager.add_user_message(
                f"Analyze strategy: {strategy_text}",
                metadata={'action': 'analyze_strategy'}
            )
        
        if self.use_mock:
            result = self._mock_analyze_strategy(strategy_text)
            if self.conversation_manager:
                self.conversation_manager.add_ai_message(
                    json.dumps(result, indent=2),
                    metadata={'action': 'strategy_analysis', 'mock': True}
                )
            return result
        
        # Build context-aware prompt
        context = self._get_conversation_context() if use_context else ""
        
        prompt = f"""
Analyze this trading strategy and provide a structured analysis.
{context}

STRATEGY:
{strategy_text}

Please provide:
1. EXTRACTED_STEPS: List the strategy steps in a numbered format
2. STRATEGY_TYPE: Classify the strategy (e.g., trend-following, mean-reversion, momentum, breakout, scalping)
3. RISK_LEVEL: Assess risk level (low, medium, high, very_high)
4. INSTRUMENTS: What instruments/assets are mentioned or implied
5. TIMEFRAME: What timeframe is suggested or implied (e.g., intraday, daily, weekly)
6. MISSING_ELEMENTS: What critical elements are missing (entry rules, exit rules, position sizing, risk management)
7. CONCERNS: Any concerns or red flags (unclear rules, excessive risk, missing safeguards)
8. SUGGESTIONS: Top 3 improvements to make this strategy more robust

Format your response as JSON with these exact keys.
"""
        
        try:
            response = self.model.generate_content(prompt)
            # Parse response - try to extract JSON
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            analysis = json.loads(response_text.strip())
            
            # Store AI response in conversation
            if self.conversation_manager:
                self.conversation_manager.add_ai_message(
                    json.dumps(analysis, indent=2),
                    metadata={'action': 'strategy_analysis'}
                )
            
            return analysis
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return text analysis
            result = {
                "extracted_steps": ["Could not parse steps automatically"],
                "strategy_type": "unknown",
                "risk_level": "medium",
                "raw_analysis": response.text,
                "parsing_error": True
            }
        except Exception as e:
            print(f"Error analyzing strategy: {e}")
            return self._mock_analyze_strategy(strategy_text)
    
    def generate_recommendations(self, strategy_dict: Dict[str, Any], context: str = "") -> List[Dict[str, Any]]:
        """
        Generate intelligent recommendations using Gemini.
        
        Args:
            strategy_dict: Canonical strategy dictionary
            context: Additional context about user's goals or concerns
            
        Returns:
            List of prioritized recommendations
        """
        if self.use_mock:
            return self._mock_generate_recommendations(strategy_dict)
        
        prompt = f"""
Analyze this trading strategy and provide actionable recommendations:

STRATEGY:
{json.dumps(strategy_dict, indent=2)}

CONTEXT:
{context or "No additional context provided"}

Provide 5-7 prioritized recommendations to improve this strategy. For each recommendation:
1. TITLE: Short title (5-10 words)
2. DESCRIPTION: What to do (one sentence)
3. RATIONALE: Why this matters (one sentence)
4. PRIORITY: 1=high, 2=medium, 3=low
5. CATEGORY: risk, sizing, testing, parameters, exits, or entries
6. TEST_PARAMS: Suggested parameters to test (optional)

Format as JSON array with these keys: [{{title, description, rationale, priority, category, test_params}}]
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Remove markdown code blocks
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            recommendations = json.loads(response_text.strip())
            return recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return self._mock_generate_recommendations(strategy_dict)
    
    def enhance_url_content(self, url: str, raw_content: str) -> Dict[str, Any]:
        """
        Use Gemini to extract and structure strategy information from web content.
        
        Args:
            url: Source URL
            raw_content: Raw content fetched from URL
            
        Returns:
            Enhanced structured content
        """
        if self.use_mock:
            return {"enhanced": False, "content": raw_content}
        
        prompt = f"""
Extract the trading strategy from this content and structure it:

SOURCE: {url}

CONTENT:
{raw_content[:3000]}  # Limit to first 3000 chars

Extract:
1. STRATEGY_STEPS: List of strategy steps
2. AUTHOR: Who created/presented this strategy
3. KEY_INDICATORS: Technical indicators mentioned
4. ENTRY_RULES: Entry conditions
5. EXIT_RULES: Exit conditions
6. RISK_MANAGEMENT: Risk management rules
7. SUMMARY: 2-3 sentence summary

Format as JSON.
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            enhanced = json.loads(response_text.strip())
            enhanced["enhanced"] = True
            return enhanced
            
        except Exception as e:
            print(f"Error enhancing content: {e}")
            return {"enhanced": False, "content": raw_content}
    
    def ask_clarifying_question(self, strategy_dict: Dict[str, Any], missing_info: List[str]) -> str:
        """
        Generate an intelligent clarifying question based on what's missing.
        
        Args:
            strategy_dict: Current strategy structure
            missing_info: List of missing information
            
        Returns:
            A single, concise clarifying question
        """
        # Store in conversation
        if self.conversation_manager:
            self.conversation_manager.add_system_message(
                f"Generating clarifying question for missing: {', '.join(missing_info)}"
            )
        
        if self.use_mock:
            question = f"Could you clarify: {', '.join(missing_info[:2])}?"
            if self.conversation_manager:
                self.conversation_manager.add_ai_message(question, metadata={'action': 'clarifying_question'})
            return question
        
        # Include conversation context
        context = self._get_conversation_context()
        
        prompt = f"""
Generate ONE concise clarifying question for this trading strategy.
{context}

CURRENT STRATEGY:
{json.dumps(strategy_dict, indent=2)}

MISSING INFORMATION:
{', '.join(missing_info)}

Generate a single, specific question that would help clarify the most critical missing element.
Be conversational and friendly. Return just the question text, nothing else.
"""
        
        try:
            response = self.model.generate_content(prompt)
            question = response.text.strip()
            
            if self.conversation_manager:
                self.conversation_manager.add_ai_message(question, metadata={'action': 'clarifying_question'})
            
            return question
        except Exception as e:
            print(f"Error generating question: {e}")
            return f"Could you please clarify: {missing_info[0]}?"
    
    def chat(self, user_message: str, include_strategy_context: bool = True) -> str:
        """
        Have a conversational interaction with the AI about strategies.
        This method maintains conversation context and can discuss strategies naturally.
        
        Args:
            user_message: User's message/question
            include_strategy_context: Whether to include linked strategy info in context
            
        Returns:
            AI's response
        """
        # Store user message
        if self.conversation_manager:
            self.conversation_manager.add_user_message(user_message, metadata={'action': 'chat'})
        
        if self.use_mock:
            response = f"[Mock response] I understand you're asking about: {user_message[:50]}..."
            if self.conversation_manager:
                self.conversation_manager.add_ai_message(response, metadata={'action': 'chat', 'mock': True})
            return response
        
        # Build context from conversation history
        context = self._get_conversation_context(max_messages=20)
        
        # Add strategy context if available
        strategy_context = ""
        if include_strategy_context and self.conversation_manager:
            session = self.conversation_manager.get_session()
            if session.strategy:
                strategy_context = f"""
LINKED STRATEGY CONTEXT:
Strategy Name: {session.strategy.name}
Description: {session.strategy.description}
Status: {session.strategy.status}
"""
        
        prompt = f"""
You are an expert trading strategy assistant. Help the user with their question about trading strategies.
{context}
{strategy_context}

USER QUESTION:
{user_message}

Provide a helpful, conversational response. Be specific and actionable when discussing trading strategies.
"""
        
        try:
            response = self.model.generate_content(prompt)
            ai_response = response.text.strip()
            
            # Store AI response
            if self.conversation_manager:
                self.conversation_manager.add_ai_message(ai_response, metadata={'action': 'chat'})
            
            return ai_response
            
        except Exception as e:
            print(f"Error in chat: {e}")
            error_response = "I apologize, but I encountered an error processing your message. Could you try rephrasing?"
            if self.conversation_manager:
                self.conversation_manager.add_ai_message(error_response, metadata={'action': 'chat', 'error': str(e)})
            return error_response
    
    def summarize_conversation(self) -> str:
        """
        Generate an AI summary of the current conversation.
        Useful for long conversations to maintain context.
        
        Returns:
            Summary of the conversation
        """
        if not self.conversation_manager:
            return "No conversation session active."
        
        history = self.conversation_manager.get_conversation_history()
        
        if not history:
            return "No conversation history yet."
        
        if self.use_mock:
            return f"Conversation summary: {len(history)} messages exchanged."
        
        # Build conversation text
        conversation_text = ""
        for msg in history:
            conversation_text += f"{msg['role'].upper()}: {msg['content']}\n\n"
        
        prompt = f"""
Provide a concise summary of this trading strategy conversation.
Focus on:
1. What strategy was discussed
2. Key decisions made
3. Important concerns or improvements identified
4. Current state/next steps

CONVERSATION:
{conversation_text}

SUMMARY:
"""
        
        try:
            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            
            # Update the session summary
            self.conversation_manager.update_session_summary(summary)
            
            return summary
            
        except Exception as e:
            print(f"Error summarizing conversation: {e}")
            return f"Could not generate summary. Conversation has {len(history)} messages."
    
    def ask_clarifying_question(self, strategy_dict: Dict[str, Any], missing_info: List[str]) -> str:
        """
        Generate an intelligent clarifying question based on what's missing.
        
        Args:
            strategy_dict: Current strategy structure
            missing_info: List of missing information
            
        Returns:
            A single, concise clarifying question
        """
        if self.use_mock:
            return f"Could you clarify: {', '.join(missing_info[:2])}?"
        
        prompt = f"""
Generate ONE concise clarifying question for this trading strategy.

CURRENT STRATEGY:
{json.dumps(strategy_dict, indent=2)}

MISSING INFORMATION:
{', '.join(missing_info)}

Generate a single, specific question that would help clarify the most critical missing element.
Be conversational and friendly. Return just the question text, nothing else.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating question: {e}")
            return f"Could you please clarify: {missing_info[0]}?"
    
    def _mock_analyze_strategy(self, strategy_text: str) -> Dict[str, Any]:
        """Mock analysis for when API is unavailable."""
        return {
            "extracted_steps": [
                "Step 1: Entry rule (extracted from text)",
                "Step 2: Exit rule (extracted from text)"
            ],
            "strategy_type": "trend-following",
            "risk_level": "medium",
            "instruments": ["AAPL"],
            "timeframe": "daily",
            "missing_elements": ["position_sizing", "stop_loss"],
            "concerns": ["No explicit position sizing rule"],
            "suggestions": [
                "Add position sizing rule",
                "Define stop loss",
                "Specify entry conditions more clearly"
            ],
            "mock_mode": True
        }
    
    def _mock_generate_recommendations(self, strategy_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock recommendations for when API is unavailable."""
        return [
            {
                "title": "Add Position Sizing Rule",
                "description": "Replace fixed sizing with risk-based position sizing",
                "rationale": "Fixed sizing doesn't account for account size changes",
                "priority": 1,
                "category": "sizing",
                "test_params": {"risk_per_trade": "1-2%"}
            },
            {
                "title": "Implement Stop Loss",
                "description": "Add a stop loss rule to limit downside risk",
                "rationale": "Protects capital from large losses",
                "priority": 1,
                "category": "risk",
                "test_params": {"stop_loss_pct": "1-3%"}
            },
            {
                "title": "Backtest with Commission",
                "description": "Test strategy with realistic commission and slippage",
                "rationale": "Ensures profitability after costs",
                "priority": 2,
                "category": "testing",
                "test_params": {"commission": "0.01-0.05%", "slippage": "0.05%"}
            }
        ]
    
    def generate_formatted_validation_response(
        self, 
        strategy_text: str, 
        validation_result: Dict[str, Any],
        use_context: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a custom formatted response for strategy validation.
        Gives AI full freedom to format the response as it sees best.
        
        Args:
            strategy_text: Original strategy text from user
            validation_result: The structured validation result from StrategyValidatorBot
            use_context: Whether to include conversation history
            
        Returns:
            Updated validation_result with optional 'formatted_response' field
        """
        if self.use_mock:
            # In mock mode, let frontend handle formatting
            return validation_result
        
        # Get conversation context if available
        context = self._get_conversation_context() if use_context else ""
        
        # Build AI prompt giving full formatting freedom
        prompt = f"""You are an expert trading strategy analyst. A user has submitted a strategy for validation.
You have complete freedom to format your response in the most helpful way possible.

{context}

USER'S STRATEGY:
{strategy_text}

VALIDATION RESULTS (structured data):
{json.dumps(validation_result, indent=2)}

YOUR TASK:
Provide a clear, helpful response about this strategy validation. You have TWO options:

OPTION 1 (Recommended): Provide a custom markdown-formatted response
- Use emojis, headers, lists, bold/italic text to make it engaging
- Structure the information in the most logical way
- Be conversational and helpful
- Focus on what matters most to the user
- Return JSON with "formatted_response" key containing your markdown text
- IMPORTANT: Ensure all newlines are properly escaped as \\n in the JSON string

Example:
{{
  "formatted_response": "## 🎯 Your EMA Crossover Strategy\\n\\n**Great start!** You've outlined a classic trend-following approach...\\n\\n### ✅ What's Working\\n- Clear entry signal (30/50 EMA cross)\\n- Simple to understand...\\n\\n### ⚠️ Critical Gaps (Fix These First!)\\n1. **Missing stop-loss** - Risk unlimited losses...\\n\\n### 💡 Recommended Next Steps\\n1. Add 10-pip stop below entry\\n2. Define position size (1-2% risk)\\n3. Test on historical data..."
}}

OPTION 2: Let the frontend handle formatting
- Just return empty JSON {{}}
- The structured data will be formatted by the frontend template

Choose whichever approach will best serve the user! If the strategy is complex or there's important context from our conversation, use Option 1 (custom formatting). For simple validations, Option 2 is fine.

CRITICAL: Return ONLY valid JSON. All newlines in the formatted_response must be escaped as \\n, not actual line breaks.
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Try to parse the JSON response with better error handling
            try:
                ai_format = json.loads(response_text)
            except json.JSONDecodeError as json_err:
                # If JSON parsing fails, try to fix it
                print(f"⚠ Initial JSON parse failed: {json_err}")
                print(f"⚠ Error at line {json_err.lineno}, column {json_err.colno}")
                
                # Save the problematic response for debugging
                import os
                import datetime
                debug_dir = os.path.join(os.path.dirname(__file__), 'debug_logs')
                os.makedirs(debug_dir, exist_ok=True)
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                debug_file = os.path.join(debug_dir, f'json_parse_error_{timestamp}.txt')
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(f"JSON Parse Error:\n")
                    f.write(f"Error: {json_err}\n")
                    f.write(f"Line {json_err.lineno}, Column {json_err.colno}\n\n")
                    f.write("Raw Response:\n")
                    f.write(response_text)
                print(f"⚠ Raw response saved to: {debug_file}")
                
                # Try to extract and fix the formatted_response
                try:
                    # Attempt 1: Find the JSON object boundaries and parse more carefully
                    # Sometimes the AI adds extra text before/after the JSON
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}')
                    if start_idx != -1 and end_idx != -1:
                        json_only = response_text[start_idx:end_idx+1]
                        
                        # Try parsing just the JSON portion
                        try:
                            ai_format = json.loads(json_only)
                            print("✓ Successfully parsed JSON after trimming extra text")
                        except json.JSONDecodeError:
                            # Attempt 2: Try to use ast.literal_eval as fallback
                            # This is more forgiving with some syntax issues
                            import ast
                            try:
                                # Replace escaped newlines with actual newlines for literal_eval
                                ai_format = ast.literal_eval(json_only)
                                print("✓ Successfully parsed using ast.literal_eval")
                            except:
                                # Attempt 3: Manual extraction of formatted_response value
                                # This is a last resort for when JSON is truly malformed
                                print("⚠ Attempting manual extraction of formatted_response...")
                                if '"formatted_response"' in response_text:
                                    # Just fall back to empty - let structured response handle it
                                    print("⚠ Found formatted_response key but couldn't parse - using structured fallback")
                                ai_format = {}
                    else:
                        ai_format = {}
                except Exception as extract_err:
                    print(f"⚠ All JSON recovery attempts failed: {extract_err}")
                    ai_format = {}
            
            # If AI provided a formatted_response, add it to validation_result
            if 'formatted_response' in ai_format and ai_format['formatted_response']:
                validation_result['formatted_response'] = ai_format['formatted_response']
                print("✓ AI provided custom formatted response")
            
            # Store in conversation if available
            if self.conversation_manager:
                self.conversation_manager.add_ai_message(
                    ai_format.get('formatted_response', 'Structured validation provided'),
                    metadata={'action': 'formatted_validation'}
                )
            
            return validation_result
            
        except Exception as e:
            print(f"⚠ Error generating formatted response: {e}")
            return validation_result


# Convenience function
def create_gemini_integrator(api_key: str = None) -> GeminiStrategyIntegrator:
    """Create a Gemini integrator instance."""
    return GeminiStrategyIntegrator(api_key)
