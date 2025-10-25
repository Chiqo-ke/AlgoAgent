"""
Backtest API Views for AlgoAgent
===============================

Django REST Framework views for the backtest API.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
import logging
import sys
from pathlib import Path
import traceback
import uuid
from decimal import Decimal

from .models import BacktestConfig, BacktestRun, BacktestResult, Trade, BacktestAlert
from .serializers import (
    BacktestConfigSerializer, BacktestRunSerializer, BacktestResultSerializer,
    TradeSerializer, BacktestAlertSerializer, BacktestRunRequestSerializer,
    BacktestConfigCreateSerializer, BacktestSearchSerializer,
    BacktestRunListSerializer, TradeListSerializer, BacktestQuickRunSerializer
)

# Add parent directory to path for imports
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

logger = logging.getLogger(__name__)


class BacktestConfigViewSet(viewsets.ModelViewSet):
    """ViewSet for managing backtest configurations"""
    queryset = BacktestConfig.objects.all()
    serializer_class = BacktestConfigSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        """Set the creating user if authenticated"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def templates(self, request):
        """Get template configurations"""
        templates = BacktestConfig.objects.filter(is_template=True)
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)


class BacktestRunViewSet(viewsets.ModelViewSet):
    """ViewSet for managing backtest runs"""
    queryset = BacktestRun.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail views"""
        if self.action == 'list':
            return BacktestRunListSerializer
        return BacktestRunSerializer
    
    def get_queryset(self):
        """Filter backtest runs by query parameters"""
        queryset = BacktestRun.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by strategy
        strategy_id = self.request.query_params.get('strategy_id', None)
        if strategy_id:
            queryset = queryset.filter(strategy__id=strategy_id)
        
        # Filter by symbols
        symbols = self.request.query_params.getlist('symbols')
        if symbols:
            for symbol in symbols:
                queryset = queryset.filter(symbols__contains=[symbol.upper()])
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        """Get detailed results for a backtest run"""
        run = self.get_object()
        try:
            result = run.result
            serializer = BacktestResultSerializer(result)
            return Response(serializer.data)
        except BacktestResult.DoesNotExist:
            return Response({
                'error': 'Results not available for this run'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def trades(self, request, pk=None):
        """Get trades for a backtest run"""
        run = self.get_object()
        trades = run.trades.all()
        serializer = TradeListSerializer(trades, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def alerts(self, request, pk=None):
        """Get alerts for a backtest run"""
        run = self.get_object()
        alerts = run.alerts.all()
        serializer = BacktestAlertSerializer(alerts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a running backtest"""
        run = self.get_object()
        if run.status in ['pending', 'queued', 'running']:
            run.status = 'cancelled'
            run.completed_at = timezone.now()
            run.save()
            
            return Response({
                'message': 'Backtest cancelled successfully',
                'run_id': run.run_id,
                'status': run.status
            })
        else:
            return Response({
                'error': f'Cannot cancel backtest with status: {run.status}'
            }, status=status.HTTP_400_BAD_REQUEST)


