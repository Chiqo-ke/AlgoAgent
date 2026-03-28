"""
Authentication API Views for AlgoAgent
=======================================

Views for user authentication, profile management, and AI chat sessions.
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging
import uuid
import sys
from pathlib import Path

from .models import UserProfile, AIContext, ChatSession, ChatMessage
from .serializers import (
    UserSerializer, UserProfileSerializer, UserRegistrationSerializer,
    UserLoginSerializer, AIContextSerializer, ChatSessionSerializer,
    ChatSessionDetailSerializer, ChatMessageSerializer,
    ChatRequestSerializer, ChatResponseSerializer
)

# Add parent directory to path for imports
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

logger = logging.getLogger(__name__)


# ========================================
# Authentication Views
# ========================================

class UserRegistrationView(generics.CreateAPIView):
    """Register a new user"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Create user and return tokens"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class UserLoginView(generics.GenericAPIView):
    """Login user and return JWT tokens"""
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Authenticate user and return tokens"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Update last active
        if hasattr(user, 'profile'):
            user.profile.last_active = timezone.now()
            user.profile.save()
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout user by blacklisting refresh token"""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response({
            'message': 'Logout completed (token may have already been invalidated)'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """Get current authenticated user details"""
    serializer = UserSerializer(request.user)
    profile_serializer = UserProfileSerializer(request.user.profile)
    
    return Response({
        'user': serializer.data,
        'profile': profile_serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """Change the current user's password"""
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not current_password or not new_password:
        return Response({
            'error': 'Both current_password and new_password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    
    # Verify current password
    if not user.check_password(current_password):
        return Response({
            'error': 'Current password is incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate new password length
    if len(new_password) < 8:
        return Response({
            'error': 'Password must be at least 8 characters long'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    logger.info(f"Password changed successfully for user: {user.username}")
    
    return Response({
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)


# ========================================
# User Profile Views
# ========================================

class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user profiles"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users can only access their own profile"""
        return UserProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Get or update current user's profile"""
        profile = get_object_or_404(UserProfile, user=request.user)
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(profile, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_me(self, request):
        """Update current user's profile"""
        profile = get_object_or_404(UserProfile, user=request.user)
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ========================================
# AI Context Views
# ========================================

class AIContextViewSet(viewsets.ModelViewSet):
    """ViewSet for managing AI context sessions"""
    serializer_class = AIContextSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users can only access their own AI contexts"""
        return AIContext.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set the user when creating AI context"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate an AI context"""
        context = self.get_object()
        context.is_active = True
        context.last_used = timezone.now()
        context.save()
        
        serializer = self.get_serializer(context)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate an AI context"""
        context = self.get_object()
        context.is_active = False
        context.save()
        
        serializer = self.get_serializer(context)
        return Response(serializer.data)


# ========================================
# Chat Session Views
# ========================================

class ChatSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing chat sessions"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return ChatSessionDetailSerializer
        return ChatSessionSerializer
    
    def get_queryset(self):
        """Users can only access their own chat sessions"""
        return ChatSession.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set the user and generate session ID when creating"""
        session_id = str(uuid.uuid4())
        serializer.save(user=self.request.user, session_id=session_id)
    
    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """End a chat session"""
        session = self.get_object()
        session.is_active = False
        session.save()
        
        serializer = self.get_serializer(session)
        return Response({
            'message': 'Session ended',
            'session': serializer.data
        })


# ========================================
# AI Chat Agent View
# ========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_chat_view(request):
    """
    Main AI chat endpoint for strategy development
    
    This endpoint handles user messages and interacts with Gemini AI
    to help develop trading strategies.
    """
    serializer = ChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    message = serializer.validated_data['message']
    session_id = serializer.validated_data.get('session_id')
    ai_context_id = serializer.validated_data.get('ai_context_id')
    title = serializer.validated_data.get('title', 'Strategy Development Session')
    
    try:
        # Get or create chat session
        if session_id:
            session = get_object_or_404(ChatSession, session_id=session_id, user=request.user)
        else:
            # Create new session
            session_id = str(uuid.uuid4())
            ai_context = None
            if ai_context_id:
                ai_context = get_object_or_404(AIContext, id=ai_context_id, user=request.user)
            
            session = ChatSession.objects.create(
                user=request.user,
                session_id=session_id,
                title=title,
                ai_context=ai_context
            )
        
        # Build context from AI context if available
        system_context = ""
        if session.ai_context:
            system_context = f"""
User Context:
- Instructions: {session.ai_context.instructions}
- Trading Goals: {request.user.profile.trading_goals if request.user.profile.trading_goals else 'Not specified'}
- Strategy Preferences: {request.user.profile.strategy_preferences if request.user.profile.strategy_preferences else 'Not specified'}
- Risk Tolerance: {request.user.profile.default_risk_tolerance}
- Preferred Timeframe: {request.user.profile.default_timeframe}
"""
        
        # Import Copilot strategy generator (preferred) with Gemini fallback
        try:
            from Backtest.copilot_strategy_generator import CopilotStrategyGenerator
            generator = CopilotStrategyGenerator()
            use_copilot = True
            logger.info("Using GitHub Copilot for chat")
        except Exception as copilot_error:
            logger.warning(f"Copilot unavailable, falling back to Gemini: {copilot_error}")
            from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
            generator = GeminiStrategyGenerator()
            use_copilot = False
        
        # Build conversation history for context
        conversation_history = session.messages if session.messages else []
        
        # Prepare the prompt with full context
        full_prompt = f"""{system_context}

Conversation History:
{chr(10).join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-5:]])}

User: {message}

Please help the user develop their trading strategy. You can:
1. Ask clarifying questions about their strategy requirements
2. Suggest strategy approaches based on their goals
3. Generate strategy code when ready
4. Explain strategy concepts and indicators
"""
        
        # Get AI response
        if use_copilot:
            # Copilot uses a different method for chat
            ai_response = generator.generate_chat_response(full_prompt)
        else:
            # Gemini uses chat method
            ai_response = generator.chat(full_prompt)
        
        # Save messages
        user_msg = {
            'role': 'user',
            'content': message,
            'timestamp': timezone.now().isoformat()
        }
        ai_msg = {
            'role': 'assistant',
            'content': ai_response,
            'timestamp': timezone.now().isoformat()
        }
        
        session.messages.append(user_msg)
        session.messages.append(ai_msg)
        session.updated_at = timezone.now()
        session.save()
        
        # Create ChatMessage records
        ChatMessage.objects.create(
            session=session,
            role='user',
            content=message
        )
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=ai_response
        )
        
        response_serializer = ChatResponseSerializer(data={
            'session_id': session.session_id,
            'title': session.title,
            'user_message': message,
            'ai_response': ai_response
        })
        response_serializer.is_valid(raise_exception=True)
        
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"AI chat error: {str(e)}", exc_info=True)
        return Response({
            'error': 'Failed to process chat message',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'service': 'auth_api',
        'user': request.user.username if request.user.is_authenticated else 'anonymous',
        'timestamp': timezone.now()
    })


# ========================================
# Frontend Error Logging
# ========================================

frontend_logger = logging.getLogger('frontend')

@api_view(['POST'])
@permission_classes([AllowAny])
def frontend_error_log(request):
    """
    Receive error/warn logs from the React frontend.
    Called by src/lib/logger.ts sendErrorToBackend().
    Logs are written to logs/frontend_errors.log and Django console.
    """
    try:
        data = request.data
        level = data.get('level', 'error')
        category = data.get('category', 'general')
        message = data.get('message', '')
        url = data.get('url', '')
        user_agent = data.get('user_agent', '')
        error_message = data.get('error_message')
        error_stack = data.get('error_stack')
        context = data.get('context')
        timestamp = data.get('timestamp')

        log_line = (
            f"[FRONTEND:{category.upper()}] {message} | "
            f"url={url} | ts={timestamp}"
        )
        if error_message:
            log_line += f" | error={error_message}"

        if level == 'warn':
            frontend_logger.warning(log_line, extra={
                'context': context,
                'user_agent': user_agent,
                'stack': error_stack,
            })
        else:
            frontend_logger.error(log_line, extra={
                'context': context,
                'user_agent': user_agent,
                'stack': error_stack,
            })
            if error_stack:
                frontend_logger.error(f"[FRONTEND:STACK] {error_stack}")

        return Response({'status': 'logged'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Failed to process frontend error log: {e}")
        return Response({'status': 'error'}, status=status.HTTP_400_BAD_REQUEST)


# ========================================
# Admin: Subscription Management
# ========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_subscription_view(request):
    """
    Staff-only endpoint to upgrade or downgrade a user's subscription plan.

    POST /api/auth/admin/set-subscription/
    Body: { "user_id": <int>, "plan": "free" | "premium" }
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'You do not have permission to perform this action.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    user_id = request.data.get('user_id')
    plan = request.data.get('plan')

    valid_plans = [UserProfile.PLAN_FREE, UserProfile.PLAN_PREMIUM]
    if plan not in valid_plans:
        return Response(
            {'error': f'Invalid plan. Choose one of: {valid_plans}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not user_id:
        return Response(
            {'error': 'user_id is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        target_user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': f'User with id {user_id} not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    old_plan = profile.subscription_plan
    profile.subscription_plan = plan
    profile.subscription_updated_at = timezone.now()
    profile.save(update_fields=['subscription_plan', 'subscription_updated_at'])

    logger.info(
        f"[ADMIN] {request.user.username} changed subscription for "
        f"{target_user.username} (id={user_id}): {old_plan} → {plan}"
    )

    return Response({
        'message': f"Subscription updated for {target_user.username}.",
        'user_id': user_id,
        'username': target_user.username,
        'old_plan': old_plan,
        'new_plan': plan,
        'updated_at': profile.subscription_updated_at,
    }, status=status.HTTP_200_OK)
