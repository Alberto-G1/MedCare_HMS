from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.patient_profile_view, name='patient_profile'),
    path('book-appointment/', views.book_appointment_view, name='book_appointment'),
    path('my-appointments/', views.my_appointments_view, name='my_appointments'),
    path('my-bills/', views.my_bills_view, name='my_bills'),
]