class BacktestAPIViewSet(viewsets.ViewSet):
    """Main API ViewSet for backtest operations"""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def run_backtest(self, request):
        """Start a new backtest run"""
        serializer = BacktestRunRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            
            # Get strategy
            try:
                from strategy_api.models import Strategy
                strategy = Strategy.objects.get(id=data['strategy_id'])
            except Strategy.DoesNotExist:
                return Response({
                    'error': 'Strategy not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get or create config
            config = None
            if data.get('config_id'):
                try:
                    config = BacktestConfig.objects.get(id=data['config_id'])
                except BacktestConfig.DoesNotExist:
                    return Response({
                        'error': 'Config not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Create temporary config from request data
                config = BacktestConfig.objects.create(
                    name=f"Auto-config for {strategy.name}",
                    description="Automatically generated configuration",
                    start_date=data.get('start_date', timezone.now().date()),
                    end_date=data.get('end_date', timezone.now().date()),
                    initial_capital=data.get('initial_capital', Decimal('10000.00')),
                    commission=data.get('commission', Decimal('0.001')),
                    slippage=data.get('slippage', Decimal('0.0005')),
                    created_by=request.user if request.user.is_authenticated else None
                )
            
            # Create backtest run
            run = BacktestRun.objects.create(
                run_id=f"bt_{uuid.uuid4().hex[:8]}",
                config=config,
                strategy=strategy,
                symbols=data['symbols'],
                status='queued',
                created_by=request.user if request.user.is_authenticated else None
            )
            
            # Try to start the backtest
            try:
                from Backtest.interactive_backtest_runner import InteractiveBacktestRunner
                
                # Update run status
                run.status = 'running'
                run.started_at = timezone.now()
                run.save()
                
                # Initialize backtest runner
                runner = InteractiveBacktestRunner()
                
                # Prepare backtest parameters
                backtest_params = {
                    'strategy_name': strategy.name,
                    'strategy_code': strategy.strategy_code,
                    'symbols': data['symbols'],
                    'start_date': config.start_date.isoformat(),
                    'end_date': config.end_date.isoformat(),
                    'initial_capital': float(config.initial_capital),
                    'commission': float(config.commission),
                    'slippage': float(config.slippage)
                }
                
                # Run backtest (this would typically be async in production)
                result = runner.run_backtest(backtest_params)
                
                if result.get('success', False):
                    # Create result record
                    metrics = result.get('metrics', {})
                    backtest_result = BacktestResult.objects.create(
                        run=run,
                        final_portfolio_value=metrics.get('final_portfolio_value', config.initial_capital),
                        total_return_pct=metrics.get('total_return', 0),
                        annualized_return_pct=metrics.get('annualized_return', 0),
                        volatility=metrics.get('volatility', 0),
                        sharpe_ratio=metrics.get('sharpe_ratio', 0),
                        max_drawdown_pct=metrics.get('max_drawdown', 0),
                        max_drawdown_duration=metrics.get('max_drawdown_duration', 0),
                        current_drawdown_pct=metrics.get('current_drawdown', 0),
                        total_trades=metrics.get('total_trades', 0),
                        winning_trades=metrics.get('winning_trades', 0),
                        losing_trades=metrics.get('losing_trades', 0),
                        win_rate_pct=metrics.get('win_rate', 0),
                        avg_trade_return_pct=metrics.get('avg_trade_return', 0),
                        avg_winning_trade_pct=metrics.get('avg_winning_trade', 0),
                        avg_losing_trade_pct=metrics.get('avg_losing_trade', 0),
                        largest_winning_trade_pct=metrics.get('largest_winning_trade', 0),
                        largest_losing_trade_pct=metrics.get('largest_losing_trade', 0),
                        profit_factor=metrics.get('profit_factor', 0),
                        payoff_ratio=metrics.get('payoff_ratio', 0),
                        portfolio_values=result.get('portfolio_values', {}),
                        returns=result.get('returns', {}),
                        drawdowns=result.get('drawdowns', {}),
                        positions=result.get('positions', {})
                    )
                    
                    # Update run summary
                    run.status = 'completed'
                    run.completed_at = timezone.now()
                    run.execution_time = (run.completed_at - run.started_at).total_seconds()
                    run.total_return = backtest_result.total_return_pct
                    run.sharpe_ratio = backtest_result.sharpe_ratio
                    run.max_drawdown = backtest_result.max_drawdown_pct
                    run.total_trades = backtest_result.total_trades
                    run.win_rate = backtest_result.win_rate_pct
                    run.save()
                    
                    return Response({
                        'run_id': run.run_id,
                        'status': 'completed',
                        'result_summary': {
                            'total_return': backtest_result.total_return_pct,
                            'sharpe_ratio': backtest_result.sharpe_ratio,
                            'max_drawdown': backtest_result.max_drawdown_pct,
                            'total_trades': backtest_result.total_trades,
                            'win_rate': backtest_result.win_rate_pct
                        }
                    })
                else:
                    run.status = 'failed'
                    run.completed_at = timezone.now()
                    run.error_message = result.get('error', 'Unknown error')
                    run.save()
                    
                    return Response({
                        'error': 'Backtest execution failed',
                        'details': result.get('error', 'Unknown error')
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except ImportError as e:
                run.status = 'failed'
                run.error_message = f'Backtest runner not available: {e}'
                run.save()
                
                return Response({
                    'error': 'Backtest runner not available',
                    'details': str(e)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except Exception as e:
            logger.error(f"Error in run_backtest: {e}")
            logger.error(traceback.format_exc())
            
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def quick_run(self, request):
        """Run a quick backtest with minimal configuration"""
        serializer = BacktestQuickRunSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            
            # Try to run quick backtest
            try:
                from Backtest.interactive_backtest_runner import InteractiveBacktestRunner
                
                runner = InteractiveBacktestRunner()
                
                # Prepare minimal backtest parameters
                backtest_params = {
                    'strategy_code': data['strategy_code'],
                    'symbols': [data['symbol']],
                    'start_date': data['start_date'].isoformat(),
                    'end_date': data['end_date'].isoformat(),
                    'initial_capital': float(data.get('initial_capital', 10000))
                }
                
                # Run backtest
                result = runner.run_quick_backtest(backtest_params)
                
                if result.get('success', False):
                    return Response({
                        'status': 'completed',
                        'metrics': result.get('metrics', {}),
                        'chart_data': result.get('chart_data', {}),
                        'trades': result.get('trades', [])
                    })
                else:
                    return Response({
                        'error': 'Quick backtest failed',
                        'details': result.get('error', 'Unknown error')
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except ImportError as e:
                return Response({
                    'error': 'Backtest runner not available',
                    'details': str(e)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except Exception as e:
            logger.error(f"Error in quick_run: {e}")
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def create_config(self, request):
        """Create a new backtest configuration"""
        serializer = BacktestConfigCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            
            config = BacktestConfig.objects.create(
                created_by=request.user if request.user.is_authenticated else None,
                **data
            )
            
            serializer = BacktestConfigSerializer(config)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error in create_config: {e}")
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Search backtest runs"""
        serializer = BacktestSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            queryset = BacktestRun.objects.all()
            
            # Apply filters
            if data.get('strategy_id'):
                queryset = queryset.filter(strategy__id=data['strategy_id'])
            
            if data.get('status'):
                queryset = queryset.filter(status=data['status'])
            
            if data.get('start_date_from'):
                queryset = queryset.filter(created_at__gte=data['start_date_from'])
            
            if data.get('start_date_to'):
                queryset = queryset.filter(created_at__lte=data['start_date_to'])
            
            if data.get('symbols'):
                for symbol in data['symbols']:
                    queryset = queryset.filter(symbols__contains=[symbol.upper()])
            
            if data.get('created_by'):
                queryset = queryset.filter(created_by__username=data['created_by'])
            
            runs = queryset.order_by('-created_at')
            serializer = BacktestRunListSerializer(runs, many=True)
            
            return Response({
                'runs': serializer.data,
                'count': runs.count()
            })
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """Health check endpoint"""
        try:
            # Check database connection
            run_count = BacktestRun.objects.count()
            config_count = BacktestConfig.objects.count()
            
            # Check if backtest modules are available
            runner_available = False
            
            try:
                from Backtest.interactive_backtest_runner import InteractiveBacktestRunner
                runner_available = True
            except ImportError:
                pass
            
            return Response({
                'status': 'healthy',
                'database': 'connected',
                'runs_count': run_count,
                'configs_count': config_count,
                'runner_available': runner_available,
                'timestamp': timezone.now()
            })
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class BacktestResultViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing backtest results"""
    queryset = BacktestResult.objects.all()
    serializer_class = BacktestResultSerializer
    permission_classes = [AllowAny]


class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing trades"""
    queryset = Trade.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail views"""
        if self.action == 'list':
            return TradeListSerializer
        return TradeSerializer
    
    def get_queryset(self):
        """Filter trades by query parameters"""
        queryset = Trade.objects.all()
        
        # Filter by run
        run_id = self.request.query_params.get('run_id', None)
        if run_id:
            queryset = queryset.filter(run__run_id=run_id)
        
        # Filter by symbol
        symbol = self.request.query_params.get('symbol', None)
        if symbol:
            queryset = queryset.filter(symbol=symbol.upper())
        
        # Filter by trade type
        trade_type = self.request.query_params.get('trade_type', None)
        if trade_type:
            queryset = queryset.filter(trade_type=trade_type)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-entry_date')


class BacktestAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing backtest alerts"""
    queryset = BacktestAlert.objects.all()
    serializer_class = BacktestAlertSerializer
    permission_classes = [AllowAny]
