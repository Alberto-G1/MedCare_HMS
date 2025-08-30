# medcare_hms/billing/forms.py

from django import forms
from patients.models import Bill

class BillGenerationForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter bill amount'}),
        }

class BillUpdateForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['payment_status']
        widgets = {
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
        }