# medcare_hms/doctors/urls.py (NEW FILE)

from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('profile/', views.doctor_profile_view, name='doctor_profile'),
    path('profile/edit/', views.edit_doctor_profile_view, name='edit_doctor_profile'),
]