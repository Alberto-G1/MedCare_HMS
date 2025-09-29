from django.db import models
from patients.models import PatientProfile, MedicalRecord
from doctors.models import DoctorProfile


class Prescription(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True, related_name='prescriptions')
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_prescriptions')
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prescription #{self.pk} for {self.patient.user.get_full_name()}"

    def is_active(self):
        return self.status == 'ACTIVE'


class PrescribedMedication(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='medications')
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=255, help_text="e.g., 500 mg")
    frequency = models.CharField(max_length=255, help_text="e.g., Twice a day")
    duration_days = models.PositiveIntegerField(default=1)
    instructions = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.medication_name} ({self.dosage})"
