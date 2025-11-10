"""
Recommendation Engine - Generate prioritized recommendations for trading strategies
Analyzes strategies and suggests improvements, tests, and parameter ranges.
"""

from typing import List, Dict, Any, Optional, Tuple
import re


class Recommendation:
    """Represents a single recommendation."""
    
    def __init__(
        self,
        title: str,
        description: str,
        rationale: str,
        priority: int = 2,
        category: str = "general",
        test_params: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a recommendation.
        
        Args:
            title: Short recommendation title
            description: Detailed description
            rationale: Why this is recommended
            priority: 1=high, 2=medium, 3=low
            category: Category (risk, sizing, testing, parameters, etc.)
            test_params: Suggested test parameters
        """
        self.title = title
        self.description = description
        self.rationale = rationale
        self.priority = priority
        self.category = category
        self.test_params = test_params or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "priority": self.priority,
            "category": self.category,
            "test_params": self.test_params
        }
    
    def format_for_output(self, index: int) -> str:
        """Format for human-readable output."""
        output = f"{index}. {self.description}"
        output += f"\n   Why: {self.rationale}"
        if self.test_params:
            test_str = ", ".join(f"{k}: {v}" for k, v in self.test_params.items())
            output += f"\n   Test: {test_str}"
        return output


class RecommendationEngine:
    """Generate recommendations for trading strategies."""
    
    def __init__(self):
        """Initialize the recommendation engine."""
        self.recommendations = []
    
    def analyze_strategy(self, strategy_dict: Dict[str, Any]) -> List[Recommendation]:
        """
        Analyze a strategy and generate recommendations.
        
        Args:
            strategy_dict: Parsed strategy dictionary
            
        Returns:
            List of recommendations
        """
        self.recommendations = []
        
        # Analyze different aspects
        self._analyze_position_sizing(strategy_dict)
        self._analyze_risk_controls(strategy_dict)
        self._analyze_parameters(strategy_dict)
        self._analyze_exit_rules(strategy_dict)
        self._analyze_reentry_rules(strategy_dict)
        self._analyze_cost_assumptions(strategy_dict)
        self._analyze_testing_needs(strategy_dict)
        
        # Sort by priority
        self.recommendations.sort(key=lambda x: x.priority)
        
        return self.recommendations
    
    def _analyze_position_sizing(self, strategy: Dict[str, Any]) -> None:
        """Check for position sizing issues."""
        steps = strategy.get("steps", [])
        
        for step in steps:
            action = step.get("action", {})
            if action.get("type") in ["enter", "modify"]:
                size = action.get("size", {})
                
                if not size:
                    self.recommendations.append(Recommendation(
                        title="Missing position size",
                        description="Add position sizing rule",
                        rationale="Without sizing, strategy cannot be executed",
                        priority=1,
                        category="sizing"
                    ))
                elif size.get("mode") == "fixed":
                    self.recommendations.append(Recommendation(
                        title="Replace fixed size with dynamic sizing",
                        description="Replace fixed size with percent_of_equity or risk_per_trade",
                        rationale="Fixed size ignores changing account value and risk",
                        priority=1,
                        category="sizing",
                        test_params={
                            "percent_of_equity": "1-5%",
                            "risk_per_trade": "0.5-2%"
                        }
                    ))
    
    def _analyze_risk_controls(self, strategy: Dict[str, Any]) -> None:
        """Check for risk control measures."""
        steps = strategy.get("steps", [])
        
        has_stop_loss = False
        has_take_profit = False
        has_max_positions = False
        
        for step in steps:
            exit_rule = step.get("exit", {})
            risk_controls = step.get("risk_controls", {})
            
            if isinstance(exit_rule, dict):
                if exit_rule.get("stop_loss"):
                    has_stop_loss = True
                if exit_rule.get("take_profit"):
                    has_take_profit = True
            elif isinstance(exit_rule, str):
                if "stop" in exit_rule.lower():
                    has_stop_loss = True
                if "profit" in exit_rule.lower() or "target" in exit_rule.lower():
                    has_take_profit = True
            
            if risk_controls.get("max_positions"):
                has_max_positions = True
        
        if not has_stop_loss:
            self.recommendations.append(Recommendation(
                title="Add stop-loss rule",
                description="Define stop-loss for risk management",
                rationale="Stop-loss prevents unlimited losses",
                priority=1,
                category="risk",
                test_params={
                    "stop_loss_pct": "0.5-3%",
                    "atr_multiple": "1-3x ATR"
                }
            ))
        
        if not has_take_profit:
            self.recommendations.append(Recommendation(
                title="Add take-profit rule",
                description="Define take-profit target or trailing stop",
                rationale="Locks in profits and improves risk/reward",
                priority=2,
                category="risk",
                test_params={
                    "take_profit_pct": "1-5%",
                    "risk_reward_ratio": "1.5-3.0"
                }
            ))
        
        if not has_max_positions:
            self.recommendations.append(Recommendation(
                title="Add maximum position limit",
                description="Set max concurrent positions to control risk",
                rationale="Prevents over-concentration and correlation risk",
                priority=2,
                category="risk",
                test_params={
                    "max_positions": "1-5"
                }
            ))
    
    def _analyze_parameters(self, strategy: Dict[str, Any]) -> None:
        """Check for parameter optimization opportunities."""
        steps = strategy.get("steps", [])
        
        all_params = []
        for step in steps:
            params = step.get("params", [])
            all_params.extend(params)
        
        if all_params:
            # Check if parameters have ranges
            params_without_range = [p for p in all_params if not p.get("range")]
            
            if params_without_range:
                param_names = ", ".join(p.get("name", "unknown") for p in params_without_range[:3])
                self.recommendations.append(Recommendation(
                    title="Define parameter ranges",
                    description=f"Add optimization ranges for: {param_names}",
                    rationale="Parameter ranges enable systematic optimization",
                    priority=2,
                    category="parameters",
                    test_params={
                        "method": "grid_search or walk_forward",
                        "validation": "out_of_sample"
                    }
                ))
    
    def _analyze_exit_rules(self, strategy: Dict[str, Any]) -> None:
        """Analyze exit rule completeness."""
        steps = strategy.get("steps", [])
        
        for step in steps:
            exit_rule = step.get("exit")
            
            if exit_rule and isinstance(exit_rule, dict):
                sl = exit_rule.get("stop_loss", "")
                tp = exit_rule.get("take_profit", "")
                
                # Check if stops are too tight
                if isinstance(sl, str):
                    sl_match = re.search(r'(\d+(?:\.\d+)?)\s*%', sl)
                    if sl_match and float(sl_match.group(1)) < 0.5:
                        self.recommendations.append(Recommendation(
                            title="Review stop-loss tightness",
                            description=f"Stop-loss at {sl_match.group(1)}% may be too tight",
                            rationale="Very tight stops increase false exits due to noise",
                            priority=2,
                            category="risk",
                            test_params={
                                "stop_loss_range": "0.5-3%",
                                "consider_volatility": "ATR-based stops"
                            }
                        ))
    
    def _analyze_reentry_rules(self, strategy: Dict[str, Any]) -> None:
        """Check for re-entry and cooldown rules."""
        steps = strategy.get("steps", [])
        
        # Look for cooldown or re-entry conditions
        has_reentry_rule = False
        for step in steps:
            condition = step.get("condition", "")
            if isinstance(condition, str):
                if any(word in condition.lower() for word in ["cooldown", "wait", "after", "no position"]):
                    has_reentry_rule = True
                    break
        
        if not has_reentry_rule:
            self.recommendations.append(Recommendation(
                title="Add re-entry cooldown",
                description="Add cooldown period or re-entry condition to prevent overtrading",
                rationale="Prevents immediate re-entry after stop-out",
                priority=2,
                category="logic",
                test_params={
                    "cooldown_minutes": "1-60",
                    "cooldown_bars": "1-10"
                }
            ))
    
    def _analyze_cost_assumptions(self, strategy: Dict[str, Any]) -> None:
        """Check for cost modeling."""
        # Always recommend modeling costs for first analysis
        self.recommendations.append(Recommendation(
            title="Model slippage and commissions",
            description="Include realistic transaction costs in backtests",
            rationale="Costs significantly impact profitability, especially with tight stops",
            priority=1,
            category="testing",
            test_params={
                "slippage": "0.05-0.5% per trade",
                "commission": "$0.005-$0.01 per share or 0.1% per trade"
            }
        ))
    
    def _analyze_testing_needs(self, strategy: Dict[str, Any]) -> None:
        """Generate testing recommendations."""
        classification = strategy.get("classification", {})
        strategy_type = classification.get("type", "unknown")
        
        # Determine recommended timeframe
        timeframe_map = {
            "scalping": "1s-1m",
            "intraday": "1m-5m",
            "swing": "5m-1h",
            "position": "1h-1d"
        }
        recommended_tf = timeframe_map.get(strategy_type, "5m-1h")
        
        self.recommendations.append(Recommendation(
            title="Run walk-forward analysis",
            description="Backtest with walk-forward validation to assess robustness",
            rationale="Walk-forward prevents overfitting and validates out-of-sample performance",
            priority=1,
            category="testing",
            test_params={
                "data_frequency": recommended_tf,
                "in_sample_period": "12 months",
                "out_sample_period": "3 months",
                "min_trades": ">=100"
            }
        ))
        
        self.recommendations.append(Recommendation(
            title="Parameter sensitivity analysis",
            description="Test parameter ranges to find robust settings",
            rationale="Ensures strategy isn't over-optimized to specific parameter values",
            priority=2,
            category="testing",
            test_params={
                "method": "grid_search +/- 20% around defaults",
                "metrics": "Sharpe, max_drawdown, win_rate"
            }
        ))
    
    def get_recommendations(self, max_count: Optional[int] = None) -> List[Recommendation]:
        """Get recommendations, optionally limited."""
        if max_count:
            return self.recommendations[:max_count]
        return self.recommendations
    
    def format_recommendations(self, max_count: Optional[int] = None) -> str:
        """Format recommendations for output."""
        recs = self.get_recommendations(max_count)
        
        if not recs:
            return "No specific recommendations at this time."
        
        output_lines = []
        for i, rec in enumerate(recs, 1):
            output_lines.append(rec.format_for_output(i))
        
        return "\n\n".join(output_lines)
    
    def get_next_actions(self, strategy: Dict[str, Any]) -> List[str]:
        """Generate list of next actions user can take."""
        actions = []
        
        # Check strategy completeness
        steps = strategy.get("steps", [])
        if not steps:
            return ["Provide strategy steps"]
        
        # Determine available actions
        has_params = any(step.get("params") for step in steps)
        has_risk_controls = any(step.get("risk_controls") or step.get("exit") for step in steps)
        
        if has_params and has_risk_controls:
            actions.append("Run quick backtest")
            actions.append("Run parameter sweep")
        
        if len(self.recommendations) > 0:
            actions.append("Review recommendations")
        
        # Check if there are ambiguities
        classification = strategy.get("classification", {})
        if classification.get("risk_tier") == "unknown":
            actions.append("Ask clarifying Q: 'What is your risk tolerance?'")
        
        # Always offer code generation as final step
        actions.append("Approve -> Generate code")
        
        return actions


def generate_recommendations(strategy_dict: Dict[str, Any]) -> RecommendationEngine:
    """
    Convenience function to generate recommendations.
    
    Args:
        strategy_dict: Parsed strategy dictionary
        
    Returns:
        RecommendationEngine with recommendations
    """
    engine = RecommendationEngine()
    engine.analyze_strategy(strategy_dict)
    return engine


if __name__ == "__main__":
    # Test recommendation engine
    test_strategy = {
        "classification": {"type": "trend-following", "risk_tier": "medium"},
        "steps": [
            {
                "step_id": "s1",
                "order": 1,
                "title": "Entry",
                "trigger": "50 EMA crosses 200 EMA",
                "action": {
                    "type": "enter",
                    "order_type": "market",
                    "size": {"mode": "fixed", "value": 100}
                },
                "exit": {
                    "stop_loss": "1%",
                    "take_profit": "2%"
                },
                "params": [
                    {"name": "ema_fast", "value": 50},
                    {"name": "ema_slow", "value": 200}
                ]
            }
        ]
    }
    
    engine = generate_recommendations(test_strategy)
    
    print("=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    print(engine.format_recommendations())
    
    print("\n\n" + "=" * 60)
    print("NEXT ACTIONS")
    print("=" * 60)
    for action in engine.get_next_actions(test_strategy):
        print(f"  [{action}]")
