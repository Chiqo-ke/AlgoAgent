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

from .models import (
    StrategyTemplate, Strategy, StrategyValidation, StrategyPerformance, 
    StrategyComment, StrategyTag, StrategyChat, StrategyChatMessage
)
from .serializers import (
    StrategyTemplateSerializer, StrategySerializer, StrategyValidationSerializer,
    StrategyPerformanceSerializer, StrategyCommentSerializer, StrategyTagSerializer,
    StrategyValidationRequestSerializer, StrategyCreateRequestSerializer,
    StrategyCodeGenerationRequestSerializer, StrategySearchSerializer, StrategyListSerializer,
    StrategyAIValidationRequestSerializer, StrategyAIValidationResponseSerializer,
    StrategyCreateWithAIRequestSerializer, StrategyChatSerializer, StrategyChatMessageSerializer,
    StrategyChatListSerializer, ChatMessageRequestSerializer, ChatResponseSerializer
)

# Add parent directory to path for imports
PARENT_DIR = Path(__file__).parent.parent
STRATEGY_DIR = PARENT_DIR / "Strategy"
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))
if str(STRATEGY_DIR) not in sys.path:
    sys.path.insert(0, str(STRATEGY_DIR))

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
            
            # Create strategy with 'validating' status
            strategy = Strategy.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                template=template,
                strategy_code=data['strategy_code'],
                parameters=data.get('parameters', {}),
                tags=data.get('tags', []),
                timeframe=data.get('timeframe', ''),
                risk_level=data.get('risk_level', ''),
                expected_return=data.get('expected_return'),
                max_drawdown=data.get('max_drawdown'),
                status='validating',  # Start in validating state
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
            
            # Trigger async validation
            self._trigger_async_validation(strategy)
            
            serializer = StrategySerializer(strategy)
            response_data = serializer.data
            
            # Add template info to response if auto-created
            if auto_created_template:
                response_data['auto_created_template'] = {
                    'id': template.id,
                    'name': template.name,
                    'message': 'Template automatically created for tracking strategy evolution'
                }
            
            # Add validation status message
            response_data['validation_message'] = 'Strategy is being validated in the background. Check status before backtesting.'
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error in create_strategy: {e}")
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _trigger_async_validation(self, strategy):
        """
        Trigger async validation for newly created strategy
        Runs validation in background thread to avoid blocking API response
        """
        import threading
        
        def validate_strategy_background():
            """Background validation task"""
            try:
                logger.info(f"[VALIDATION] Starting background validation for strategy {strategy.id}: {strategy.name}")
                
                # Import validator
                sys.path.insert(0, str(PARENT_DIR / "Backtest"))
                from Backtest.strategy_validator import StrategyValidator
                
                validator = StrategyValidator()
                result = validator.validate_strategy_code(
                    strategy_code=strategy.strategy_code,
                    strategy_name=strategy.name,
                    test_symbol='AAPL',
                    test_period_days=365  # 1 year test
                )
                
                # Update strategy status based on validation
                if result['valid']:
                    strategy.status = 'valid'
                    strategy.last_validated = timezone.now()
                    logger.info(f"[VALIDATION] Strategy {strategy.id} is VALID ({result['trades_executed']} trades)")
                else:
                    strategy.status = 'invalid'
                    logger.warning(f"[VALIDATION] Strategy {strategy.id} is INVALID: {result['errors']}")
                
                strategy.save(update_fields=['status', 'last_validated'])
                
                # Create or update StrategyValidation record with correct field names
                StrategyValidation.objects.update_or_create(
                    strategy=strategy,
                    validation_type='backtest',
                    defaults={
                        'status': 'passed' if result['valid'] else 'failed',
                        'score': result.get('performance_score', 0),
                        'passed_checks': result.get('passed_checks', []),
                        'failed_checks': result.get('errors', []),
                        'warnings': result.get('warnings', []),
                        'recommendations': result.get('suggestions', []),
                        'validation_config': {'test_period': '1 year', 'framework': 'backtesting.py'},
                        'execution_time': result.get('execution_time', 0),
                        'completed_at': timezone.now(),
                    }
                )
                
                logger.info(f"[VALIDATION] Strategy {strategy.id} validation complete: {strategy.status}")
                
            except Exception as e:
                logger.error(f"[VALIDATION] Error validating strategy {strategy.id}: {e}")
                logger.error(traceback.format_exc())
                # Mark as invalid on error
                strategy.status = 'invalid'
                strategy.save(update_fields=['status'])
        
        # Start validation in background thread
        thread = threading.Thread(target=validate_strategy_background, daemon=True)
        thread.start()
        logger.info(f"[VALIDATION] Triggered background validation thread for strategy {strategy.id}")
    
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
    def generate_executable_code(self, request):
        """
        Generate executable Python strategy code from canonical JSON.
        This is used after strategy confirmation to create a runnable Python file
        that can be used with SimBroker for backtesting.
        
        Request body:
        {
            "canonical_json": {...},  // The canonical strategy JSON
            "strategy_name": "MyStrategy",  // Strategy name for class naming
            "strategy_id": 123  // Optional: existing strategy ID to link
        }
        
        Returns:
        {
            "success": true,
            "strategy_code": "...",  // Generated Python code
            "file_path": "...",  // Path where code was saved
            "strategy_id": 123  // Strategy ID if linked
        }
        """
        try:
            data = request.data
            canonical_json = data.get('canonical_json')
            strategy_name = data.get('strategy_name', 'GeneratedStrategy')
            strategy_id = data.get('strategy_id')
            
            if not canonical_json:
                return Response({
                    'error': 'canonical_json is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Import strategy generator
            try:
                from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
            except ImportError as e:
                return Response({
                    'error': 'Strategy generator not available',
                    'details': str(e)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Parse canonical JSON if it's a string
            if isinstance(canonical_json, str):
                import json
                try:
                    canonical_json = json.loads(canonical_json)
                except json.JSONDecodeError as e:
                    return Response({
                        'error': 'Invalid JSON format',
                        'details': str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Build strategy description from canonical JSON
            description = f"{canonical_json.get('strategy_name', strategy_name)}\n"
            description += f"{canonical_json.get('description', '')}\n\n"
            
            # Add entry rules
            if canonical_json.get('entry_rules'):
                description += "Entry Rules:\n"
                for i, rule in enumerate(canonical_json['entry_rules'], 1):
                    description += f"{i}. {rule.get('description', str(rule))}\n"
                description += "\n"
            
            # Add exit rules
            if canonical_json.get('exit_rules'):
                description += "Exit Rules:\n"
                for i, rule in enumerate(canonical_json['exit_rules'], 1):
                    description += f"{i}. {rule.get('description', str(rule))}\n"
                description += "\n"
            
            # Add risk management
            if canonical_json.get('risk_management'):
                description += "Risk Management:\n"
                risk = canonical_json['risk_management']
                if risk.get('stop_loss'):
                    description += f"- Stop Loss: {risk['stop_loss']}\n"
                if risk.get('take_profit'):
                    description += f"- Take Profit: {risk['take_profit']}\n"
                if risk.get('position_sizing'):
                    description += f"- Position Sizing: {risk['position_sizing']}\n"
                description += "\n"
            
            # Add indicators
            if canonical_json.get('indicators'):
                description += "Indicators:\n"
                for indicator in canonical_json['indicators']:
                    description += f"- {indicator.get('name', indicator.get('type', 'Unknown'))}\n"
                description += "\n"
            
            # Add symbol-agnostic instructions
            description += "\nIMPORTANT INSTRUCTIONS FOR CODE GENERATION:\n"
            description += "- Strategy should work with ANY symbol (do not hardcode symbols)\n"
            description += "- Symbol will be provided dynamically through market_data parameter\n"
            description += "- Use market_data dictionary to access OHLCV data for any symbol\n"
            description += "- Constructor should only accept broker and trading parameters (no symbol parameter)\n"
            description += "- Timeframe: " + str(canonical_json.get('timeframe', '1d')) + "\n"
            
            # Generate the code
            generator = GeminiStrategyGenerator()
            
            logger.info(f"Generating executable code for: {strategy_name}")
            
            strategy_code = generator.generate_strategy(
                description=description,
                strategy_name=strategy_name
            )
            
            # Save to Backtest/codes/ directory
            import re
            from pathlib import Path
            
            # Create safe filename
            safe_name = re.sub(r'[^a-zA-Z0-9\s]', '', strategy_name.lower())
            words = safe_name.split()[:8]
            base_filename = "_".join(words) if words else f"strategy_{strategy_id or 'new'}"
            
            backtest_codes_dir = Path(__file__).parent.parent / "Backtest" / "codes"
            backtest_codes_dir.mkdir(parents=True, exist_ok=True)
            
            # Save Python file
            python_file = backtest_codes_dir / f"{base_filename}.py"
            counter = 1
            while python_file.exists():
                python_file = backtest_codes_dir / f"{base_filename}_{counter}.py"
                counter += 1
            
            with open(python_file, 'w', encoding='utf-8') as f:
                f.write(strategy_code)
            
            # Also save the canonical JSON for reference
            json_file = python_file.with_suffix('.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(canonical_json, f, indent=2)
            
            logger.info(f"Strategy code saved to: {python_file}")
            
            # Update strategy record if strategy_id provided
            if strategy_id:
                try:
                    strategy = Strategy.objects.get(id=strategy_id)
                    # Store the file path in parameters
                    if not strategy.parameters:
                        strategy.parameters = {}
                    strategy.parameters['generated_code_path'] = str(python_file)
                    strategy.parameters['generated_code_filename'] = python_file.name
                    strategy.save(update_fields=['parameters'])
                    logger.info(f"Updated strategy {strategy_id} with generated code path")
                except Strategy.DoesNotExist:
                    logger.warning(f"Strategy {strategy_id} not found for update")
            
            return Response({
                'success': True,
                'strategy_code': strategy_code,
                'file_path': str(python_file),
                'file_name': python_file.name,
                'json_file_path': str(json_file),
                'strategy_id': strategy_id,
                'message': 'Executable strategy code generated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error in generate_executable_code: {e}", exc_info=True)
            return Response({
                'error': 'Failed to generate executable code',
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
    
    @action(detail=False, methods=['post'])
    def validate_strategy_with_ai(self, request):
        """
        Validate a strategy using AI-powered analysis with conversation memory
        
        This endpoint uses the StrategyValidatorBot to analyze strategy text,
        providing canonicalized steps, classification, and AI recommendations.
        Now supports conversation memory to track validation history.
        
        Expected payload:
        {
            "strategy_text": "Buy when RSI < 30, sell when RSI > 70...",
            "input_type": "auto",  # or "numbered", "freetext", "url"
            "use_gemini": true,
            "strict_mode": false,
            "session_id": "chat_abc123",  # optional, for conversation memory
            "use_context": true  # optional, use conversation history
        }
        
        Returns:
        - Canonicalized steps
        - Strategy classification
        - AI-powered recommendations
        - Confidence level
        - Next actions
        - Canonical JSON schema
        - Session ID (new or existing)
        """
        serializer = StrategyAIValidationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            strategy_text = data['strategy_text']
            input_type = data.get('input_type', 'auto')
            use_gemini = data.get('use_gemini', True)
            strict_mode = data.get('strict_mode', False)
            session_id = data.get('session_id')
            use_context = data.get('use_context', True)
            
            # Import the validator and conversation manager
            try:
                from Strategy.strategy_validator import StrategyValidatorBot
                from Strategy.conversation_manager import ConversationManager
            except ImportError as e:
                return Response({
                    'error': 'Strategy validator not available',
                    'details': str(e)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Get username and user from authenticated user or default
            username = request.user.username if request.user.is_authenticated else "api_user"
            user = request.user if request.user.is_authenticated else None
            
            # Initialize or retrieve conversation manager
            conv_manager = ConversationManager(session_id=session_id, user=user)
            
            # Store user's validation request in conversation
            conv_manager.add_user_message(
                f"Validate strategy: {strategy_text[:200]}...",
                metadata={
                    'action': 'validate_strategy',
                    'input_type': input_type,
                    'use_context': use_context
                }
            )
            
            # Initialize validator bot with conversation context
            logger.info(f"Initializing StrategyValidatorBot for user: {username}, session: {conv_manager.session_id}")
            bot = StrategyValidatorBot(
                username=username,
                strict_mode=strict_mode,
                use_gemini=use_gemini,
                session_id=conv_manager.session_id,
                user=user
            )
            
            # Process the strategy
            logger.info(f"Processing strategy: {strategy_text[:100]}...")
            result = bot.process_input(strategy_text, input_type)
            
            logger.info(f"Validation result status: {result.get('status')}")
            
            # ✨ NEW: Let AI format the response with full freedom
            if use_gemini and result.get('status') == 'success':
                try:
                    # Give AI opportunity to provide custom formatted response
                    result = bot.gemini.generate_formatted_validation_response(
                        strategy_text=strategy_text,
                        validation_result=result,
                        use_context=use_context
                    )
                except Exception as e:
                    logger.warning(f"Could not generate custom AI formatting: {e}")
                    # Continue with structured response
            
            # Store AI's validation result in conversation
            ai_summary = f"Validation {result.get('status')}: {result.get('classification', 'N/A')}"
            conv_manager.add_ai_message(
                ai_summary,
                metadata={
                    'action': 'validation_result',
                    'status': result.get('status'),
                    'confidence': result.get('confidence'),
                    'has_custom_format': 'formatted_response' in result,
                    'full_result': result
                }
            )
            
            # Add session info to result
            result['session_id'] = conv_manager.session_id
            result['message_count'] = conv_manager.get_session().message_count
            result['context_used'] = use_context
            
            # Return the complete AI analysis with conversation tracking
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in validate_strategy_with_ai: {e}")
            logger.error(traceback.format_exc())
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def create_strategy_with_ai(self, request):
        """
        Create a new strategy using AI-powered validation with conversation memory
        
        This endpoint combines strategy creation with AI analysis:
        1. Validates and analyzes the strategy text using AI
        2. Creates a Strategy record with the canonical JSON
        3. Optionally creates a linked StrategyTemplate
        4. Optionally saves canonical JSON to Backtest/codes/
        5. Tracks the entire creation process in conversation memory
        
        Expected payload:
        {
            "strategy_text": "Buy when RSI < 30...",
            "input_type": "auto",
            "name": "RSI Strategy",  # optional, auto-generated if not provided
            "description": "...",  # optional
            "template_id": 1,  # optional
            "tags": ["momentum", "rsi"],  # optional
            "use_gemini": true,
            "strict_mode": false,
            "save_to_backtest": false,
            "session_id": "chat_abc123",  # optional, for conversation memory
            "use_context": true  # optional, use conversation history
        }
        
        Returns:
        - Created strategy data
        - Complete AI validation results
        - Template info (if auto-created)
        - File path (if saved to Backtest/codes/)
        - Session ID for tracking
        """
        serializer = StrategyCreateWithAIRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            strategy_text = data['strategy_text']
            input_type = data.get('input_type', 'auto')
            use_gemini = data.get('use_gemini', True)
            strict_mode = data.get('strict_mode', False)
            save_to_backtest = data.get('save_to_backtest', False)
            session_id = data.get('session_id')
            use_context = data.get('use_context', True)
            
            # Import the validator and conversation manager
            try:
                from Strategy.strategy_validator import StrategyValidatorBot
                from Strategy.conversation_manager import ConversationManager
            except ImportError as e:
                return Response({
                    'error': 'Strategy validator not available',
                    'details': str(e)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Get username and user
            username = request.user.username if request.user.is_authenticated else "api_user"
            user = request.user if request.user.is_authenticated else None
            
            # Initialize or retrieve conversation manager
            conv_manager = ConversationManager(session_id=session_id, user=user)
            
            # Store user's create request in conversation
            conv_manager.add_user_message(
                f"Create strategy: {strategy_text[:200]}...",
                metadata={
                    'action': 'create_strategy',
                    'input_type': input_type,
                    'use_context': use_context,
                    'name': data.get('name', 'auto-generated'),
                    'tags': data.get('tags', [])
                }
            )
            
            # Initialize and run AI validation with conversation context
            logger.info(f"Creating strategy with AI validation for user: {username}, session: {conv_manager.session_id}")
            bot = StrategyValidatorBot(
                username=username,
                strict_mode=strict_mode,
                use_gemini=use_gemini,
                session_id=conv_manager.session_id,
                user=user
            )
            
            ai_result = bot.process_input(strategy_text, input_type)
            
            # Check if validation was successful
            if ai_result.get('status') != 'success':
                # Store failure in conversation
                error_message = ai_result.get('message', 'Unknown error')
                conv_manager.add_ai_message(
                    f"Strategy validation failed: {error_message}",
                    metadata={
                        'action': 'creation_failed',
                        'status': ai_result.get('status'),
                        'result': ai_result
                    }
                )
                return Response({
                    'error': 'Strategy validation failed',
                    'message': error_message,
                    'details': ai_result.get('details', ''),
                    'validation_result': ai_result,
                    'session_id': conv_manager.session_id,
                    'suggestions': [
                        'Ensure your strategy description is clear and specific',
                        'Include entry and exit signal descriptions',
                        'Specify what indicators or conditions to use',
                        'Try regenerating or modifying the strategy description'
                    ]
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract canonical JSON
            import json
            canonical_json_str = ai_result.get('canonical_json', '{}')
            try:
                canonical_data = json.loads(canonical_json_str)
            except json.JSONDecodeError:
                canonical_data = {}
            
            # Generate strategy name if not provided
            strategy_name = data.get('name')
            if not strategy_name:
                strategy_name = canonical_data.get('title', 'AI Generated Strategy')
            
            # Get or create template
            template = None
            auto_created_template = False
            template_id = data.get('template_id')
            
            if template_id:
                try:
                    template = StrategyTemplate.objects.get(id=template_id)
                except StrategyTemplate.DoesNotExist:
                    return Response({
                        'error': 'Template not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Extract metadata from AI result
            classification = ai_result.get('classification_detail', {})
            strategy_type = classification.get('type', '')
            risk_tier = (classification.get('risk_tier', '') or '')[:20]
            timeframe = (canonical_data.get('metadata', {}).get('timeframe', '') or '')[:20]
            
            # Parse optional numeric fields
            expected_return = None
            max_drawdown = None
            try:
                if 'expected_return' in canonical_data.get('metadata', {}):
                    expected_return = float(canonical_data['metadata']['expected_return'])
            except (ValueError, TypeError):
                pass
            
            try:
                if 'max_drawdown' in canonical_data.get('metadata', {}):
                    max_drawdown = float(canonical_data['metadata']['max_drawdown'])
            except (ValueError, TypeError):
                pass
            
            # Handle duplicate name/version constraint
            # Check if strategy with this name already exists and find next available version
            base_name = strategy_name
            version_num = 1
            existing = Strategy.objects.filter(name=strategy_name, version='1.0.0').first()
            if existing:
                # Find the highest version number for this strategy name
                existing_strategies = Strategy.objects.filter(name__startswith=base_name)
                version_numbers = []
                for strat in existing_strategies:
                    try:
                        # Parse version string like "1.0.0" to extract major version
                        parts = str(strat.version).split('.')
                        version_numbers.append(int(parts[0]))
                    except (ValueError, IndexError):
                        pass
                
                version_num = max(version_numbers) + 1 if version_numbers else 1
                strategy_name = f"{base_name} v{version_num}"
            
            version_str = f"{version_num}.0.0"
            
            # Create the Strategy record
            strategy = Strategy.objects.create(
                name=strategy_name,
                version=version_str,
                description=data.get('description', canonical_data.get('description', '')),
                template=template,
                strategy_code=canonical_json_str,  # Store canonical JSON as code
                parameters=canonical_data.get('metadata', {}),
                tags=data.get('tags', classification.get('primary_instruments', [])),
                timeframe=timeframe,
                risk_level=risk_tier,
                expected_return=expected_return,
                max_drawdown=max_drawdown,
                created_by=request.user if request.user.is_authenticated else None
            )
            
            logger.info(f"Created strategy {strategy.id}: {strategy.name}")
            
            # Auto-create template if not provided
            if not template:
                try:
                    template_name = f"Template: {strategy_name}"
                    counter = 1
                    while StrategyTemplate.objects.filter(name=template_name).exists():
                        template_name = f"Template: {strategy_name} ({counter})"
                        counter += 1
                    
                    template = StrategyTemplate.objects.create(
                        name=template_name,
                        description=f"Auto-generated from AI analysis: {canonical_data.get('description', '')}",
                        category=strategy_type or 'custom',
                        template_code=canonical_json_str,
                        parameters_schema=canonical_data.get('metadata', {}),
                        is_active=True,
                        is_system_template=False,
                        linked_strategy=strategy,
                        latest_strategy_code=canonical_json_str,
                        latest_parameters=canonical_data.get('metadata', {}),
                        chat_history=[{
                            'timestamp': timezone.now().isoformat(),
                            'message': f'Strategy created with AI validation. Confidence: {ai_result.get("confidence")}',
                            'user': username
                        }],
                        created_by=request.user if request.user.is_authenticated else None
                    )
                    
                    strategy.template = template
                    strategy.save(update_fields=['template'])
                    auto_created_template = True
                    
                    logger.info(f"Auto-created template {template.id} for strategy {strategy.id}")
                except Exception as e:
                    logger.warning(f"Failed to auto-create template: {e}")
            
            # Link strategy to conversation session
            conv_manager.link_strategy(strategy.id)
            
            # Store AI's creation result in conversation
            ai_summary = f"Successfully created strategy '{strategy.name}' (ID: {strategy.id}). Classification: {classification.get('type', 'N/A')}, Risk: {risk_tier}"
            conv_manager.add_ai_message(
                ai_summary,
                metadata={
                    'action': 'strategy_created',
                    'strategy_id': strategy.id,
                    'strategy_name': strategy.name,
                    'classification': classification,
                    'confidence': ai_result.get('confidence')
                }
            )
            
            # Save to Backtest/codes/ if requested
            saved_file_path = None
            if save_to_backtest:
                try:
                    from datetime import datetime
                    import re
                    
                    # Generate filename from strategy name
                    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', strategy_name.lower())
                    words = clean_name.split()[:8]
                    base_filename = "_".join(words) if words else f"strategy_{strategy.id}"
                    
                    # Create directory and file path
                    backtest_codes_dir = PARENT_DIR / "Backtest" / "codes"
                    backtest_codes_dir.mkdir(parents=True, exist_ok=True)
                    
                    filepath = backtest_codes_dir / f"{base_filename}.json"
                    counter = 1
                    while filepath.exists():
                        filepath = backtest_codes_dir / f"{base_filename}_{counter}.json"
                        counter += 1
                    
                    # Save canonical JSON
                    with open(filepath, 'w') as f:
                        json.dump(canonical_data, f, indent=2)
                    
                    saved_file_path = str(filepath)
                    logger.info(f"Saved canonical JSON to: {filepath}")
                except Exception as e:
                    logger.warning(f"Failed to save to Backtest/codes/: {e}")
            
            # Prepare response
            strategy_serializer = StrategySerializer(strategy)
            response_data = {
                'strategy': strategy_serializer.data,
                'ai_validation': ai_result,
                'success': True,
                'session_id': conv_manager.session_id,
                'message_count': conv_manager.get_session().message_count
            }
            
            if auto_created_template:
                response_data['auto_created_template'] = {
                    'id': template.id,
                    'name': template.name,
                    'message': 'Template automatically created for tracking strategy evolution'
                }
            
            if saved_file_path:
                response_data['saved_to_file'] = {
                    'path': saved_file_path,
                    'message': 'Canonical JSON saved to Backtest/codes/'
                }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error in create_strategy_with_ai: {e}")
            logger.error(traceback.format_exc())
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['put', 'patch'])
    def update_strategy_with_ai(self, request, pk=None):
        """
        Update an existing strategy using AI-powered validation with conversation memory
        
        This endpoint allows editing a strategy with AI re-validation:
        1. Retrieves existing strategy by ID
        2. Re-validates updated strategy text using AI
        3. Updates the strategy record
        4. Updates linked template's chat history
        5. Tracks the update process in conversation memory
        
        Expected payload:
        {
            "strategy_text": "Updated strategy description...",
            "input_type": "auto",
            "use_gemini": true,
            "strict_mode": false,
            "update_description": "What changed in this update",
            "session_id": "chat_abc123",  # optional, for conversation memory
            "use_context": true  # optional, use conversation history
        }
        """
        # Get the existing strategy
        try:
            strategy = Strategy.objects.get(id=pk)
        except Strategy.DoesNotExist:
            return Response({
                'error': 'Strategy not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = StrategyAIValidationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            strategy_text = data['strategy_text']
            input_type = data.get('input_type', 'auto')
            use_gemini = data.get('use_gemini', True)
            strict_mode = data.get('strict_mode', False)
            update_description = request.data.get('update_description', 'Strategy updated via API')
            session_id = data.get('session_id')
            use_context = data.get('use_context', True)
            
            # Import validator and conversation manager
            try:
                from Strategy.strategy_validator import StrategyValidatorBot
                from Strategy.conversation_manager import ConversationManager
            except ImportError as e:
                return Response({
                    'error': 'Strategy validator not available',
                    'details': str(e)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Get username and user
            username = request.user.username if request.user.is_authenticated else "api_user"
            user = request.user if request.user.is_authenticated else None
            
            # Initialize or retrieve conversation manager
            conv_manager = ConversationManager(session_id=session_id, user=user)
            
            # Link to existing strategy
            conv_manager.link_strategy(strategy.id)
            
            # Store user's update request in conversation
            conv_manager.add_user_message(
                f"Update strategy '{strategy.name}' (ID: {strategy.id}): {update_description}. New definition: {strategy_text[:200]}...",
                metadata={
                    'action': 'update_strategy',
                    'strategy_id': strategy.id,
                    'update_description': update_description,
                    'use_context': use_context
                }
            )
            
            # Run AI validation with conversation context
            logger.info(f"Updating strategy {pk} with AI validation, session: {conv_manager.session_id}")
            bot = StrategyValidatorBot(
                username=username,
                strict_mode=strict_mode,
                use_gemini=use_gemini,
                session_id=conv_manager.session_id,
                user=user
            )
            
            ai_result = bot.process_input(strategy_text, input_type)
            
            # Check validation status
            if ai_result.get('status') != 'success':
                # Store failure in conversation
                conv_manager.add_ai_message(
                    f"Strategy update validation failed: {ai_result.get('message', 'Unknown error')}",
                    metadata={
                        'action': 'update_failed',
                        'status': ai_result.get('status'),
                        'result': ai_result
                    }
                )
                return Response({
                    'error': 'Strategy validation failed',
                    'validation_result': ai_result,
                    'session_id': conv_manager.session_id
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract canonical JSON
            import json
            canonical_json_str = ai_result.get('canonical_json', '{}')
            try:
                canonical_data = json.loads(canonical_json_str)
            except json.JSONDecodeError:
                canonical_data = {}
            
            # Update strategy
            classification = ai_result.get('classification_detail', {})
            strategy.strategy_code = canonical_json_str
            strategy.parameters = canonical_data.get('metadata', {})
            strategy.risk_level = (classification.get('risk_tier', strategy.risk_level) or '')[:20]
            strategy.timeframe = (canonical_data.get('metadata', {}).get('timeframe', strategy.timeframe) or '')[:20]
            
            # Update optional numeric fields if present
            if 'expected_return' in canonical_data.get('metadata', {}):
                try:
                    strategy.expected_return = float(canonical_data['metadata']['expected_return'])
                except (ValueError, TypeError):
                    pass
            
            if 'max_drawdown' in canonical_data.get('metadata', {}):
                try:
                    strategy.max_drawdown = float(canonical_data['metadata']['max_drawdown'])
                except (ValueError, TypeError):
                    pass
            
            strategy.save()
            
            logger.info(f"Updated strategy {strategy.id}")
            
            # Store successful update in conversation
            ai_summary = f"Successfully updated strategy '{strategy.name}' (ID: {strategy.id}). {update_description}"
            conv_manager.add_ai_message(
                ai_summary,
                metadata={
                    'action': 'strategy_updated',
                    'strategy_id': strategy.id,
                    'update_description': update_description,
                    'classification': classification,
                    'confidence': ai_result.get('confidence')
                }
            )
            
            # Update template chat history if linked
            if strategy.template:
                try:
                    chat_entry = {
                        'timestamp': timezone.now().isoformat(),
                        'message': update_description,
                        'user': username,
                        'confidence': ai_result.get('confidence'),
                        'warnings': ai_result.get('warnings', [])
                    }
                    strategy.template.chat_history.append(chat_entry)
                    
                    # Update template code
                    strategy.template.latest_strategy_code = canonical_json_str
                    strategy.template.latest_parameters = canonical_data.get('metadata', {})
                    strategy.template.save()
                    
                    logger.info(f"Updated template {strategy.template.id} chat history")
                except Exception as e:
                    logger.warning(f"Failed to update template: {e}")
            
            # Prepare response
            strategy_serializer = StrategySerializer(strategy)
            response_data = {
                'strategy': strategy_serializer.data,
                'ai_validation': ai_result,
                'success': True,
                'message': 'Strategy updated successfully',
                'session_id': conv_manager.session_id,
                'message_count': conv_manager.get_session().message_count
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in update_strategy_with_ai: {e}")
            logger.error(traceback.format_exc())
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


class StrategyChatViewSet(viewsets.ModelViewSet):
    """ViewSet for managing chat sessions with AI conversation memory"""
    queryset = StrategyChat.objects.all()
    permission_classes = [AllowAny]
    lookup_field = 'session_id'  # Allow lookup by session_id instead of pk
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail views"""
        if self.action == 'list':
            return StrategyChatListSerializer
        return StrategyChatSerializer
    
    def get_queryset(self):
        """Filter chat sessions by user if authenticated"""
        queryset = StrategyChat.objects.all()
        
        # Filter by user
        if self.request.user.is_authenticated:
            user_filter = self.request.query_params.get('my_sessions', None)
            if user_filter:
                queryset = queryset.filter(user=self.request.user)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by strategy
        strategy_id = self.request.query_params.get('strategy_id', None)
        if strategy_id:
            queryset = queryset.filter(strategy_id=strategy_id)
        
        return queryset.order_by('-updated_at')
    
    @action(detail=False, methods=['post'])
    def chat(self, request):
        """
        Send a message to the AI and get a response with conversation memory.
        
        Expected payload:
        {
            "message": "User's message",
            "session_id": "optional_existing_session_id",
            "strategy_id": 123,  // optional
            "use_context": true  // optional, default true
        }
        
        Returns:
        {
            "session_id": "chat_abc123",
            "message": "AI's response",
            "message_count": 5,
            "context_used": true
        }
        """
        serializer = ChatMessageRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            user_message = data['message']
            session_id = data.get('session_id')
            strategy_id = data.get('strategy_id')
            use_context = data.get('use_context', True)
            
            # Get or create conversation manager
            try:
                from Strategy.conversation_manager import ConversationManager
                from Strategy.gemini_strategy_integrator import GeminiStrategyIntegrator
            except ImportError as e:
                return Response({
                    'error': 'Conversation manager not available',
                    'details': str(e)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Get user
            user = request.user if request.user.is_authenticated else None
            
            # Initialize or retrieve conversation
            conv_manager = ConversationManager(session_id=session_id, user=user)
            
            # Link to strategy if provided
            if strategy_id:
                conv_manager.link_strategy(strategy_id)
            
            # Initialize AI integrator with conversation context
            ai = GeminiStrategyIntegrator(
                session_id=conv_manager.session_id,
                user=user
            )
            
            # Get AI response
            ai_response = ai.chat(user_message, include_strategy_context=use_context)
            
            # Prepare response
            response_data = {
                'session_id': conv_manager.session_id,
                'message': ai_response,
                'message_count': conv_manager.get_session().message_count,
                'context_used': use_context
            }
            
            response_serializer = ChatResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in chat endpoint: {e}")
            logger.error(traceback.format_exc())
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, session_id=None):
        """Get all messages for a specific chat session"""
        session = self.get_object()
        messages = session.messages.all().order_by('created_at')
        serializer = StrategyChatMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def summarize(self, request, session_id=None):
        """Generate an AI summary of the conversation"""
        session = self.get_object()
        
        try:
            from Strategy.gemini_strategy_integrator import GeminiStrategyIntegrator
            
            ai = GeminiStrategyIntegrator(
                session_id=session.session_id,
                user=session.user
            )
            
            summary = ai.summarize_conversation()
            
            return Response({
                'session_id': session.session_id,
                'summary': summary,
                'message_count': session.message_count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return Response({
                'error': 'Failed to generate summary',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def clear(self, request, session_id=None):
        """Clear all messages from a chat session"""
        session = self.get_object()
        
        try:
            from Strategy.conversation_manager import ConversationManager
            
            conv_manager = ConversationManager(
                session_id=session.session_id,
                user=session.user
            )
            conv_manager.clear_conversation()
            
            return Response({
                'success': True,
                'message': 'Conversation cleared',
                'session_id': session.session_id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return Response({
                'error': 'Failed to clear conversation',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, session_id=None):
        """Mark a chat session as inactive"""
        session = self.get_object()
        session.is_active = False
        session.save(update_fields=['is_active'])
        
        serializer = self.get_serializer(session)
        return Response(serializer.data)

