"""
API View for Strategy Validation
Validates generated strategy code before user backtesting
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import sys
from pathlib import Path
import logging

# Add Backtest directory to path
BACKTEST_DIR = Path(__file__).parent.parent.parent / "Backtest"
sys.path.insert(0, str(BACKTEST_DIR))

from Backtest.strategy_validator import StrategyValidator

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_strategy(request):
    """
    Validate strategy code before backtesting
    
    VALIDATION REQUIREMENT: Strategy must execute at least 1 trade in 1-year test
    to be approved. This ensures the strategy logic actually works.
    
    POST /api/strategies/validate/
    Body:
    {
        "strategy_code": "...",  # Python code string
        "strategy_name": "MyStrategy",  # Optional
        "test_symbol": "AAPL",  # Optional, default: AAPL
        "test_period_days": 365  # Optional, default: 365 (1 year)
    }
    
    Returns:
    {
        "valid": true/false,  # true ONLY if at least 1 trade executed
        "strategy_name": "...",
        "trades_executed": 5,  # Must be > 0 for valid=true
        "execution_time": 4.5,
        "errors": [],  # Critical errors that prevent approval
        "warnings": [],  # Non-critical issues
        "suggestions": [],  # Recommendations for improvement
        "test_results": {
            "return": 5.2,
            "trades": 5,
            "win_rate": 60.0,
            "sharpe": 1.2,
            "max_drawdown": -8.5
        }
    }
    """
    try:
        # Get request data
        strategy_code = request.data.get('strategy_code')
        strategy_name = request.data.get('strategy_name', 'GeneratedStrategy')
        test_symbol = request.data.get('test_symbol', 'AAPL')
        test_period_days = request.data.get('test_period_days', 365)  # Default to 1 year
        
        if not strategy_code:
            return Response(
                {"error": "strategy_code is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Validating strategy: {strategy_name}")
        
        # Create validator and run validation
        validator = StrategyValidator()
        result = validator.validate_strategy_code(
            strategy_code=strategy_code,
            strategy_name=strategy_name,
            test_symbol=test_symbol,
            test_period_days=test_period_days
        )
        
        logger.info(f"Validation complete: valid={result['valid']}, trades={result['trades_executed']}")
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        return Response(
            {
                "error": "Validation failed",
                "detail": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_strategy_file(request):
    """
    Validate a saved strategy file
    
    POST /api/strategies/validate-file/
    Body:
    {
        "file_path": "codes/ema.py",  # Relative to Backtest directory
        "test_symbol": "AAPL",  # Optional
        "test_period_days": 90  # Optional
    }
    """
    try:
        file_path = request.data.get('file_path')
        test_symbol = request.data.get('test_symbol', 'AAPL')
        test_period_days = request.data.get('test_period_days', 365)  # Default to 1 year
        
        if not file_path:
            return Response(
                {"error": "file_path is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Construct full path
        full_path = BACKTEST_DIR / file_path
        
        if not full_path.exists():
            return Response(
                {"error": f"File not found: {file_path}"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        logger.info(f"Validating strategy file: {file_path}")
        
        # Read strategy code
        with open(full_path, 'r') as f:
            strategy_code = f.read()
        
        # Extract strategy name from file
        strategy_name = Path(file_path).stem
        
        # Create validator and run validation
        validator = StrategyValidator()
        result = validator.validate_strategy_code(
            strategy_code=strategy_code,
            strategy_name=strategy_name,
            test_symbol=test_symbol,
            test_period_days=test_period_days
        )
        
        logger.info(f"File validation complete: valid={result['valid']}")
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"File validation error: {e}", exc_info=True)
        return Response(
            {
                "error": "File validation failed",
                "detail": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
