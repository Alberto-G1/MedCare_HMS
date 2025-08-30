# medcare_hms/doctors/models.py (NEW FILE CONTENT)

from django.db import models
from django.contrib.auth.models import User

class DoctorProfile(models.Model):
    """
    Stores profile information specific to users with the 'DOCTOR' role.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctorprofile')
    specialization = models.CharField(max_length=100, blank=True, null=True)
    qualifications = models.TextField(blank=True, null=True, help_text="Enter qualifications, separated by commas.")
    availability = models.TextField(blank=True, null=True, help_text="E.g., Mon-Fri, 9am-5pm")

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} - Profile"