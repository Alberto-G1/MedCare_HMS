from django.urls import path
from . import views

app_name = 'reports'
urlpatterns = [
    path('', views.reports_dashboard_view, name='reports_dashboard'),
    path('api/kpis/', views.kpi_summary_api, name='kpi_summary_api'),
    path('api/appointments-over-time/', views.appointments_over_time_api, name='appointments_over_time_api'),
    path('api/revenue-over-time/', views.revenue_over_time_api, name='revenue_over_time_api'),
    path('api/revenue-by-doctor/', views.revenue_by_doctor_api, name='revenue_by_doctor_api'),
    path('api/prescriptions-activity/', views.prescriptions_activity_api, name='prescriptions_activity_api'),
    path('api/user-distribution/', views.user_distribution_api, name='user_distribution_api'),
]