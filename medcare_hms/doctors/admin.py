# doctors/admin.py
from django.contrib import admin
from .models import DoctorProfile, DoctorAvailability

admin.site.register(DoctorProfile)
admin.site.register(DoctorAvailability)