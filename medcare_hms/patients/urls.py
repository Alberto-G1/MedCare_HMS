# patients/urls.py
from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    # Profile URLs
    path('profile/', views.patient_profile_view, name='patient_profile'),
    path('profile/edit/', views.edit_patient_profile_view, name='edit_patient_profile'),

    # Appointment URLs
    path('appointments/book/', views.book_appointment_view, name='book_appointment'),
    path('appointments/', views.my_appointments_view, name='my_appointments'),
    path('find-doctor/', views.doctor_list_view, name='doctor_list'),
]