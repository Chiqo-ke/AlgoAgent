"""
Canonical Schema Definitions V2 - Pydantic Edition
==================================================

Enhanced version of canonical schema using Pydantic for runtime validation,
JSON schema export, and type safety enforcement.

Features:
- Runtime validation of all data structures
- JSON schema generation for external tools
- Schema versioning for backward compatibility
- Immutable constraints enforcement
- Comprehensive field validation

Version: 2.0.0
Last Updated: 2025-11-02
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from enum import Enum
import uuid


# Schema version for compatibility tracking
SCHEMA_VERSION = "2.0.0"


# ============================================================================
# ENUMERATIONS (Canonical Values)
# ============================================================================

class OrderSide(str, Enum):
    """Order side constants"""
    BUY = "BUY"
    SELL = "SELL"


class OrderAction(str, Enum):
    """Signal action types"""
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    MODIFY = "MODIFY"
    CANCEL = "CANCEL"


class OrderType(str, Enum):
    """Order type constants"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    """Order lifecycle status"""
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class SizeType(str, Enum):
    """Position sizing method"""
    SHARES = "SHARES"
    CONTRACTS = "CONTRACTS"
    NOTIONAL = "NOTIONAL"
    RISK_PERCENT = "RISK_PERCENT"
    MARGIN_PERCENT = "MARGIN_PERCENT"
    KELLY = "KELLY"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class Signal(BaseModel):
    """
    Canonical Signal Schema (Input from Strategy)
    
    This is the primary interface for strategies to communicate
    trading intentions to the SimBroker.
    """
    signal_id: str = Field(default_factory=lambda: f"sig_{uuid.uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str = Field(..., min_length=1, max_length=20, description="Ticker symbol")
    side: OrderSide
    action: OrderAction
    order_type: OrderType
    size: float = Field(..., gt=0, description="Order size (must be positive)")
    size_type: SizeType = Field(default=SizeType.SHARES)
    price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)
    risk_params: Optional[Dict[str, Any]] = None
    strategy_id: str = Field(default="default")
    meta: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = Field(default=SCHEMA_VERSION)
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        """Ensure symbol is uppercase and valid"""
        return v.upper().strip()
    
    @model_validator(mode='after')
    def validate_price_requirements(self):
        """Validate price fields based on order type"""
        order_type = self.order_type
        price = self.price
        stop_price = self.stop_price
        
        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
            if price is None:
                raise ValueError(f"{order_type} orders require price field")
        
        if order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            if stop_price is None:
                raise ValueError(f"{order_type} orders require stop_price field")
        
        return self
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Order(BaseModel):
    """Order object with full lifecycle tracking"""
    order_id: str = Field(default_factory=lambda: f"ord_{uuid.uuid4().hex[:8]}")
    signal_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str = Field(..., min_length=1)
    side: OrderSide
    order_type: OrderType
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    quantity: float = Field(..., gt=0)
    filled_quantity: float = Field(default=0.0, ge=0)
    price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)
    filled_price: Optional[float] = None
    commission: float = Field(default=0.0, ge=0)
    meta: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = Field(default=SCHEMA_VERSION)
    
    @model_validator(mode='after')
    def validate_filled_quantity(self):
        """Ensure filled quantity doesn't exceed order quantity"""
        if self.filled_quantity > self.quantity:
            raise ValueError(f"Filled quantity {self.filled_quantity} exceeds order quantity {self.quantity}")
        return self
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Fill(BaseModel):
    """Fill execution record"""
    fill_id: str = Field(default_factory=lambda: f"fill_{uuid.uuid4().hex[:8]}")
    order_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str
    side: OrderSide
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    commission: float = Field(default=0.0, ge=0)
    meta: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = Field(default=SCHEMA_VERSION)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Position(BaseModel):
    """Current position in a symbol"""
    symbol: str = Field(..., min_length=1)
    quantity: float = Field(default=0.0)
    avg_entry_price: float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)
    unrealized_pnl: float = Field(default=0.0)
    realized_pnl: float = Field(default=0.0)
    last_update: datetime = Field(default_factory=datetime.now)
    meta: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = Field(default=SCHEMA_VERSION)
    
    @property
    def market_value(self) -> float:
        """Calculate current market value"""
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """Calculate cost basis"""
        return self.quantity * self.avg_entry_price
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Trade(BaseModel):
    """Completed trade record"""
    trade_id: str = Field(default_factory=lambda: f"trade_{uuid.uuid4().hex[:8]}")
    symbol: str
    entry_time: datetime
    exit_time: datetime
    side: OrderSide
    quantity: float = Field(..., gt=0)
    entry_price: float = Field(..., gt=0)
    exit_price: float = Field(..., gt=0)
    pnl: float
    pnl_percent: float
    commission: float = Field(default=0.0, ge=0)
    duration_seconds: float = Field(..., ge=0)
    meta: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = Field(default=SCHEMA_VERSION)
    
    @model_validator(mode='after')
    def calculate_metrics(self):
        """Calculate derived metrics"""
        if self.entry_time and self.exit_time:
            self.duration_seconds = (self.exit_time - self.entry_time).total_seconds()
        
        return self
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StrategyDefinition(BaseModel):
    """
    JSON Strategy Definition Schema
    
    This is the canonical format for defining strategies in JSON files
    before code generation.
    """
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    version: str = Field(default="1.0.0")
    framework: Literal["backtesting.py", "simbroker"] = Field(default="backtesting.py")
    
    # Data requirements
    symbol: str = Field(default="AAPL")
    period: str = Field(default="1y")
    interval: str = Field(default="1d")
    
    # Strategy parameters (optimizable)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Trading rules
    entry_rules: List[str] = Field(default_factory=list)
    exit_rules: List[str] = Field(default_factory=list)
    
    # Risk management
    position_sizing: Dict[str, Any] = Field(default_factory=dict)
    risk_limits: Dict[str, Any] = Field(default_factory=dict)
    
    # Indicators required
    indicators: Dict[str, Optional[Dict[str, Any]]] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    schema_version: str = Field(default=SCHEMA_VERSION)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Ensure name is valid Python identifier"""
        if not v.replace('_', '').isalnum():
            raise ValueError("Strategy name must be alphanumeric with underscores only")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GeneratedCode(BaseModel):
    """
    Schema for generated code response from LLM
    
    Enforces structured output from code generation.
    """
    code: str = Field(..., min_length=10)
    language: str = Field(default="python")
    entrypoint: str = Field(..., description="Main function or class name")
    dependencies: List[str] = Field(default_factory=list)
    files: List[Dict[str, str]] = Field(default_factory=list)  # [{path: str, content: str}]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = Field(default=SCHEMA_VERSION)
    
    @field_validator('code')
    @classmethod
    def validate_code_syntax(cls, v):
        """Basic validation - check it's not empty"""
        if not v.strip():
            raise ValueError("Code cannot be empty")
        return v


