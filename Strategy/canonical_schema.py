"""
Canonical Strategy Schema - JSON Schema and validation for trading strategies
Based on the production-ready specification for canonicalized strategy format.
"""

import json
import jsonschema
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

# Core JSON Schema for Canonical Strategy
CANONICAL_STRATEGY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "CanonicalStrategy",
    "type": "object",
    "required": ["strategy_id", "version", "title", "steps", "metadata"],
    "properties": {
        "strategy_id": {
            "type": "string", 
            "description": "UUID or unique ID for the strategy"
        },
        "version": {
            "type": "string", 
            "description": "Semantic version or timestamp"
        },
        "title": {"type": "string"},
        "description": {
            "type": "string", 
            "description": "Short human summary"
        },
        "classification": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string", 
                    "enum": [
                        "scalping", "intraday", "swing", "position", 
                        "market-neutral", "stat-arb", "trend-following", 
                        "mean-reversion", "other"
                    ]
                },
                "risk_tier": {
                    "type": "string", 
                    "enum": ["low", "medium", "high", "unknown"]
                },
                "primary_instruments": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["step_id", "order", "title", "trigger", "action"],
                "properties": {
                    "step_id": {"type": "string"},
                    "order": {"type": "integer"},
                    "title": {"type": "string"},
                    "trigger": {
                        "type": "string", 
                        "description": "What event or signal starts this step"
                    },
                    "condition": {
                        "type": ["string", "object"],
                        "description": "Optional structured condition"
                    },
                    "action": {
                        "type": "object",
                        "required": ["type"],
                        "properties": {
                            "type": {
                                "type": "string", 
                                "enum": [
                                    "enter", "exit", "modify", "hold", 
                                    "cancel", "notify", "wait"
                                ]
                            },
                            "order_type": {
                                "type": "string", 
                                "enum": [
                                    "market", "limit", "stop", "stop_limit", 
                                    "conditional", "other"
                                ]
                            },
                            "instrument": {"type": "string"},
                            "size": {
                                "type": "object",
                                "properties": {
                                    "mode": {
                                        "type": "string", 
                                        "enum": [
                                            "fixed", "percent_of_equity", 
                                            "volatility_target", "risk_per_trade", "other"
                                        ]
                                    },
                                    "value": {}
                                }
                            },
                            "price_offset": {"type": "number"},
                            "notes": {"type": "string"}
                        }
                    },
                    "exit": {
                        "type": ["string", "object"],
                        "description": "Stop, take-profit, time-based exit, or complex exit rules"
                    },
                    "risk_controls": {
                        "type": "object",
                        "properties": {
                            "stop_loss": {},
                            "take_profit": {},
                            "max_drawdown_per_trade": {},
                            "max_positions": {"type": "integer"}
                        }
                    },
                    "params": {
                        "type": "array",
                        "items": {
                            "type": "object", 
                            "properties": {
                                "name": {"type": "string"},
                                "value": {},
                                "range": {},
                                "comment": {"type": "string"}
                            }
                        }
                    },
                    "rationale": {"type": "string"},
                    "notes": {"type": "string"}
                }
            }
        },
        "provenance": {
            "type": "object",
            "properties": {
                "sources": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "type": {
                                "type": "string", 
                                "enum": [
                                    "user_input", "web_article", "youtube", 
                                    "tiktok", "social_post", "pdf", "other"
                                ]
                            },
                            "author": {"type": "string"},
                            "fetched_at": {"type": "string", "format": "date-time"},
                            "snippet": {"type": "string"}
                        }
                    }
                }
            }
        },
        "metadata": {
            "type": "object",
            "required": ["created_at", "created_by"],
            "properties": {
                "created_at": {"type": "string", "format": "date-time"},
                "created_by": {"type": "string"},
                "last_updated": {"type": "string", "format": "date-time"},
                "notes": {"type": "string"},
                "confidence": {
                    "type": "string", 
                    "enum": ["low", "medium", "high"]
                }
            }
        }
    }
}


