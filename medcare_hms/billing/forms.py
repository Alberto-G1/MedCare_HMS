# billing/forms.py (CORRECTED)

from django import forms
from .models import Bill, BillItem
from patients.models import PatientProfile, Appointment

class BillForm(forms.ModelForm):
    """
    Form for creating the main Bill object.
    The total_amount is excluded because it will be calculated automatically.
    """
    patient = forms.ModelChoiceField(
        queryset=PatientProfile.objects.filter(user__is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    # Appointment is optional
    appointment = forms.ModelChoiceField(
        queryset=Appointment.objects.filter(status='Completed'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Bill
        # We only need to specify the fields that are manually entered for the main bill
        fields = ['patient', 'appointment', 'due_date', 'status', 'payment_method']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
        }

class BillItemForm(forms.ModelForm):
    """
    Form for adding individual line items to an existing Bill.
    """
    class Meta:
        model = BillItem
        # The 'bill' and 'amount' fields will be set in the view, not by the user
        fields = ['description', 'quantity', 'unit_price']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Consultation Fee'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
        }