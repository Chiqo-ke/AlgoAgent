"""
Test Suite for Strategy Validator
Comprehensive tests for all modules in the strategy validation system.
"""

import pytest
import json
from datetime import datetime

# Import modules to test
from canonical_schema import CanonicalStrategy, validate_strategy_json, create_minimal_example
from input_parser import InputParser, parse_strategy_input
from provenance_tracker import ProvenanceTracker, MetadataManager
from recommendation_engine import RecommendationEngine, generate_recommendations
from guardrails import Guardrails, check_strategy_safety, SecurityViolation
from strategy_validator import StrategyValidatorBot, validate_strategy
from examples import get_all_examples, get_safe_examples, get_dangerous_examples


class TestCanonicalSchema:
    """Test the canonical schema module."""
    
    def test_create_minimal_example(self):
        """Test creating the minimal example from spec."""
        example = create_minimal_example()
        assert example.data["strategy_id"] == "strat-20251014-001"
        assert example.data["title"] == "EMA Crossover Simple"
        assert len(example.data["steps"]) == 1
    
    def test_validate_minimal_example(self):
        """Test validation of minimal example."""
        example = create_minimal_example()
        assert example.validate() is True
    
    def test_create_template(self):
        """Test creating a strategy template."""
        strategy = CanonicalStrategy.create_template("Test Strategy", "test_user")
        assert strategy.data["title"] == "Test Strategy"
        assert strategy.data["metadata"]["created_by"] == "test_user"
        assert len(strategy.data["steps"]) == 0
    
    def test_add_step(self):
        """Test adding steps to a strategy."""
        strategy = CanonicalStrategy.create_template("Test", "user")
        step = {
            "step_id": "s1",
            "order": 1,
            "title": "Test step",
            "trigger": "Test trigger",
            "action": {"type": "enter"}
        }
        strategy.add_step(step)
        assert len(strategy.data["steps"]) == 1
        assert strategy.data["steps"][0]["title"] == "Test step"
    
    def test_json_serialization(self):
        """Test JSON serialization."""
        example = create_minimal_example()
        json_str = example.to_json()
        assert isinstance(json_str, str)
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["title"] == "EMA Crossover Simple"
    
    def test_compact_json(self):
        """Test compact JSON output."""
        example = create_minimal_example()
        compact = example.to_json(compact=True)
        normal = example.to_json(compact=False)
        assert len(compact) < len(normal)


class TestInputParser:
    """Test the input parser module."""
    
    def test_detect_numbered_input(self):
        """Test detection of numbered input."""
        parser = InputParser()
        text = "1. Buy when EMA crosses\n2. Sell at target"
        input_type = parser._detect_input_type(text)
        assert input_type == "numbered"
    
    def test_detect_freetext_input(self):
        """Test detection of freetext input."""
        parser = InputParser()
        text = "Buy 100 shares when price goes up"
        input_type = parser._detect_input_type(text)
        assert input_type == "freetext"
    
    def test_detect_url_input(self):
        """Test detection of URL input."""
        parser = InputParser()
        text = "Check this strategy: https://example.com/strategy"
        input_type = parser._detect_input_type(text)
        assert input_type == "url"
    
    def test_parse_numbered_steps(self):
        """Test parsing numbered steps."""
        text = """
        1. Buy 100 shares when 50 EMA crosses above 200 EMA
        2. Set stop loss at 1% below entry
        3. Take profit at 2% above entry
        """
        result = parse_strategy_input(text, "numbered")
        assert result["input_type"] == "numbered"
        assert len(result["steps"]) >= 1
    
    def test_parse_freetext(self):
        """Test parsing freetext."""
        text = "Buy 100 shares when price breaks above resistance. Set stop at 2%."
        result = parse_strategy_input(text, "freetext")
        assert result["input_type"] == "freetext"
        assert len(result["steps"]) >= 1
    
    def test_extract_size_fixed(self):
        """Test extracting fixed size."""
        parser = InputParser()
        text = "Buy 100 shares"
        size = parser._extract_size(text)
        assert size is not None
        assert size["mode"] == "fixed"
        assert size["value"] == 100
    
    def test_extract_size_percent(self):
        """Test extracting percentage size."""
        parser = InputParser()
        text = "Risk 5% of equity"
        size = parser._extract_size(text)
        assert size is not None
        assert size["mode"] == "percent_of_equity"
        assert size["value"] == 5.0
    
    def test_extract_stop_loss(self):
        """Test extracting stop loss."""
        parser = InputParser()
        text = "Set stop loss at 2% below entry"
        exit_rule = parser._extract_exit_rule(text)
        assert exit_rule is not None
        assert "stop_loss" in exit_rule
    
    def test_extract_take_profit(self):
        """Test extracting take profit."""
        parser = InputParser()
        text = "Take profit at 3%"
        exit_rule = parser._extract_exit_rule(text)
        assert exit_rule is not None
        assert "take_profit" in exit_rule


