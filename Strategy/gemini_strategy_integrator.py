"""
Gemini Strategy Integrator - AI-powered strategy analysis using Gemini API
Enhances strategy validation with natural language understanding and recommendations.
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
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize Gemini integrator with API key.
        
        Args:
            api_key: Gemini API key (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.client = None
        self.model = None
        self.use_mock = False
        
        if self.api_key and self.api_key != 'your_gemini_api_key_here':
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.client = genai
                print("✓ Gemini API initialized successfully")
            except ImportError:
                print("⚠ google-generativeai not installed. Run: pip install google-generativeai")
                self.use_mock = True
            except Exception as e:
                print(f"⚠ Gemini API initialization failed: {e}")
                self.use_mock = True
        else:
            print("⚠ No valid Gemini API key found - Using mock mode")
            self.use_mock = True
    
    def analyze_strategy_text(self, strategy_text: str) -> Dict[str, Any]:
        """
        Analyze raw strategy text using Gemini to extract structure and insights.
        
        Args:
            strategy_text: Raw strategy description from user
            
        Returns:
            Analysis including extracted steps, type, risk level, and suggestions
        """
        if self.use_mock:
            return self._mock_analyze_strategy(strategy_text)
        
        prompt = f"""
Analyze this trading strategy and provide a structured analysis:

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
            return analysis
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return text analysis
            return {
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


# Convenience function
def create_gemini_integrator(api_key: str = None) -> GeminiStrategyIntegrator:
    """Create a Gemini integrator instance."""
    return GeminiStrategyIntegrator(api_key)
