# medcare_hms/receptionist/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Patient Management
    path('add-patient/', views.add_patient_view, name='add_patient'),
    
    # Appointment Management
    path('book-appointment/', views.book_appointment_view, name='book_appointment_receptionist'),
    
    # Profile Management
    path('profile/', views.profile_view, name='receptionist_profile'),
    path('profile/edit/', views.edit_receptionist_profile_view, name='edit_receptionist_profile'),
]