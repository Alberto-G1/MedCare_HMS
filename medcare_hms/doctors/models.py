from django.db import models
from django.contrib.auth.models import User
from management.models import Department

def get_doctor_image_path(instance, filename):
    return f'profile_pictures/doctors/{instance.user.username}/{filename}'

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctorprofile')
    profile_picture = models.ImageField(upload_to=get_doctor_image_path, null=True, blank=True, default='profile_pictures/default.jpeg')
    
    specialization = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    license_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    availability = models.TextField(blank=True, null=True, help_text="e.g., Mon-Fri, 9am-5pm")

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"