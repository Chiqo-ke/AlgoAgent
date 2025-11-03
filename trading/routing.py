"""
WebSocket URL routing for Django Channels
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/backtest/stream/$', consumers.BacktestStreamConsumer.as_asgi()),
]
