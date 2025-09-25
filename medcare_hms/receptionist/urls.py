from django.urls import path
from . import views

app_name = 'receptionist'

urlpatterns = [
    # Profile URLs
    path('profile/', views.receptionist_profile_view, name='receptionist_profile'),
    path('profile/edit/', views.edit_receptionist_profile_view, name='edit_receptionist_profile'),

    # Patient Management URLs
    path('patients/', views.patient_list_view, name='patient_list'),
    path('patients/add/', views.add_patient_view, name='add_patient'),
    path('patients/<int:pk>/edit/', views.edit_patient_view, name='edit_patient'),

    # Appointment Management URLs
    path('appointments/', views.appointment_list_view, name='appointment_list'),
    path('appointments/book/', views.book_appointment_view, name='book_appointment'),
    path('appointments/<int:pk>/update_status/<str:status>/', views.update_appointment_status_view, name='update_appointment_status'),
    path('appointments/<int:pk>/cancel/', views.cancel_appointment_view, name='cancel_appointment'),
]