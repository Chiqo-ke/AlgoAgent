"""
Data API Views for AlgoAgent
============================

Django REST Framework views for the data API.
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

from .models import Symbol, DataRequest, MarketData, Indicator, IndicatorData, DataCache
from .serializers import (
    SymbolSerializer, DataRequestSerializer, MarketDataSerializer,
    IndicatorSerializer, IndicatorDataSerializer, DataCacheSerializer,
    DataFetchRequestSerializer, IndicatorCalculationRequestSerializer,
    MarketDataBulkSerializer
)

# Add parent directory to path for imports
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

logger = logging.getLogger(__name__)


class SymbolViewSet(viewsets.ModelViewSet):
    """ViewSet for managing trading symbols"""
    queryset = Symbol.objects.all()
    serializer_class = SymbolSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create symbols from a list"""
        symbols_data = request.data.get('symbols', [])
        if not isinstance(symbols_data, list):
            return Response(
                {'error': 'symbols must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_symbols = []
        for symbol_data in symbols_data:
            if isinstance(symbol_data, str):
                symbol_data = {'symbol': symbol_data, 'name': symbol_data}
            
            symbol, created = Symbol.objects.get_or_create(
                symbol=symbol_data['symbol'].upper(),
                defaults=symbol_data
            )
            if created:
                created_symbols.append(symbol)
        
        serializer = self.get_serializer(created_symbols, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search symbols by name or symbol"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Query parameter q is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        symbols = Symbol.objects.filter(
            Q(symbol__icontains=query) | Q(name__icontains=query)
        ).filter(is_active=True)
        
        serializer = self.get_serializer(symbols, many=True)
        return Response(serializer.data)


class DataRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing data requests"""
    queryset = DataRequest.objects.all()
    serializer_class = DataRequestSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        """Set the requesting user if authenticated"""
        if self.request.user.is_authenticated:
            serializer.save(requested_by=self.request.user)
        else:
            serializer.save()


class MarketDataViewSet(viewsets.ModelViewSet):
    """ViewSet for managing market data"""
    queryset = MarketData.objects.all()
    serializer_class = MarketDataSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Filter market data by query parameters"""
        queryset = MarketData.objects.all()
        
        symbol = self.request.query_params.get('symbol', None)
        if symbol:
            queryset = queryset.filter(symbol__symbol=symbol.upper())
        
        interval = self.request.query_params.get('interval', None)
        if interval:
            queryset = queryset.filter(interval=interval)
        
        start_date = self.request.query_params.get('start_date', None)
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        
        end_date = self.request.query_params.get('end_date', None)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.order_by('timestamp')


class IndicatorViewSet(viewsets.ModelViewSet):
    """ViewSet for managing indicators"""
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get list of indicator categories"""
        categories = Indicator.objects.values_list('category', flat=True).distinct()
        return Response({'categories': list(categories)})


class IndicatorDataViewSet(viewsets.ModelViewSet):
    """ViewSet for managing indicator data"""
    queryset = IndicatorData.objects.all()
    serializer_class = IndicatorDataSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Filter indicator data by query parameters"""
        queryset = IndicatorData.objects.all()
        
        symbol = self.request.query_params.get('symbol', None)
        if symbol:
            queryset = queryset.filter(symbol__symbol=symbol.upper())
        
        indicator = self.request.query_params.get('indicator', None)
        if indicator:
            queryset = queryset.filter(indicator__name=indicator)
        
        interval = self.request.query_params.get('interval', None)
        if interval:
            queryset = queryset.filter(interval=interval)
        
        return queryset.order_by('timestamp')


class DataAPIViewSet(viewsets.ViewSet):
    """Main API ViewSet for data operations"""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def fetch_data(self, request):
        """Fetch market data for a symbol"""
        serializer = DataFetchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            symbol_str = data['symbol']
            period = data['period']
            interval = data['interval']
            indicators = data.get('indicators', [])
            
            # Get or create symbol
            symbol, created = Symbol.objects.get_or_create(
                symbol=symbol_str,
                defaults={'name': symbol_str, 'is_active': True}
            )
            
            # Create data request
            data_request = DataRequest.objects.create(
                symbol=symbol,
                period=period,
                interval=interval,
                status='processing',
                requested_by=request.user if request.user.is_authenticated else None
            )
            
            # Try to import and use existing data fetcher
            try:
                from Data.data_fetcher import DataFetcher
                from Data.indicator_calculator import compute_indicator
                
                # Fetch data
                data_fetcher = DataFetcher()
                df = data_fetcher.fetch_data(symbol_str, period=period, interval=interval)
                
                if df is not None and not df.empty:
                    # Save market data
                    saved_count = 0
                    for idx, row in df.iterrows():
                        market_data, created = MarketData.objects.get_or_create(
                            symbol=symbol,
                            timestamp=idx,
                            interval=interval,
                            defaults={
                                'open_price': row['Open'],
                                'high_price': row['High'],
                                'low_price': row['Low'],
                                'close_price': row['Close'],
                                'volume': row['Volume'],
                                'adj_close': row.get('Adj Close', row['Close'])
                            }
                        )
                        if created:
                            saved_count += 1
                    
                    # Calculate indicators if requested
                    indicator_results = {}
                    for indicator_name in indicators:
                        try:
                            indicator_result = compute_indicator(df, indicator_name)
                            if indicator_result is not None:
                                indicator_results[indicator_name] = indicator_result.tolist() if hasattr(indicator_result, 'tolist') else indicator_result
                        except Exception as e:
                            logger.warning(f"Error calculating indicator {indicator_name}: {e}")
                    
                    data_request.status = 'completed'
                    data_request.completed_at = timezone.now()
                    data_request.save()
                    
                    return Response({
                        'request_id': data_request.request_id,
                        'status': 'completed',
                        'symbol': symbol_str,
                        'records_saved': saved_count,
                        'total_records': len(df),
                        'indicators': indicator_results,
                        'data_sample': df.head().to_dict() if not df.empty else {}
                    })
                else:
                    data_request.status = 'failed'
                    data_request.error_message = 'No data retrieved'
                    data_request.save()
                    
                    return Response({
                        'error': 'No data found for the specified symbol and period'
                    }, status=status.HTTP_404_NOT_FOUND)
                    
            except ImportError as e:
                data_request.status = 'failed'
                data_request.error_message = f'Data fetcher not available: {e}'
                data_request.save()
                
                return Response({
                    'error': 'Data fetcher module not available',
                    'details': str(e)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            logger.error(f"Error in fetch_data: {e}")
            logger.error(traceback.format_exc())
            
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def calculate_indicator(self, request):
        """Calculate an indicator for a symbol"""
        serializer = IndicatorCalculationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            symbol_str = data['symbol']
            indicator_name = data['indicator']
            parameters = data.get('parameters', {})
            
            # Get symbol
            try:
                symbol = Symbol.objects.get(symbol=symbol_str)
            except Symbol.DoesNotExist:
                return Response({
                    'error': f'Symbol {symbol_str} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get market data
            market_data = MarketData.objects.filter(
                symbol=symbol,
                interval=data['interval']
            ).order_by('timestamp')
            
            if not market_data.exists():
                return Response({
                    'error': 'No market data found for this symbol. Fetch data first.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Convert to DataFrame
            import pandas as pd
            df_data = []
            for md in market_data:
                df_data.append({
                    'Open': float(md.open_price),
                    'High': float(md.high_price),
                    'Low': float(md.low_price),
                    'Close': float(md.close_price),
                    'Volume': md.volume,
                    'timestamp': md.timestamp
                })
            
            df = pd.DataFrame(df_data)
            df.set_index('timestamp', inplace=True)
            
            # Calculate indicator
            try:
                from Data.indicator_calculator import compute_indicator
                result = compute_indicator(df, indicator_name, **parameters)
                
                if result is not None:
                    # Convert result to serializable format
                    if hasattr(result, 'tolist'):
                        result_data = result.tolist()
                    elif hasattr(result, 'to_dict'):
                        result_data = result.to_dict()
                    else:
                        result_data = result
                    
                    return Response({
                        'symbol': symbol_str,
                        'indicator': indicator_name,
                        'parameters': parameters,
                        'result': result_data
                    })
                else:
                    return Response({
                        'error': f'Failed to calculate indicator {indicator_name}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except ImportError:
                return Response({
                    'error': 'Indicator calculator not available'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except Exception as e:
            logger.error(f"Error in calculate_indicator: {e}")
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def available_indicators(self, request):
        """Get list of available indicators"""
        try:
            from Data import registry
            indicators = registry.get_all_indicators()
            
            return Response({
                'indicators': indicators
            })
        except ImportError:
            return Response({
                'error': 'Indicator registry not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """Health check endpoint"""
        try:
            # Check database connection
            symbol_count = Symbol.objects.count()
            
            # Check if data modules are available
            data_fetcher_available = False
            indicators_available = False
            
            try:
                from Data.data_fetcher import DataFetcher
                data_fetcher_available = True
            except ImportError:
                pass
            
            try:
                from Data.indicator_calculator import compute_indicator
                indicators_available = True
            except ImportError:
                pass
            
            return Response({
                'status': 'healthy',
                'database': 'connected',
                'symbols_count': symbol_count,
                'data_fetcher_available': data_fetcher_available,
                'indicators_available': indicators_available,
                'timestamp': timezone.now()
            })
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