class CanonicalStrategy:
    """
    Represents a canonicalized trading strategy with validation and utility methods.
    """
    
    def __init__(self, strategy_data: Dict[str, Any]):
        """Initialize with strategy data and validate against schema."""
        self.data = strategy_data
        self.validate()
    
    def validate(self) -> bool:
        """Validate the strategy data against the canonical schema."""
        try:
            jsonschema.validate(self.data, CANONICAL_STRATEGY_SCHEMA)
            return True
        except jsonschema.ValidationError as e:
            raise ValueError(f"Strategy validation failed: {e.message}")
    
    @classmethod
    def create_template(cls, title: str, created_by: str) -> 'CanonicalStrategy':
        """Create a minimal template strategy structure."""
        template = {
            "strategy_id": f"strat-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}",
            "version": "0.1.0",
            "title": title,
            "description": "",
            "classification": {
                "type": "other",
                "risk_tier": "unknown",
                "primary_instruments": []
            },
            "steps": [],
            "provenance": {
                "sources": []
            },
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "created_by": created_by,
                "last_updated": datetime.now().isoformat(),
                "confidence": "low"
            }
        }
        return cls(template)
    
    def add_step(self, step_data: Dict[str, Any]) -> None:
        """Add a step to the strategy."""
        if "step_id" not in step_data:
            step_data["step_id"] = f"s{len(self.data['steps']) + 1}"
        if "order" not in step_data:
            step_data["order"] = len(self.data['steps']) + 1
        
        self.data["steps"].append(step_data)
        self.update_timestamp()
    
    def add_source(self, source_data: Dict[str, Any]) -> None:
        """Add a provenance source."""
        if "sources" not in self.data["provenance"]:
            self.data["provenance"]["sources"] = []
        
        self.data["provenance"]["sources"].append(source_data)
        self.update_timestamp()
    
    def update_classification(self, classification: Dict[str, Any]) -> None:
        """Update strategy classification."""
        self.data["classification"] = {**self.data.get("classification", {}), **classification}
        self.update_timestamp()
    
    def update_timestamp(self) -> None:
        """Update the last_updated timestamp."""
        self.data["metadata"]["last_updated"] = datetime.now().isoformat()
    
    def to_json(self, compact: bool = False) -> str:
        """Convert to JSON string."""
        if compact:
            return json.dumps(self.data, separators=(',', ':'))
        return json.dumps(self.data, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the underlying dictionary."""
        return self.data.copy()
    
    def get_steps_summary(self) -> List[str]:
        """Get human-readable summary of steps."""
        summaries = []
        for step in self.data["steps"]:
            action_type = step["action"].get("type", "unknown")
            summaries.append(f"{step['order']}. {step['title']} — {step['trigger']} → {action_type}")
        return summaries
    
    def get_classification_summary(self) -> str:
        """Get classification summary."""
        cls = self.data.get("classification", {})
        return f"Type: {cls.get('type', 'unknown')}, Risk: {cls.get('risk_tier', 'unknown')}, Instruments: {', '.join(cls.get('primary_instruments', []))}"


# Validation utilities
def validate_strategy_json(strategy_json: str) -> bool:
    """Validate a JSON string against the canonical schema."""
    try:
        strategy_data = json.loads(strategy_json)
        jsonschema.validate(strategy_data, CANONICAL_STRATEGY_SCHEMA)
        return True
    except (json.JSONDecodeError, jsonschema.ValidationError):
        return False


def create_minimal_example() -> CanonicalStrategy:
    """Create the minimal example from the specification."""
    example_data = {
        "strategy_id": "strat-20251014-001",
        "version": "0.1.0",
        "title": "EMA Crossover Simple",
        "description": "Buy on 50 EMA crossing above 200 EMA. Fixed position. SL 1%, TP 2%.",
        "classification": {
            "type": "trend-following",
            "risk_tier": "medium",
            "primary_instruments": ["AAPL", "SPY"]
        },
        "steps": [
            {
                "step_id": "s1",
                "order": 1,
                "title": "Entry rule",
                "trigger": "50 EMA crosses above 200 EMA on 5m bar",
                "condition": "no open position on instrument",
                "action": {
                    "type": "enter",
                    "order_type": "market",
                    "instrument": "ticker",
                    "size": {"mode": "fixed", "value": 100}
                },
                "exit": {
                    "stop_loss": "1% below entry",
                    "take_profit": "2% above entry"
                },
                "params": [
                    {"name": "ema_fast", "value": 50},
                    {"name": "ema_slow", "value": 200}
                ],
                "rationale": "Simple trend-follow test"
            }
        ],
        "provenance": {
            "sources": [{
                "url": "https://example.com/post",
                "type": "web_article",
                "author": "Jane Doe",
                "fetched_at": "2025-10-14T10:00:00Z",
                "snippet": "...50/200 EMA crossover..."
            }]
        },
        "metadata": {
            "created_at": "2025-10-14T10:01:00Z",
            "created_by": "user:nyaga",
            "last_updated": "2025-10-14T10:01:00Z",
            "confidence": "medium"
        }
    }
    
    return CanonicalStrategy(example_data)


if __name__ == "__main__":
    # Test the schema and example
    example = create_minimal_example()
    print("Example strategy created successfully!")
    print("\nSteps summary:")
    for step in example.get_steps_summary():
        print(f"  {step}")
    print(f"\nClassification: {example.get_classification_summary()}")
    print(f"\nJSON (compact): {example.to_json(compact=True)[:100]}...")