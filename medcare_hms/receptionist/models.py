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
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    # Basic Information
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='receptionistprofile')
    profile_picture = models.ImageField(upload_to=get_receptionist_image_path, null=True, blank=True, default='profile_pictures/default.jpeg')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    shift = models.CharField(max_length=50, choices=SHIFT_CHOICES, blank=True, null=True)
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    
    # Contact Information
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email_address = models.EmailField(blank=True, null=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Address Information
    residential_address = models.TextField(blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Identification
    national_id_passport = models.CharField(max_length=50, blank=True, null=True, verbose_name="National ID / Passport Number")

    def __str__(self):
        return f"Receptionist: {self.user.username}"
    
    class Meta:
        verbose_name = "Receptionist Profile"
        verbose_name_plural = "Receptionist Profiles"