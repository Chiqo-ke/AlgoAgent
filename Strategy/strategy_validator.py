"""
Strategy Validator - Main orchestrator for strategy validation and canonicalization
Integrates all modules to provide the StrategyValidatorBot functionality.
Enhanced with Gemini AI for intelligent strategy analysis.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import sys
from pathlib import Path

# Add Strategy directory to path if not already there
STRATEGY_DIR = Path(__file__).parent
if str(STRATEGY_DIR) not in sys.path:
    sys.path.insert(0, str(STRATEGY_DIR))

from canonical_schema import CanonicalStrategy, CANONICAL_STRATEGY_SCHEMA
from input_parser import InputParser, parse_strategy_input
from provenance_tracker import ProvenanceTracker, MetadataManager
from recommendation_engine import RecommendationEngine, generate_recommendations
from guardrails import Guardrails, check_strategy_safety
from gemini_strategy_integrator import GeminiStrategyIntegrator


class StrategyValidatorBot:
    """
    Main strategy validator bot that canonicalizes, classifies, and validates strategies.
    Implements the production-ready specification with AI-enhanced analysis.
    """
    
    def __init__(self, username: str = "user", strict_mode: bool = False, use_gemini: bool = True, session_id: str = None, user=None):
        """
        Initialize the validator bot.
        
        Args:
            username: User identifier for provenance
            strict_mode: If True, raise exceptions on security violations
            use_gemini: If True, use Gemini API for enhanced analysis
            session_id: Optional chat session ID for conversation memory
            user: Optional Django user object for conversation tracking
        """
        self.username = username
        self.strict_mode = strict_mode
        self.current_strategy = None
        self.input_parser = InputParser()
        self.provenance = ProvenanceTracker()
        self.metadata = MetadataManager(username)
        self.guardrails = Guardrails(strict_mode=strict_mode)
        self.recommendation_engine = RecommendationEngine()
        self.session_id = session_id
        self.user = user
        
        # Initialize Gemini integration with conversation context
        self.use_gemini = use_gemini
        self.gemini = GeminiStrategyIntegrator(session_id=session_id, user=user) if use_gemini else None
        if self.gemini and not self.gemini.use_mock:
            print("✓ AI-enhanced strategy analysis enabled")
            if session_id:
                print(f"✓ Conversation memory enabled for session {session_id}")
    
    def process_input(
        self,
        user_input: str,
        input_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Main entry point: process user input and return complete analysis.
        
        Args:
            user_input: Raw strategy text or URL from user
            input_type: Type of input ("auto", "numbered", "freetext", "url")
            
        Returns:
            Complete strategy analysis with canonical JSON
        """
        # Step 1: Safety checks
        if self.guardrails.check_credentials_request(user_input):
            return self._format_error("Security violation: Credential request detected")
        
        if self.guardrails.check_live_trading_request(user_input):
            return {
                "status": "approval_required",
                "message": self.guardrails.require_approval_token("Live Trading")
            }
        
        # Step 2: Parse input
        parsed_input = self.input_parser.parse(user_input, input_type)
        
        # Step 3: Track provenance
        self.provenance.add_user_input(user_input, self.username)
        
        # Handle URL inputs
        if parsed_input["input_type"] == "url":
            return self._handle_url_input(parsed_input)
        
        # Step 4: Create canonical strategy
        title = self._generate_title_from_steps(parsed_input.get("steps", []))
        self.current_strategy = CanonicalStrategy.create_template(title, f"user:{self.username}")
        
        # Step 5: Convert parsed steps to canonical format
        for parsed_step in parsed_input.get("steps", []):
            canonical_step = self._convert_to_canonical_step(parsed_step)
            self.current_strategy.add_step(canonical_step)
        
        # Step 6: Add provenance
        self.current_strategy.data["provenance"] = self.provenance.to_canonical_format()
        
        # Step 7: Classify strategy
        classification = self._classify_strategy(parsed_input)
        self.current_strategy.update_classification(classification)
        
        # Step 8: Run safety checks
        is_safe, issues = self.guardrails.check_strategy(
            self.current_strategy.data,
            user_input
        )
        
        if not is_safe:
            return self._format_error(
                "Strategy contains security violations",
                issues=self.guardrails.get_violations()
            )
        
        # Step 9: Generate recommendations
        self.recommendation_engine.analyze_strategy(self.current_strategy.data)
        
        # Step 10: Set confidence level
        confidence = self._assess_confidence(
            self.current_strategy.data,
            issues
        )
        self.metadata.set_confidence(confidence)
        self.current_strategy.data["metadata"]["confidence"] = confidence
        
        # Step 11: Format output
        return self._format_output()
    
    def _handle_url_input(self, parsed_input: Dict[str, Any]) -> Dict[str, Any]:
        """Handle URL-based input (requires external content fetching)."""
        urls = parsed_input.get("urls", [])
        
        return {
            "status": "url_fetch_required",
            "message": "URL content fetching not yet implemented",
            "urls": urls,
            "next_steps": [
                "Implement content_fetcher.py to fetch URL content",
                "For YouTube/TikTok: fetch transcripts",
                "For web articles: extract main content",
                "Re-run parser with fetched content"
            ]
        }
    
    def _generate_title_from_steps(self, steps: List[Dict[str, Any]]) -> str:
        """Generate a title from parsed steps."""
        if not steps:
            return "Untitled Strategy"
        
        first_step = steps[0]
        title = first_step.get("title", "Strategy")
        
        # Look for indicator names in parameters
        params = first_step.get("params", [])
        if params:
            param_names = [p.get("name", "") for p in params[:2]]
            param_str = "/".join(param_names).upper()
            if param_str:
                title = f"{param_str} {title}"
        
        return title[:100]  # Limit length
    
    def _convert_to_canonical_step(self, parsed_step: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a parsed step to canonical format."""
        canonical_step = {
            "step_id": parsed_step.get("step_id", "s1"),
            "order": parsed_step.get("order", 1),
            "title": parsed_step.get("title", "Untitled step"),
            "trigger": parsed_step.get("trigger", "Condition not specified"),
            "action": parsed_step.get("action", {"type": "enter"})
        }
        
        # Optional fields
        if "condition" in parsed_step:
            canonical_step["condition"] = parsed_step["condition"]
        
        if "exit" in parsed_step:
            canonical_step["exit"] = parsed_step["exit"]
        
        if "params" in parsed_step:
            canonical_step["params"] = parsed_step["params"]
        
        if "rationale" in parsed_step:
            canonical_step["rationale"] = parsed_step["rationale"]
        
        # Add raw text as notes if present
        if "raw_text" in parsed_step:
            canonical_step["notes"] = f"Original: {parsed_step['raw_text']}"
        
        return canonical_step
    
    def _classify_strategy(self, parsed_input: Dict[str, Any]) -> Dict[str, Any]:
        """Classify the strategy type and risk tier."""
        classification = {
            "type": "other",
            "risk_tier": "unknown",
            "primary_instruments": []
        }
        
        # Analyze steps for classification clues
        steps = parsed_input.get("steps", [])
        raw_text = parsed_input.get("raw_input", "").lower()
        
        # Determine strategy type
        if any(word in raw_text for word in ["scalp", "second", "tick"]):
            classification["type"] = "scalping"
        elif any(word in raw_text for word in ["intraday", "day trade", "minutes"]):
            classification["type"] = "intraday"
        elif any(word in raw_text for word in ["swing", "days", "week"]):
            classification["type"] = "swing"
        elif any(word in raw_text for word in ["position", "months", "long-term"]):
            classification["type"] = "position"
        elif any(word in raw_text for word in ["ema", "sma", "moving average", "trend"]):
            classification["type"] = "trend-following"
        elif any(word in raw_text for word in ["mean reversion", "revert", "bollinger"]):
            classification["type"] = "mean-reversion"
        
        # Determine risk tier
        has_stop_loss = any(
            step.get("exit", {}).get("stop_loss") or "stop" in str(step).lower()
            for step in steps
        )
        
        has_dynamic_sizing = any(
            step.get("action", {}).get("size", {}).get("mode") in 
            ["percent_of_equity", "risk_per_trade", "volatility_target"]
            for step in steps
        )
        
        if has_stop_loss and has_dynamic_sizing:
            classification["risk_tier"] = "low"
        elif has_stop_loss or has_dynamic_sizing:
            classification["risk_tier"] = "medium"
        else:
            classification["risk_tier"] = "high"
        
        # Extract instruments
        instruments = set()
        for step in steps:
            instrument = step.get("action", {}).get("instrument")
            if instrument:
                instruments.add(instrument)
        
        classification["primary_instruments"] = list(instruments)
        
        return classification
    
    def _assess_confidence(
        self,
        strategy_dict: Dict[str, Any],
        issues: List[str]
    ) -> str:
        """Assess confidence level of the strategy."""
        steps = strategy_dict.get("steps", [])
        
        if not steps:
            return "low"
        
        # Count complete elements
        complete_count = 0
        total_checks = 5
        
        # Check 1: Has clear triggers
        if all(step.get("trigger") for step in steps):
            complete_count += 1
        
        # Check 2: Has exit rules
        if any(step.get("exit") for step in steps):
            complete_count += 1
        
        # Check 3: Has position sizing
        if any(step.get("action", {}).get("size") for step in steps):
            complete_count += 1
        
        # Check 4: Has parameters
        if any(step.get("params") for step in steps):
            complete_count += 1
        
        # Check 5: No major issues
        if len(issues) == 0:
            complete_count += 1
        
        # Determine confidence
        if complete_count >= 4:
            return "high"
        elif complete_count >= 2:
            return "medium"
        else:
            return "low"
    
    def _format_output(self) -> Dict[str, Any]:
        """Format the complete output response."""
        if not self.current_strategy:
            return self._format_error("No strategy to output")
        
        strategy_dict = self.current_strategy.data
        
        # Get components
        steps_summary = self.current_strategy.get_steps_summary()
        classification_summary = self.current_strategy.get_classification_summary()
        recommendations = self.recommendation_engine.format_recommendations(max_count=5)
        next_actions = self.recommendation_engine.get_next_actions(strategy_dict)
        warnings = self.guardrails.get_warnings()
        
        return {
            "status": "success",
            "canonicalized_steps": steps_summary,
            "classification": classification_summary,
            "classification_detail": strategy_dict.get("classification", {}),
            "recommendations": recommendations,
            "recommendations_list": [r.to_dict() for r in self.recommendation_engine.get_recommendations(5)],
            "confidence": strategy_dict["metadata"]["confidence"],
            "next_actions": next_actions,
            "warnings": warnings,
            "canonical_json": self.current_strategy.to_json(compact=True),
            "canonical_json_formatted": self.current_strategy.to_json(compact=False),
            "metadata": strategy_dict.get("metadata", {}),
            "provenance": strategy_dict.get("provenance", {})
        }
    
    def _format_error(self, message: str, issues: Optional[List[str]] = None) -> Dict[str, Any]:
        """Format an error response."""
        response = {
            "status": "error",
            "message": message
        }
        
        if issues:
            response["issues"] = issues
        
        return response
    
    def get_formatted_output(self) -> str:
        """Get human-readable formatted output."""
        if not self.current_strategy:
            return "No strategy processed yet."
        
        result = self._format_output()
        
        if result["status"] != "success":
            return f"Error: {result.get('message', 'Unknown error')}"
        
        # Format for human reading
        output_parts = []
        
        output_parts.append("=" * 70)
        output_parts.append("1) CANONICALIZED STEPS")
        output_parts.append("=" * 70)
        for step in result["canonicalized_steps"]:
            output_parts.append(step)
        
        output_parts.append("\n" + "=" * 70)
        output_parts.append("2) CLASSIFICATION & META")
        output_parts.append("=" * 70)
        output_parts.append(result["classification"])
        
        output_parts.append("\n" + "=" * 70)
        output_parts.append("3) RECOMMENDATIONS")
        output_parts.append("=" * 70)
        output_parts.append(result["recommendations"])
        
        if result["warnings"]:
            output_parts.append("\n⚠️  WARNINGS:")
            for warning in result["warnings"]:
                output_parts.append(f"  - {warning}")
        
        output_parts.append("\n" + "=" * 70)
        output_parts.append("4) CONFIDENCE & NEXT ACTIONS")
        output_parts.append("=" * 70)
        output_parts.append(f"Confidence: {result['confidence'].upper()}")
        output_parts.append("\nNext Actions:")
        for action in result["next_actions"]:
            output_parts.append(f"  [{action}]")
        
        output_parts.append("\n" + "=" * 70)
        output_parts.append("5) JSON PAYLOAD (compact)")
        output_parts.append("=" * 70)
        output_parts.append(result["canonical_json"][:500] + "...")
        
        return "\n".join(output_parts)


def validate_strategy(
    user_input: str,
    username: str = "user",
    input_type: str = "auto"
) -> Dict[str, Any]:
    """
    Convenience function to validate a strategy.
    
    Args:
        user_input: Raw strategy text from user
        username: User identifier
        input_type: Input type ("auto", "numbered", "freetext", "url")
        
    Returns:
        Complete validation result
    """
    bot = StrategyValidatorBot(username=username)
    return bot.process_input(user_input, input_type)


if __name__ == "__main__":
    # Test the validator bot
    test_input = """
    Buy 100 shares when 50 EMA crosses above 200 EMA. 
    Place stop at 1% below entry. Take profit at 2%. 
    No position sizing rule.
    """
    
    print("Processing strategy input...")
    print("=" * 70)
    
    bot = StrategyValidatorBot(username="test_user")
    result = bot.process_input(test_input)
    
    if result["status"] == "success":
        print(bot.get_formatted_output())
    else:
        print(f"Error: {result.get('message')}")
        if "issues" in result:
            for issue in result["issues"]:
                print(f"  - {issue}")
