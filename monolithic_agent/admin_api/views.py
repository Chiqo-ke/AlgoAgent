from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.pagination import PageNumberPagination

from .permissions import IsAdminGroupMember
from .serializers import (
    AdminUserSerializer,
    AdminLiveSessionSerializer,
    AdminBrokerCredentialSerializer,
    AdminStrategySerializer,
    AdminBacktestRunSerializer,
    AdminSymbolSerializer,
    AdminDataRequestSerializer,
    AdminDataCacheSerializer,
    AdminChatSessionSerializer,
    AdminStrategyChatSerializer,
    AdminBacktestAlertSerializer,
)
from auth_api.models import UserProfile, ChatSession
from strategy_api.models import Strategy, StrategyChat
from backtest_api.models import BacktestRun, BacktestAlert
from data_api.models import Symbol, DataRequest, DataCache
from trading_sessions_api.models import BrokerCredential, LiveTradingSession


class AdminPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


# ── System Stats ───────────────────────────────────────────────────────────────

class AdminStatsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminGroupMember]

    def get(self, request):
        today = timezone.now().date()
        yesterday = timezone.now() - timedelta(days=1)

        stats = {
            'users': {
                'total': User.objects.count(),
                'active': User.objects.filter(is_active=True).count(),
                'new_last_24h': User.objects.filter(date_joined__gte=yesterday).count(),
            },
            'strategies': {
                'total': Strategy.objects.count(),
                'by_status': {
                    s: Strategy.objects.filter(status=s).count()
                    for s in ['draft', 'valid', 'invalid', 'active', 'inactive']
                },
            },
            'backtests': {
                'total': BacktestRun.objects.count(),
                'today': BacktestRun.objects.filter(created_at__date=today).count(),
                'by_status': {
                    s: BacktestRun.objects.filter(status=s).count()
                    for s in ['pending', 'running', 'completed', 'failed', 'cancelled']
                },
            },
            'live_sessions': {
                'total': LiveTradingSession.objects.count(),
                'active': LiveTradingSession.objects.filter(status='running').count(),
                'dry_run': LiveTradingSession.objects.filter(dry_run=True).count(),
            },
            'market_data': {
                'symbols': Symbol.objects.count(),
                'active_symbols': Symbol.objects.filter(is_active=True).count(),
                'cached_entries': DataCache.objects.count(),
                'data_requests_total': DataRequest.objects.count(),
            },
            'chats': {
                'auth_sessions': ChatSession.objects.count(),
                'strategy_chats': StrategyChat.objects.count(),
                'active_strategy_chats': StrategyChat.objects.filter(is_active=True).count(),
            },
            'subscriptions': {
                'free': UserProfile.objects.filter(subscription_plan=UserProfile.PLAN_FREE).count(),
                'premium': UserProfile.objects.filter(subscription_plan=UserProfile.PLAN_PREMIUM).count(),
                'total_profiles': UserProfile.objects.count(),
            },
        }
        return Response(stats)


# ── Users ──────────────────────────────────────────────────────────────────────

class AdminUserListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminGroupMember]

    def get(self, request):
        # Optional filter by subscription plan: ?plan=free or ?plan=premium
        plan_filter = request.query_params.get('plan')
        queryset = User.objects.select_related('profile').prefetch_related('groups').order_by('-date_joined')
        if plan_filter in (UserProfile.PLAN_FREE, UserProfile.PLAN_PREMIUM):
            queryset = queryset.filter(profile__subscription_plan=plan_filter)
        paginator = AdminPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminUserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminUserDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminGroupMember]

    def get(self, request, user_id):
        try:
            user = User.objects.select_related('profile').prefetch_related('groups').get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminUserSerializer(user)
        return Response(serializer.data)

    def patch(self, request, user_id):
        """Toggle is_active for a user. Only 'is_active' field is accepted."""
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Prevent admins from deactivating themselves
        if user == request.user:
            return Response({'detail': 'Cannot modify your own account.'}, status=status.HTTP_400_BAD_REQUEST)

        is_active = request.data.get('is_active')
        if is_active is None:
            return Response({'detail': 'is_active field required.'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = bool(is_active)
        user.save(update_fields=['is_active'])
        return Response({'id': user.id, 'username': user.username, 'is_active': user.is_active})


# ── Subscription Management ────────────────────────────────────────────────────

class AdminSubscriptionListView(APIView):
    """GET all users with their subscription plans, sorted by plan then join date."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminGroupMember]

    def get(self, request):
        queryset = User.objects.select_related('profile').prefetch_related('groups').order_by(
            'profile__subscription_plan', '-date_joined'
        )
        paginator = AdminPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminUserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminSubscriptionUpdateView(APIView):
    """PATCH to set a user's subscription plan. Body: {"plan": "free"|"premium"}"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminGroupMember]

    _VALID_PLANS = (UserProfile.PLAN_FREE, UserProfile.PLAN_PREMIUM)

    def patch(self, request, user_id):
        try:
            target_user = User.objects.select_related('profile').get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        plan = request.data.get('plan')
        if plan not in self._VALID_PLANS:
            return Response(
                {'detail': f'Invalid plan. Valid choices: {list(self._VALID_PLANS)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile, _ = UserProfile.objects.get_or_create(user=target_user)
        old_plan = profile.subscription_plan
        profile.subscription_plan = plan
        profile.subscription_updated_at = timezone.now()
        profile.save(update_fields=['subscription_plan', 'subscription_updated_at'])

        return Response({
            'user_id': target_user.id,
            'username': target_user.username,
            'old_plan': old_plan,
            'new_plan': plan,
            'subscription_updated_at': profile.subscription_updated_at,
        })


# ── Live Sessions ──────────────────────────────────────────────────────────────

class AdminLiveSessionListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminGroupMember]

    def get(self, request):
        queryset = LiveTradingSession.objects.select_related('strategy', 'created_by').order_by('-created_at')
        paginator = AdminPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminLiveSessionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# ── Strategies ─────────────────────────────────────────────────────────────────

class AdminStrategyListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminGroupMember]

    def get(self, request):
        queryset = Strategy.objects.select_related('created_by').order_by('-created_at')
        paginator = AdminPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminStrategySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# ── Backtests ──────────────────────────────────────────────────────────────────

class AdminBacktestListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminGroupMember]

    def get(self, request):
        queryset = BacktestRun.objects.select_related('strategy', 'created_by').order_by('-created_at')
        paginator = AdminPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminBacktestRunSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# ── Market Data ────────────────────────────────────────────────────────────────

class AdminMarketDataView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminGroupMember]

    def get(self, request):
        symbols = Symbol.objects.order_by('symbol')
        data_requests = DataRequest.objects.select_related('symbol', 'requested_by').order_by('-created_at')[:50]
        cache_entries = DataCache.objects.select_related('symbol').order_by('-created_at')[:50]

        return Response({
            'symbols': AdminSymbolSerializer(symbols, many=True).data,
            'recent_data_requests': AdminDataRequestSerializer(data_requests, many=True).data,
            'recent_cache_entries': AdminDataCacheSerializer(cache_entries, many=True).data,
        })


# ── AI Chats ───────────────────────────────────────────────────────────────────

class AdminChatListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminGroupMember]

    def get(self, request):
        auth_sessions = ChatSession.objects.select_related('user').order_by('-updated_at')
        strategy_chats = StrategyChat.objects.select_related('user', 'strategy').order_by('-updated_at')
        paginator = AdminPagination()

        auth_page = paginator.paginate_queryset(auth_sessions, request)
        return Response({
            'auth_chat_sessions': AdminChatSessionSerializer(auth_page, many=True).data,
            'strategy_chats': AdminStrategyChatSerializer(strategy_chats[:50], many=True).data,
        })


# ── Broker Credentials ─────────────────────────────────────────────────────────

class AdminBrokerCredentialListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminGroupMember]

    def get(self, request):
        queryset = BrokerCredential.objects.select_related('user').order_by('user__username')
        paginator = AdminPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminBrokerCredentialSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# ── Alerts ─────────────────────────────────────────────────────────────────────

class AdminAlertListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminGroupMember]

    def get(self, request):
        queryset = BacktestAlert.objects.select_related('run').order_by('-timestamp')
        paginator = AdminPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminBacktestAlertSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