class ExecutionResult(BaseModel):
    """
    Structured execution result from sandbox
    """
    status: Literal["success", "error", "timeout", "not_found"]
    exit_code: int
    stdout: str = Field(default="")
    stderr: str = Field(default="")
    execution_time: float = Field(..., ge=0)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    sandbox_id: Optional[str] = None
    resource_usage: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = Field(default=SCHEMA_VERSION)


class PlanStep(BaseModel):
    """Individual step in execution plan"""
    id: str
    type: Literal["generate", "test", "fix", "analyze", "deploy"]
    description: str
    files: List[str] = Field(default_factory=list)
    command: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)
    timeout: int = Field(default=120, gt=0)
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=0)


class ExecutionPlan(BaseModel):
    """
    Complete execution plan from planner
    
    Structured plan that orchestrator can validate and execute.
    """
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    goal: str = Field(..., min_length=1)
    steps: List[PlanStep]
    estimated_time: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    schema_version: str = Field(default=SCHEMA_VERSION)
    
    @field_validator('steps')
    @classmethod
    def validate_dependencies(cls, v):
        """Ensure all dependencies reference valid step IDs"""
        step_ids = {step.id for step in v}
        for step in v:
            for dep in step.depends_on:
                if dep not in step_ids:
                    raise ValueError(f"Step {step.id} depends on non-existent step {dep}")
        return v


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_id(prefix: str = "id") -> str:
    """Generate unique ID with prefix"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def export_json_schema(model_class: type[BaseModel], output_path: str):
    """Export Pydantic model as JSON Schema"""
    import json
    schema = model_class.schema()
    with open(output_path, 'w') as f:
        json.dump(schema, f, indent=2)


def validate_strategy_json(json_path: str) -> StrategyDefinition:
    """
    Validate a strategy JSON file against schema
    
    Args:
        json_path: Path to JSON file
        
    Returns:
        Validated StrategyDefinition
        
    Raises:
        ValidationError if schema is invalid
    """
    import json
    with open(json_path, 'r') as f:
        data = json.load(f)
    return StrategyDefinition(**data)


def get_all_schemas() -> Dict[str, type[BaseModel]]:
    """Get all schema models for export"""
    return {
        "Signal": Signal,
        "Order": Order,
        "Fill": Fill,
        "Position": Position,
        "Trade": Trade,
        "StrategyDefinition": StrategyDefinition,
        "GeneratedCode": GeneratedCode,
        "ExecutionResult": ExecutionResult,
        "ExecutionPlan": ExecutionPlan,
        "PlanStep": PlanStep,
    }


# CLI for schema validation
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate JSON files against canonical schema")
    parser.add_argument("--validate", type=str, help="Path to strategy JSON file to validate")
    parser.add_argument("--export-schemas", type=str, help="Directory to export all JSON schemas")
    parser.add_argument("--show-schema", type=str, choices=list(get_all_schemas().keys()), 
                       help="Show JSON schema for a specific model")
    
    args = parser.parse_args()
    
    if args.validate:
        try:
            strategy = validate_strategy_json(args.validate)
            print(f"✓ Valid strategy: {strategy.name}")
            print(f"  Description: {strategy.description}")
            print(f"  Parameters: {list(strategy.parameters.keys())}")
        except Exception as e:
            print(f"✗ Validation failed: {e}")
            sys.exit(1)
    
    elif args.export_schemas:
        import os
        os.makedirs(args.export_schemas, exist_ok=True)
        for name, model in get_all_schemas().items():
            output_path = os.path.join(args.export_schemas, f"{name}.schema.json")
            export_json_schema(model, output_path)
            print(f"Exported {name} schema to {output_path}")
    
    elif args.show_schema:
        import json
        model = get_all_schemas()[args.show_schema]
        print(json.dumps(model.schema(), indent=2))
    
    else:
        parser.print_help()
