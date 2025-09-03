# accounts/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard redirector
    path('dashboard/', views.dashboard_redirect_view, name='dashboard_redirect'),
    
    # Specific dashboards
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('dashboard/admin/reject/<int:user_id>/', views.reject_user, name='reject_user'),
    path('dashboard/doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('dashboard/receptionist/', views.receptionist_dashboard, name='receptionist_dashboard'),
    path('dashboard/patient/', views.patient_dashboard, name='patient_dashboard'),

    # Staff Management URLs
    path('staff/', views.staff_management_list, name='staff_management_list'),
    
    # Npage for pending staff
    path('staff/pending/', views.pending_staff_list, name='pending_staff_list'),
    
    # page for deactivated staff
    path('staff/deactivated/', views.deactivated_staff_list, name='deactivated_staff_list'),

    # pages for viewing and updating a single staff member
    path('staff/<int:pk>/view/', views.StaffDetailView.as_view(), name='staff_detail'),
    path('staff/<int:pk>/update/', views.StaffUpdateView.as_view(), name='staff_update'),

    path('staff/approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('staff/reject/<int:user_id>/', views.reject_user, name='reject_user'),
    path('staff/toggle/<int:user_id>/', views.toggle_staff_status, name='toggle_staff_status'),

]