class TestProvenanceTracker:
    """Test the provenance tracker module."""
    
    def test_add_user_input(self):
        """Test adding user input source."""
        tracker = ProvenanceTracker()
        source = tracker.add_user_input("Test strategy", "test_user")
        assert source["type"] == "user_input"
        assert source["author"] == "test_user"
        assert "fetched_at" in source
    
    def test_add_web_article(self):
        """Test adding web article source."""
        tracker = ProvenanceTracker()
        source = tracker.add_web_article(
            url="https://example.com/article",
            author="John Doe",
            snippet="Test snippet"
        )
        assert source["type"] == "web_article"
        assert source["url"] == "https://example.com/article"
    
    def test_detect_youtube_url(self):
        """Test YouTube URL detection."""
        tracker = ProvenanceTracker()
        source_type = tracker._detect_source_type_from_url("https://youtube.com/watch?v=abc")
        assert source_type == "youtube"
    
    def test_detect_tiktok_url(self):
        """Test TikTok URL detection."""
        tracker = ProvenanceTracker()
        source_type = tracker._detect_source_type_from_url("https://tiktok.com/@user/video/123")
        assert source_type == "tiktok"
    
    def test_metadata_manager(self):
        """Test metadata manager."""
        meta = MetadataManager("test_user")
        assert meta.metadata["created_by"] == "test_user"
        assert "created_at" in meta.metadata
        assert meta.metadata["confidence"] == "low"
    
    def test_set_confidence(self):
        """Test setting confidence level."""
        meta = MetadataManager("user")
        meta.set_confidence("high")
        assert meta.metadata["confidence"] == "high"


class TestRecommendationEngine:
    """Test the recommendation engine module."""
    
    def test_analyze_fixed_size(self):
        """Test recommendation for fixed size."""
        strategy = {
            "steps": [{
                "action": {
                    "type": "enter",
                    "size": {"mode": "fixed", "value": 100}
                }
            }]
        }
        engine = RecommendationEngine()
        engine.analyze_strategy(strategy)
        
        # Should recommend replacing fixed size
        recs = engine.get_recommendations()
        assert any("fixed size" in r.description.lower() for r in recs)
    
    def test_analyze_missing_stop_loss(self):
        """Test recommendation for missing stop loss."""
        strategy = {
            "steps": [{
                "action": {"type": "enter"}
            }]
        }
        engine = RecommendationEngine()
        engine.analyze_strategy(strategy)
        
        # Should recommend adding stop loss
        recs = engine.get_recommendations()
        assert any("stop" in r.description.lower() for r in recs)
    
    def test_priority_sorting(self):
        """Test that recommendations are sorted by priority."""
        strategy = {
            "steps": [{
                "action": {
                    "type": "enter",
                    "size": {"mode": "fixed", "value": 100}
                }
            }]
        }
        engine = generate_recommendations(strategy)
        recs = engine.get_recommendations()
        
        # Check priorities are in order
        priorities = [r.priority for r in recs]
        assert priorities == sorted(priorities)
    
    def test_get_next_actions(self):
        """Test next actions generation."""
        strategy = {
            "steps": [{
                "trigger": "test",
                "action": {"type": "enter"},
                "params": [{"name": "test", "value": 10}],
                "exit": {"stop_loss": "1%"}
            }]
        }
        engine = RecommendationEngine()
        engine.analyze_strategy(strategy)
        actions = engine.get_next_actions(strategy)
        
        assert len(actions) > 0
        assert "Approve -> Generate code" in actions


class TestGuardrails:
    """Test the guardrails module."""
    
    def test_detect_scam_keywords(self):
        """Test detection of scam keywords."""
        guardrails = Guardrails(strict_mode=False)
        text = "This is a guaranteed profit pump and dump strategy"
        strategy = {"steps": []}
        
        is_safe, issues = guardrails.check_strategy(strategy, text)
        assert not is_safe
        assert len(guardrails.get_violations()) > 0
    
    def test_safe_strategy(self):
        """Test a safe strategy passes."""
        guardrails = Guardrails(strict_mode=False)
        strategy = {
            "steps": [{
                "action": {"size": {"mode": "risk_per_trade", "value": 1}},
                "exit": {"stop_loss": "2%"}
            }],
            "provenance": {"sources": [{"url": "https://example.com"}]}
        }
        
        is_safe, issues = guardrails.check_strategy(strategy, "Buy when EMA crosses")
        assert is_safe
    
    def test_excessive_leverage_warning(self):
        """Test warning for excessive leverage."""
        guardrails = Guardrails(strict_mode=False)
        strategy = {"steps": [], "leverage": "20x"}
        
        guardrails.check_strategy(strategy, "Use 20x leverage")
        warnings = guardrails.get_warnings()
        assert len(warnings) > 0
    
    def test_credential_request_detection(self):
        """Test detection of credential requests."""
        guardrails = Guardrails()
        text = "Please enter your API key"
        assert guardrails.check_credentials_request(text) is True
    
    def test_live_trading_detection(self):
        """Test detection of live trading requests."""
        guardrails = Guardrails()
        text = "Execute this strategy live with real money"
        assert guardrails.check_live_trading_request(text) is True


