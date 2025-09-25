from django import forms
from .models import Bill, BillItem
from patients.models import PatientProfile, Appointment

class BillForm(forms.ModelForm):
    """
    Form for creating the main Bill object.
    Now includes validation to prevent patient/appointment mismatch.
    """
    patient = forms.ModelChoiceField(
        queryset=PatientProfile.objects.filter(user__is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    # Appointment is optional, for miscellaneous bills (e.g., pharmacy pickup)
    appointment = forms.ModelChoiceField(
        queryset=Appointment.objects.filter(status='Completed'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Bill
        fields = ['patient', 'appointment', 'due_date', 'status', 'payment_method']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean(self):
        """
        THIS IS THE CRITICAL VALIDATION LOGIC.
        It ensures that if an appointment is selected, it MUST belong to the selected patient.
        """
        cleaned_data = super().clean()
        patient = cleaned_data.get('patient')
        appointment = cleaned_data.get('appointment')

        if patient and appointment:
            # Check if the appointment's patient is the same as the selected patient
            if appointment.patient != patient:
                # If they don't match, raise a validation error.
                # This error will be displayed at the top of the form.
                raise forms.ValidationError(
                    "Data mismatch: The selected appointment does not belong to the selected patient."
                )
        
        return cleaned_data


class BillItemForm(forms.ModelForm):
    """
    Form for adding/editing individual line items to an existing Bill.
    """
    class Meta:
        model = BillItem
        fields = ['description', 'quantity', 'unit_price']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Consultation Fee'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
        }

class UpdatePaymentForm(forms.ModelForm):
    # This field is for entering a new payment amount, it's not directly saved to the model
    new_payment_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 20000'})
    )

    class Meta:
        model = Bill
        fields = ['status', 'payment_method']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
        }