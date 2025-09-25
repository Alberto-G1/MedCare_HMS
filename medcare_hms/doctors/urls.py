from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    # Profile URLs
    path('profile/', views.doctor_profile_view, name='doctor_profile'),
    path('profile/edit/', views.edit_doctor_profile_view, name='edit_doctor_profile'),
    
    # Appointment Management URLs
    path('appointments/', views.doctor_appointments_view, name='doctor_appointments'),
    path('appointments/<int:pk>/', views.appointment_detail_view, name='appointment_detail'),
    path('appointments/<int:pk>/update_status/<str:status>/', views.update_appointment_status_view, name='update_appointment_status'),

    # Medical Record URLs
    path('appointments/<int:appointment_pk>/add-record/', views.add_medical_record_view, name='add_medical_record'),
    path('medical-records/', views.medical_record_list_view, name='medical_record_list'),
]