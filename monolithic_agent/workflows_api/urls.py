from django.urls import path
from . import views

urlpatterns = [
    path('', views.workflow_list, name='workflow-list'),
]
