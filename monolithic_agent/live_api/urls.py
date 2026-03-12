from django.urls import path
from live_api.views import (
    LiveDataRefreshView,
    LiveDataStatusView,
    LiveSchedulerActivateView,
    LiveSchedulerDeactivateView,
    LiveSchedulerJobsView,
)

app_name = 'live_api'

urlpatterns = [
    # Data endpoints
    path('data/refresh/',  LiveDataRefreshView.as_view(),  name='live-data-refresh'),
    path('data/status/',   LiveDataStatusView.as_view(),   name='live-data-status'),

    # Scheduler endpoints
    path('scheduler/activate/',   LiveSchedulerActivateView.as_view(),   name='live-scheduler-activate'),
    path('scheduler/deactivate/', LiveSchedulerDeactivateView.as_view(), name='live-scheduler-deactivate'),
    path('scheduler/jobs/',       LiveSchedulerJobsView.as_view(),       name='live-scheduler-jobs'),
]
