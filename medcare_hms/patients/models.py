from django.db import models
from django.contrib.auth.models import User
from doctors.models import DoctorProfile
from django.conf import settings


def get_patient_image_path(instance, filename):
    return f'profile_pictures/patients/{instance.user.username}/{filename}'

class PatientProfile(models.Model):
    GENDER_CHOICES = (('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other'))
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patientprofile')
    profile_picture = models.ImageField(upload_to=get_patient_image_path, null=True, blank=True, default='static/profile_pictures/default.jpeg')
    
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    address = models.TextField(max_length=500, null=True, blank=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, null=True, blank=True)
    
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_number = models.CharField(max_length=20, null=True, blank=True)
    
    medical_history = models.TextField(null=True, blank=True, help_text="Allergies, chronic conditions, etc.")
    insurance_provider = models.CharField(max_length=100, null=True, blank=True)
    insurance_policy_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Patient: {self.user.username}"


def get_appointment_attachment_path(instance, filename):
    return f'attachments/appointments/{instance.pk}/{filename}'

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected'),
        ('Completed', 'Completed'), ('Cancelled', 'Cancelled'),
    )
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.PROTECT) # Protect doctor from deletion if they have appointments
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    attachment = models.FileField(upload_to=get_appointment_attachment_path, null=True, blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_appointments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Appointment for {self.patient.user.username} with {self.doctor}"
    

def get_medical_report_path(instance, filename):
    return f'medical_records/{instance.patient.user.username}/{filename}'

class MedicalRecord(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True)
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    
    record_date = models.DateField(auto_now_add=True)
    diagnosis = models.CharField(max_length=255)
    notes = models.TextField()
    prescription = models.TextField(blank=True, null=True)
    report_file = models.FileField(upload_to=get_medical_report_path, null=True, blank=True)
    
    def __str__(self):
        return f"Record for {self.patient.user.username} on {self.record_date}"