class TestStrategyValidator:
    """Test the main strategy validator."""
    
    def test_process_simple_input(self):
        """Test processing simple text input."""
        bot = StrategyValidatorBot(username="test_user")
        result = bot.process_input("Buy 100 shares when EMA crosses")
        
        assert result["status"] == "success"
        assert "canonicalized_steps" in result
        assert "recommendations" in result
        assert "canonical_json" in result
    
    def test_url_input_handling(self):
        """Test URL input handling."""
        bot = StrategyValidatorBot(username="test_user")
        result = bot.process_input("https://youtube.com/watch?v=abc123")
        
        assert result["status"] == "url_fetch_required"
        assert "urls" in result
    
    def test_dangerous_input_blocked(self):
        """Test dangerous input is blocked."""
        bot = StrategyValidatorBot(username="test_user", strict_mode=False)
        result = bot.process_input("Guaranteed profit pump and dump with no risk!")
        
        assert result["status"] == "error"
        assert "issues" in result or "message" in result
    
    def test_classification(self):
        """Test strategy classification."""
        bot = StrategyValidatorBot(username="test_user")
        result = bot.process_input("Scalping strategy: buy on breakout, exit within seconds")
        
        if result["status"] == "success":
            classification = result.get("classification_detail", {})
            # Should be classified as scalping
            assert classification.get("type") in ["scalping", "intraday", "other"]
    
    def test_confidence_assessment(self):
        """Test confidence assessment."""
        bot = StrategyValidatorBot(username="test_user")
        result = bot.process_input("""
        Buy when 50 EMA crosses 200 EMA.
        Risk 1% per trade.
        Stop loss at 2%.
        Take profit at 4%.
        """)
        
        if result["status"] == "success":
            confidence = result.get("confidence")
            assert confidence in ["low", "medium", "high"]


class TestExamples:
    """Test using the example strategies."""
    
    def test_all_safe_examples(self):
        """Test all safe examples process without errors."""
        safe_examples = get_safe_examples()
        bot = StrategyValidatorBot(username="test_user")
        
        for example in safe_examples:
            result = bot.process_input(example["input"])
            # URL examples will have different status
            if example["should_pass"] == "url":
                assert result["status"] in ["url_fetch_required", "success"]
            else:
                assert result["status"] == "success", f"Example {example['id']} failed"
    
    def test_dangerous_example_blocked(self):
        """Test dangerous examples are blocked."""
        dangerous_examples = get_dangerous_examples()
        bot = StrategyValidatorBot(username="test_user", strict_mode=False)
        
        for example in dangerous_examples:
            result = bot.process_input(example["input"])
            assert result["status"] == "error", f"Dangerous example {example['id']} not blocked"


class TestIntegration:
    """Integration tests for the complete system."""
    
    def test_end_to_end_flow(self):
        """Test complete end-to-end flow."""
        input_text = """
        1. Buy 100 shares of AAPL when 20 EMA crosses above 50 EMA
        2. Set stop loss at 2% below entry
        3. Take profit at 4% above entry
        4. Maximum 3 concurrent positions
        """
        
        # Process through validator
        result = validate_strategy(input_text, username="test_user")
        
        # Verify all expected fields
        assert result["status"] == "success"
        assert len(result["canonicalized_steps"]) > 0
        assert "classification" in result
        assert "recommendations" in result
        assert "next_actions" in result
        assert "canonical_json" in result
        
        # Verify JSON is valid
        json_data = json.loads(result["canonical_json"])
        assert "strategy_id" in json_data
        assert "steps" in json_data
        assert "metadata" in json_data
    
    def test_formatted_output(self):
        """Test formatted output generation."""
        bot = StrategyValidatorBot(username="test_user")
        bot.process_input("Buy when price breaks resistance. Stop at 1%.")
        
        formatted = bot.get_formatted_output()
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert "CANONICALIZED STEPS" in formatted
        assert "RECOMMENDATIONS" in formatted


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
