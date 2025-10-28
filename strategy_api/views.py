"""
Strategy API Views for AlgoAgent
===============================

Django REST Framework views for the strategy API.
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

from .models import StrategyTemplate, Strategy, StrategyValidation, StrategyPerformance, StrategyComment, StrategyTag
from .serializers import (
    StrategyTemplateSerializer, StrategySerializer, StrategyValidationSerializer,
    StrategyPerformanceSerializer, StrategyCommentSerializer, StrategyTagSerializer,
    StrategyValidationRequestSerializer, StrategyCreateRequestSerializer,
    StrategyCodeGenerationRequestSerializer, StrategySearchSerializer, StrategyListSerializer
)

# Add parent directory to path for imports
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

logger = logging.getLogger(__name__)


class StrategyTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing strategy templates"""
    queryset = StrategyTemplate.objects.all()
    serializer_class = StrategyTemplateSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        """Set the creating user if authenticated"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def sync_from_strategy(self, request, pk=None):
        """Sync template with latest strategy changes
        
        This endpoint allows the AI agent to update the template with the latest
        strategy code, parameters, and chat context.
        
        Expected payload:
        {
            "strategy_code": "updated code",
            "parameters": {...},
            "chat_message": "Summary of changes made",
            "force_update": false  # Optional: update even if template is a system template
        }
        """
        template = self.get_object()
        
        try:
            data = request.data
            
            # Prevent updating system templates unless forced
            if template.is_system_template and not data.get('force_update', False):
                return Response({
                    'error': 'Cannot update system templates',
                    'message': 'This is a pre-built system template. Use force_update=true to override.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Update template with latest strategy info
            if 'strategy_code' in data:
                template.latest_strategy_code = data['strategy_code']
                template.template_code = data['strategy_code']  # Also update template_code
            
            if 'parameters' in data:
                template.latest_parameters = data['parameters']
                # Merge into parameters_schema
                for key, value in data['parameters'].items():
                    if key not in template.parameters_schema:
                        template.parameters_schema[key] = {
                            'type': type(value).__name__,
                            'default': value
                        }
            
            # Add chat message to history
            if 'chat_message' in data:
                chat_entry = {
                    'timestamp': timezone.now().isoformat(),
                    'message': data['chat_message'],
                    'user': request.user.username if request.user.is_authenticated else 'anonymous'
                }
                template.chat_history.append(chat_entry)
                
                # Keep only last 50 chat entries to prevent unbounded growth
                if len(template.chat_history) > 50:
                    template.chat_history = template.chat_history[-50:]
            
            # Update description if provided
            if 'description' in data:
                template.description = data['description']
            
            template.save()
            
            serializer = self.get_serializer(template)
            return Response({
                'success': True,
                'message': 'Template synchronized successfully',
                'template': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error in sync_from_strategy: {e}")
            return Response({
                'error': 'Failed to sync template',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def get_context(self, request, pk=None):
        """Get full context for AI agent
        
        Returns the template with full chat history, linked strategy info,
        and current state - useful for AI agents to understand the strategy evolution.
        """
        template = self.get_object()
        
        try:
            serializer = self.get_serializer(template)
            context_data = serializer.data
            
            # Add linked strategy info if available
            if template.linked_strategy:
                context_data['linked_strategy'] = {
                    'id': template.linked_strategy.id,
                    'name': template.linked_strategy.name,
                    'description': template.linked_strategy.description,
                    'status': template.linked_strategy.status,
                    'version': template.linked_strategy.version,
                    'updated_at': template.linked_strategy.updated_at,
                }
            
            # Add summary statistics
            context_data['context_summary'] = {
                'chat_messages_count': len(template.chat_history),
                'last_update': template.updated_at,
                'is_active': template.is_active,
                'template_type': 'system' if template.is_system_template else 'user-generated'
            }
            
            return Response(context_data)
            
        except Exception as e:
            logger.error(f"Error in get_context: {e}")
            return Response({
                'error': 'Failed to get context',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StrategyViewSet(viewsets.ModelViewSet):
    """ViewSet for managing strategies"""
    queryset = Strategy.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail views"""
        if self.action == 'list':
            return StrategyListSerializer
        return StrategySerializer
    
    def get_queryset(self):
        """Filter strategies by query parameters"""
        queryset = Strategy.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by category/template
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(template__category=category)
        
        # Filter by tags
        tags = self.request.query_params.getlist('tags')
        if tags:
            for tag in tags:
                queryset = queryset.filter(tags__contains=[tag])
        
        # Search by name or description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set the creating user if authenticated"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def validate_strategy(self, request, pk=None):
        """Validate a strategy"""
        strategy = self.get_object()
        serializer = StrategyValidationRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validation_types = serializer.validated_data['validation_types']
            config = serializer.validated_data.get('config', {})
            
            # Try to import strategy validator
            try:
                from Strategy.strategy_validator import StrategyValidatorBot
                
                validator = StrategyValidatorBot(
                    username=request.user.username if request.user.is_authenticated else 'anonymous',
                    strict_mode=config.get('strict_mode', False),
                    use_gemini=config.get('use_gemini', True)
                )
                
                # Process the strategy
                result = validator.process_input(
                    strategy_input=strategy.strategy_code,
                    input_type='code'
                )
                
                # Create validation record for each type
                validations = []
                for validation_type in validation_types:
                    validation = StrategyValidation.objects.create(
                        strategy=strategy,
                        validation_type=validation_type,
                        status='completed' if result.get('success', False) else 'failed',
                        score=result.get('confidence_score', 0) * 100 if result.get('confidence_score') else None,
                        passed_checks=result.get('validation_results', {}).get('passed', []),
                        failed_checks=result.get('validation_results', {}).get('failed', []),
                        warnings=result.get('warnings', []),
                        recommendations=result.get('recommendations', []),
                        validator_version='1.0.0',
                        validation_config=config,
                        completed_at=timezone.now()
                    )
                    validations.append(validation)
                
                # Update strategy status
                if result.get('success', False):
                    strategy.status = 'valid'
                else:
                    strategy.status = 'invalid'
                strategy.last_validated = timezone.now()
                strategy.save()
                
                return Response({
                    'strategy_id': strategy.id,
                    'validation_results': [
                        StrategyValidationSerializer(v).data for v in validations
                    ],
                    'overall_result': result
                })
                
            except ImportError as e:
                return Response({
                    'error': 'Strategy validator not available',
                    'details': str(e)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except Exception as e:
            logger.error(f"Error in validate_strategy: {e}")
            logger.error(traceback.format_exc())
            
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def validation_history(self, request, pk=None):
        """Get validation history for a strategy"""
        strategy = self.get_object()
        validations = strategy.validations.all()
        serializer = StrategyValidationSerializer(validations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def performance_history(self, request, pk=None):
        """Get performance history for a strategy"""
        strategy = self.get_object()
        performances = strategy.performance_records.all()
        serializer = StrategyPerformanceSerializer(performances, many=True)
        return Response(serializer.data)


class StrategyAPIViewSet(viewsets.ViewSet):
    """Main API ViewSet for strategy operations"""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def create_strategy(self, request):
        """Create a new strategy
        
        If template_id is not provided, automatically creates a new StrategyTemplate
        to track this strategy's evolution in the chat session.
        """
        serializer = StrategyCreateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            
            # Get template if specified
            template = None
            auto_created_template = False
            
            if data.get('template_id'):
                try:
                    template = StrategyTemplate.objects.get(id=data['template_id'])
                except StrategyTemplate.DoesNotExist:
                    return Response({
                        'error': 'Template not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Create strategy first
            strategy = Strategy.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                template=template,
                strategy_code=data['strategy_code'],
                parameters=data.get('parameters', {}),
                tags=data.get('tags', []),
                timeframe=data.get('timeframe', ''),
                risk_level=data.get('risk_level', ''),
                created_by=request.user if request.user.is_authenticated else None
            )
            
            # Auto-create template if not provided (for chat-based strategy development)
            if not template and not data.get('skip_template_creation', False):
                try:
                    # Generate unique template name
                    template_name = f"Template: {data['name']}"
                    counter = 1
                    while StrategyTemplate.objects.filter(name=template_name).exists():
                        template_name = f"Template: {data['name']} ({counter})"
                        counter += 1
                    
                    # Create auto-template
                    template = StrategyTemplate.objects.create(
                        name=template_name,
                        description=f"Auto-generated template for strategy development: {data.get('description', '')}",
                        category=data.get('tags', ['custom'])[0] if data.get('tags') else 'custom',
                        template_code=data['strategy_code'],
                        parameters_schema=data.get('parameters', {}),
                        is_active=True,
                        is_system_template=False,
                        linked_strategy=strategy,
                        latest_strategy_code=data['strategy_code'],
                        latest_parameters=data.get('parameters', {}),
                        chat_history=[],
                        created_by=request.user if request.user.is_authenticated else None
                    )
                    
                    # Link the template back to the strategy
                    strategy.template = template
                    strategy.save(update_fields=['template'])
                    
                    auto_created_template = True
                    logger.info(f"Auto-created template {template.id} for strategy {strategy.id}")
                    
                except Exception as e:
                    logger.warning(f"Failed to auto-create template: {e}")
                    # Don't fail the entire request if template creation fails
            
            serializer = StrategySerializer(strategy)
            response_data = serializer.data
            
            # Add template info to response if auto-created
            if auto_created_template:
                response_data['auto_created_template'] = {
                    'id': template.id,
                    'name': template.name,
                    'message': 'Template automatically created for tracking strategy evolution'
                }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error in create_strategy: {e}")
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def generate_code(self, request):
        """Generate strategy code using AI"""
        serializer = StrategyCodeGenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            description = data['strategy_description']
            template_id = data.get('template_id')
            parameters = data.get('parameters', {})
            use_gemini = data.get('use_gemini', True)
            
            # Try to import strategy generator
            try:
                from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
                
                generator = GeminiStrategyGenerator()
                
                # Get template if specified
                template_code = None
                if template_id:
                    try:
                        template = StrategyTemplate.objects.get(id=template_id)
                        template_code = template.template_code
                    except StrategyTemplate.DoesNotExist:
                        pass
                
                # Generate strategy code
                result = generator.generate_strategy(
                    description=description,
                    template_code=template_code,
                    parameters=parameters
                )
                
                if result.get('success', False):
                    return Response({
                        'generated_code': result.get('code', ''),
                        'strategy_name': result.get('name', ''),
                        'description': result.get('description', ''),
                        'parameters': result.get('parameters', {}),
                        'metadata': result.get('metadata', {})
                    })
                else:
                    return Response({
                        'error': 'Failed to generate strategy code',
                        'details': result.get('error', 'Unknown error')
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except ImportError as e:
                return Response({
                    'error': 'Strategy generator not available',
                    'details': str(e)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except Exception as e:
            logger.error(f"Error in generate_code: {e}")
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Advanced strategy search"""
        serializer = StrategySearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            queryset = Strategy.objects.all()
            
            # Apply filters
            if data.get('query'):
                query = data['query']
                queryset = queryset.filter(
                    Q(name__icontains=query) | Q(description__icontains=query)
                )
            
            if data.get('category'):
                queryset = queryset.filter(template__category=data['category'])
            
            if data.get('tags'):
                for tag in data['tags']:
                    queryset = queryset.filter(tags__contains=[tag])
            
            if data.get('status'):
                queryset = queryset.filter(status=data['status'])
            
            if data.get('risk_level'):
                queryset = queryset.filter(risk_level=data['risk_level'])
            
            if data.get('timeframe'):
                queryset = queryset.filter(timeframe=data['timeframe'])
            
            if data.get('created_by'):
                queryset = queryset.filter(created_by__username=data['created_by'])
            
            strategies = queryset.order_by('-created_at')
            serializer = StrategyListSerializer(strategies, many=True)
            
            return Response({
                'strategies': serializer.data,
                'count': strategies.count()
            })
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get list of strategy categories"""
        try:
            categories = StrategyTemplate.objects.values_list('category', flat=True).distinct()
            return Response({'categories': list(categories)})
        except Exception as e:
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """Health check endpoint"""
        try:
            # Check database connection
            strategy_count = Strategy.objects.count()
            template_count = StrategyTemplate.objects.count()
            
            # Check if strategy modules are available
            validator_available = False
            generator_available = False
            
            try:
                from Strategy.strategy_validator import StrategyValidatorBot
                validator_available = True
            except ImportError:
                pass
            
            try:
                from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
                generator_available = True
            except ImportError:
                pass
            
            return Response({
                'status': 'healthy',
                'database': 'connected',
                'strategies_count': strategy_count,
                'templates_count': template_count,
                'validator_available': validator_available,
                'generator_available': generator_available,
                'timestamp': timezone.now()
            })
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class StrategyValidationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing strategy validations"""
    queryset = StrategyValidation.objects.all()
    serializer_class = StrategyValidationSerializer
    permission_classes = [AllowAny]


class StrategyPerformanceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing strategy performance records"""
    queryset = StrategyPerformance.objects.all()
    serializer_class = StrategyPerformanceSerializer
    permission_classes = [AllowAny]


class StrategyCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing strategy comments"""
    queryset = StrategyComment.objects.all()
    serializer_class = StrategyCommentSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        """Set the comment author if authenticated"""
        if self.request.user.is_authenticated:
            serializer.save(author=self.request.user)
        else:
            # Create anonymous user or handle as needed
            serializer.save()


class StrategyTagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing strategy tags"""
    queryset = StrategyTag.objects.all()
    serializer_class = StrategyTagSerializer
    permission_classes = [AllowAny]
