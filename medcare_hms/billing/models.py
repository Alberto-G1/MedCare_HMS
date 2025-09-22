# billing/models.py
from django.db import models
from patients.models import PatientProfile, Appointment

def get_receipt_path(instance, filename):
    return f'receipts/{instance.pk}/{filename}'

class Bill(models.Model):
    STATUS_CHOICES = (('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Partially Paid', 'Partially Paid'))
    PAYMENT_METHOD_CHOICES = (('Cash', 'Cash'), ('Card', 'Card'), ('Insurance', 'Insurance'))

    patient = models.ForeignKey(PatientProfile, on_delete=models.PROTECT)
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    
    bill_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Unpaid')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    receipt = models.FileField(upload_to=get_receipt_path, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bill #{self.pk} for {self.patient.user.username}"

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} (x{self.quantity})"