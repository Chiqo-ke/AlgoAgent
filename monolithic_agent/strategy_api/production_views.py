"""
Production-Hardened Strategy API Views
======================================

Enhanced API views integrating:
- Pydantic validation (canonical_schema_v2)
- State management (state_manager)
- Safe tools (safe_tools)
- Output validation (output_validator)
- Sandbox orchestration (sandbox_orchestrator)
- Git patch management (git_patch_manager)
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.shortcuts import get_object_or_404
from pathlib import Path
import logging
import sys
import json
import traceback
from typing import Dict, Any

# Set up logger FIRST (before any other imports that might use it)
logger = logging.getLogger(__name__)

# Add Backtest module to path
BACKTEST_DIR = Path(__file__).parent.parent / "Backtest"
sys.path.insert(0, str(BACKTEST_DIR))

# Import production components
try:
    from canonical_schema_v2 import (
        StrategyDefinition, Signal, GeneratedCode, 
        ExecutionResult, OrderSide, OrderType, SizeType
    )
    from state_manager import StateManager, StrategyStatus
    from safe_tools import SafeTools, ReadFileRequest, WriteFileRequest
    from output_validator import OutputValidator, CodeSafetyChecker
    from sandbox_orchestrator import SandboxRunner, SandboxConfig
    from git_patch_manager import GitPatchManager, PatchWorkflow
    
    PRODUCTION_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import production components: {e}")
    PRODUCTION_COMPONENTS_AVAILABLE = False

# Import existing models and serializers
from strategy_api.models import Strategy, StrategyValidation
from strategy_api.serializers import StrategySerializer, StrategyValidationSerializer

# Initialize production components
state_manager = None
safe_tools = None
output_validator = None
sandbox_runner = None
git_manager = None

if PRODUCTION_COMPONENTS_AVAILABLE:
    workspace_root = Path(__file__).parent.parent
    
    # Initialize each component individually with error handling
    try:
        state_manager = StateManager(db_path=str(workspace_root / "production_state.db"))
        logger.info("[OK] StateManager initialized")
    except Exception as e:
        logger.warning(f"StateManager initialization failed: {e}")
    
    try:
        safe_tools = SafeTools(workspace_root=workspace_root / "codes")
        logger.info("[OK] SafeTools initialized")
    except Exception as e:
        logger.warning(f"SafeTools initialization failed: {e}")
    
    try:
        output_validator = OutputValidator(strict_safety=True)
        logger.info("[OK] OutputValidator initialized")
    except Exception as e:
        logger.warning(f"OutputValidator initialization failed: {e}")
    
    try:
        sandbox_runner = SandboxRunner(workspace_root=workspace_root)
        logger.info("[OK] SandboxRunner initialized")
    except Exception as e:
        logger.warning(f"SandboxRunner initialization failed: {e}")
    
    try:
        git_manager = GitPatchManager(repo_path=workspace_root / "codes")
        logger.info("[OK] GitPatchManager initialized")
    except Exception as e:
        logger.warning(f"GitPatchManager initialization failed (git repo may not exist): {e}")


class ProductionStrategyViewSet(viewsets.ViewSet):
    """
    Production-hardened strategy management endpoints
    
    New endpoints:
    - POST /strategies/validate-schema/ - Validate with Pydantic
    - POST /strategies/validate-code/ - Check for dangerous patterns
    - POST /strategies/sandbox-test/ - Run in Docker sandbox
    - GET /strategies/{id}/lifecycle/ - Get full state history
    - POST /strategies/{id}/deploy/ - Deploy with git commit
    - POST /strategies/{id}/rollback/ - Rollback to previous version
    """
    
    permission_classes = [AllowAny]
    
    def _check_components(self, required_components=None):
        """
        Check if required production components are available
        
        Args:
            required_components: List of component names to check (e.g., ['state_manager', 'output_validator'])
                               If None, checks if ANY components are available
        """
        if not PRODUCTION_COMPONENTS_AVAILABLE:
            return Response({
                'error': 'Production components not available',
                'message': 'Required production hardening components are not installed'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        if required_components:
            missing = []
            component_map = {
                'state_manager': state_manager,
                'safe_tools': safe_tools,
                'output_validator': output_validator,
                'sandbox_runner': sandbox_runner,
                'git_manager': git_manager
            }
            
            for comp in required_components:
                if component_map.get(comp) is None:
                    missing.append(comp)
            
            if missing:
                return Response({
                    'error': 'Required components not available',
                    'missing_components': missing,
                    'message': f'The following components are required but not initialized: {", ".join(missing)}'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return None
    
    @action(detail=False, methods=['post'], url_path='validate-schema')
    def validate_schema(self, request):
        """
        Validate strategy JSON against Pydantic schema
        
        POST /api/strategies/validate-schema/
        {
            "name": "RSI_Reversal",
            "description": "RSI reversal strategy",
            "parameters": {...},
            "indicators": {"rsi": {"period": 14}},
            "entry_rules": ["rsi < 30"],
            "exit_rules": ["rsi > 70"]
        }
        
        Returns validation errors or validated strategy
        """
        # Schema validation only needs Pydantic (already imported)
        try:
            # Validate with Pydantic
            strategy_def = StrategyDefinition.model_validate(request.data)
            
            # Return validated data
            return Response({
                'status': 'valid',
                'message': 'Strategy schema is valid',
                'validated_data': strategy_def.model_dump(),
                'schema_version': strategy_def.schema_version
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Return validation errors
            error_details = []
            if hasattr(e, 'errors'):
                error_details = e.errors()
            
            return Response({
                'status': 'invalid',
                'message': 'Strategy schema validation failed',
                'errors': error_details,
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='validate-code')
    def validate_code(self, request):
        """
        Validate generated code for dangerous patterns
        
        POST /api/strategies/validate-code/
        {
            "code": "class MyStrategy: ...",
            "strict_mode": true
        }
        
        Returns safety check results
        """
        error_response = self._check_components(['output_validator'])
        if error_response:
            return error_response
        
        try:
            code = request.data.get('code', '')
            strict_mode = request.data.get('strict_mode', True)
            
            if not code:
                return Response({
                    'error': 'No code provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate code with safety checker
            is_safe, violations = output_validator.safety_checker.check(code)
            
            if not is_safe:
                return Response({
                    'status': 'rejected',
                    'safe': False,
                    'message': 'Code contains dangerous patterns',
                    'issues': violations,
                    'severity': 'high' if strict_mode else 'medium'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Format code if safe
            formatted_code = output_validator.formatter.format(code)
            
            return Response({
                'status': 'validated',
                'safe': True,
                'message': 'Code passed all safety checks',
                'formatted_code': formatted_code,
                'checks_passed': [
                    'No dangerous imports',
                    'No system commands',
                    'No eval/exec usage',
                    'Syntax valid',
                    'AST analysis passed'
                ]
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in validate_code: {e}")
            return Response({
                'error': 'Code validation failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='sandbox-test')
    def sandbox_test(self, request):
        """
        Run strategy code in isolated Docker sandbox
        
        POST /api/strategies/sandbox-test/
        {
            "strategy_id": 123,
            "timeout": 60,
            "resource_limits": {
                "cpu": "0.5",
                "memory": "512m"
            }
        }
        
        Returns execution results
        """
        error_response = self._check_components()
        if error_response:
            return error_response
        
        try:
            strategy_id = request.data.get('strategy_id')
            timeout = request.data.get('timeout', 60)
            limits = request.data.get('resource_limits', {})
            
            # Get strategy from Django
            strategy = get_object_or_404(Strategy, id=strategy_id)
            
            if not strategy.strategy_code:
                return Response({
                    'error': 'Strategy has no code to test'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update state
            state_record = state_manager.register_strategy(
                name=strategy.name,
                json_path=f"strategies/{strategy.name}.json",
                py_path=f"strategies/{strategy.name}.py"
            )
            state_manager.update_status(
                name=strategy.name,
                status=StrategyStatus.TESTING
            )
            
            # Save code to temporary file
            temp_file = Path(f"temp_{strategy.name}.py")
            safe_tools.write_file(
                WriteFileRequest(
                    path=str(temp_file),
                    content=strategy.strategy_code
                )
            )
            
            try:
                # Run in sandbox
                config = SandboxConfig(
                    cpu_limit=limits.get('cpu', '0.5'),
                    memory_limit=limits.get('memory', '512m'),
                    timeout=timeout
                )
                
                result = sandbox_runner.run_python_script(
                    script_path=f"Backtest/{temp_file}",
                    timeout=timeout
                )
                
                # Update state based on result
                if result.status == "completed" and result.exit_code == 0:
                    state_manager.update_status(
                        name=strategy.name,
                        status=StrategyStatus.PASSED
                    )
                    strategy.status = 'tested'
                    success = True
                else:
                    state_manager.update_status(
                        name=strategy.name,
                        status=StrategyStatus.FAILED,
                        error=result.stderr
                    )
                    success = False
                
                strategy.last_tested = timezone.now()
                strategy.save()
                
                return Response({
                    'status': 'completed' if success else 'failed',
                    'success': success,
                    'execution_time': result.execution_time,
                    'exit_code': result.exit_code,
                    'output': result.stdout,
                    'errors': result.stderr,
                    'timed_out': result.timed_out,
                    'resource_usage': {
                        'max_memory_mb': result.max_memory_mb,
                        'cpu_percent': result.cpu_percent
                    }
                }, status=status.HTTP_200_OK)
                
            finally:
                # Cleanup temp file
                if temp_file.exists():
                    temp_file.unlink()
            
        except Exception as e:
            logger.error(f"Error in sandbox_test: {e}")
            logger.error(traceback.format_exc())
            return Response({
                'error': 'Sandbox test failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='lifecycle')
    def get_lifecycle(self, request, pk=None):
        """
        Get complete lifecycle history for a strategy
        
        GET /api/strategies/{id}/lifecycle/
        
        Returns state tracking and audit log
        """
        error_response = self._check_components()
        if error_response:
            return error_response
        
        try:
            strategy = get_object_or_404(Strategy, id=pk)
            
            # Get from state manager
            try:
                state_record = state_manager.get_strategy(strategy.name)
                audit_log = state_manager.get_audit_log(strategy.name)
                
                return Response({
                    'strategy_id': strategy.id,
                    'name': strategy.name,
                    'current_status': state_record.status if state_record else 'unknown',
                    'lifecycle_tracking': {
                        'generation_attempts': state_record.generation_attempts if state_record else 0,
                        'test_attempts': state_record.test_attempts if state_record else 0,
                        'fix_attempts': state_record.fix_attempts if state_record else 0,
                        'error_count': state_record.error_count if state_record else 0,
                        'last_error': state_record.last_error if state_record else None
                    },
                    'timestamps': {
                        'created_at': state_record.created_at if state_record else None,
                        'last_generation': state_record.last_generation_at if state_record else None,
                        'last_test': state_record.last_test_at if state_record else None,
                        'last_success': state_record.last_success_at if state_record else None
                    },
                    'audit_log': audit_log or []
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'strategy_id': strategy.id,
                    'name': strategy.name,
                    'message': 'No lifecycle tracking data available',
                    'details': str(e)
                }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Error in get_lifecycle: {e}")
            return Response({
                'error': 'Failed to retrieve lifecycle data',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='deploy')
    def deploy(self, request, pk=None):
        """
        Deploy strategy with git commit and state update
        
        POST /api/strategies/{id}/deploy/
        {
            "commit_message": "Deploy RSI strategy v1.0",
            "create_tag": true,
            "tag_version": "v1.0.0"
        }
        
        Creates git commit and updates state to deployed
        """
        error_response = self._check_components()
        if error_response:
            return error_response
        
        try:
            strategy = get_object_or_404(Strategy, id=pk)
            
            # Check if strategy is ready
            state_record = state_manager.get_strategy(strategy.name)
            if state_record and state_record.status != StrategyStatus.PASSED.value:
                return Response({
                    'error': 'Strategy must pass tests before deployment',
                    'current_status': state_record.status,
                    'required_status': 'passed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            commit_message = request.data.get('commit_message', f'Deploy {strategy.name}')
            create_tag = request.data.get('create_tag', False)
            tag_version = request.data.get('tag_version', 'v1.0.0')
            
            # Create deployment branch
            workflow = PatchWorkflow(repo_path=safe_tools.workspace_root)
            branch_info = workflow.start_generation(
                strategy_name=strategy.name,
                purpose='deployment'
            )
            
            # Save strategy code if not already saved
            code_file = safe_tools.workspace_root / f"{strategy.name}.py"
            if strategy.strategy_code:
                with open(code_file, 'w') as f:
                    f.write(strategy.strategy_code)
            
            # Commit the deployment
            workflow.commit_generation(
                strategy_name=strategy.name,
                generated_file=str(code_file),
                message=commit_message
            )
            
            # Finalize (merge to main)
            workflow.finalize_success(branch_info.name)
            
            # Create git tag if requested
            if create_tag:
                git_manager.create_tag(tag_version, f"Release {strategy.name}")
            
            # Update state
            state_manager.update_status(
                name=strategy.name,
                status=StrategyStatus.DEPLOYED
            )
            
            # Update Django model
            strategy.status = 'deployed'
            strategy.version = tag_version if create_tag else strategy.version
            strategy.save()
            
            return Response({
                'status': 'deployed',
                'strategy_id': strategy.id,
                'branch': branch_info.name,
                'commit': git_manager.get_latest_commit(),
                'tag': tag_version if create_tag else None,
                'message': f'Strategy {strategy.name} deployed successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in deploy: {e}")
            logger.error(traceback.format_exc())
            return Response({
                'error': 'Deployment failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='rollback')
    def rollback(self, request, pk=None):
        """
        Rollback strategy to previous version
        
        POST /api/strategies/{id}/rollback/
        {
            "commit_hash": "abc123",  // optional, defaults to previous commit
            "reason": "Bug in production"
        }
        
        Reverts to specified or previous commit
        """
        error_response = self._check_components()
        if error_response:
            return error_response
        
        try:
            strategy = get_object_or_404(Strategy, id=pk)
            
            commit_hash = request.data.get('commit_hash')
            reason = request.data.get('reason', 'Rollback requested via API')
            
            # Create rollback branch
            workflow = PatchWorkflow(repo_path=safe_tools.workspace_root)
            branch_info = workflow.start_generation(
                strategy_name=strategy.name,
                purpose='rollback'
            )
            
            # Revert to commit
            if commit_hash:
                git_manager.revert_to_commit(commit_hash)
            else:
                # Revert to previous commit
                git_manager.revert_last_commit()
            
            # Commit rollback
            workflow.commit_fix(
                strategy_name=strategy.name,
                error_message=reason,
                attempt=1
            )
            
            # Finalize rollback
            workflow.finalize_success(branch_info.name)
            
            # Update state
            state_manager.update_status(
                name=strategy.name,
                status=StrategyStatus.READY
            )
            
            # Update Django model
            strategy.status = 'rolled_back'
            strategy.save()
            
            return Response({
                'status': 'rolled_back',
                'strategy_id': strategy.id,
                'reverted_to': commit_hash or 'previous commit',
                'branch': branch_info.name,
                'reason': reason,
                'message': f'Strategy {strategy.name} rolled back successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in rollback: {e}")
            return Response({
                'error': 'Rollback failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='health')
    def health_check(self, request):
        """
        Check health of production components
        
        GET /api/strategies/health/
        
        Returns status of all production components
        """
        health_status = {
            'overall': 'healthy',
            'components': {}
        }
        
        # Check each component
        try:
            # State Manager
            health_status['components']['state_manager'] = {
                'available': state_manager is not None,
                'strategies_tracked': len(state_manager.list_strategies()) if state_manager else 0
            }
            
            # Safe Tools
            health_status['components']['safe_tools'] = {
                'available': safe_tools is not None,
                'workspace': str(safe_tools.workspace_root) if safe_tools else None
            }
            
            # Output Validator
            health_status['components']['output_validator'] = {
                'available': output_validator is not None,
                'strict_mode': output_validator.safety_checker.strict_mode if output_validator else None
            }
            
            # Sandbox Runner
            health_status['components']['sandbox_runner'] = {
                'available': sandbox_runner is not None,
                'docker_available': sandbox_runner.orchestrator.docker_available if sandbox_runner else False
            }
            
            # Git Manager
            health_status['components']['git_manager'] = {
                'available': git_manager is not None,
                'repo_path': str(git_manager.repo_path) if git_manager else None
            }
            
            # Check if any critical component is missing
            if not all([state_manager, safe_tools, output_validator, sandbox_runner, git_manager]):
                health_status['overall'] = 'degraded'
            
        except Exception as e:
            health_status['overall'] = 'unhealthy'
            health_status['error'] = str(e)
        
        status_code = status.HTTP_200_OK if health_status['overall'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_status, status=status_code)
