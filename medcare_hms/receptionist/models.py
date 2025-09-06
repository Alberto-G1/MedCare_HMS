from django.db import models
from django.contrib.auth.models import User
from management.models import Department

def get_receptionist_image_path(instance, filename):
    return f'profile_pictures/receptionists/{instance.user.username}/{filename}'

class ReceptionistProfile(models.Model):
    SHIFT_CHOICES = [
        ("Morning", "Morning (8 AM - 2 PM)"),
        ("Afternoon", "Afternoon (2 PM - 8 PM)"),
        ("Night", "Night (8 PM - 8 AM)"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='receptionistprofile')
    profile_picture = models.ImageField(upload_to=get_receptionist_image_path, null=True, blank=True, default='profile_pictures/default.jpeg')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    shift = models.CharField(max_length=50, choices=SHIFT_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"Receptionist: {self.user.username}"