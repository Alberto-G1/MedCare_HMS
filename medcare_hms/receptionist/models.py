from django.db import models
from django.contrib.auth.models import User
from management.models import Department

class ReceptionistProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='receptionistprofile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    shift = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., Morning, 9am-5pm")

    def __str__(self):
        return f"Receptionist: {self.user.username}"