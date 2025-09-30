from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('recent/', views.recent_audit_events, name='recent_audit_events'),
    path('feed/', views.audit_feed, name='audit_feed'),
    # Accept either canonical UUID with hyphens or 32 hex chars without hyphens
    path('correlation/<str:correlation_id>/', views.correlation_detail, name='correlation_detail'),
]