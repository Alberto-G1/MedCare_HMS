from django.urls import path
from . import views

app_name = 'notifications'
urlpatterns = [
    path('', views.notification_list_view, name='notification_list'),
    path('dropdown-data/', views.notification_dropdown_data, name='notification_dropdown_data'),
    path('mark-read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]