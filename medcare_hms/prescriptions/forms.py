from django import forms
from django.forms import inlineformset_factory
from .models import Prescription, PrescribedMedication


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['notes', 'status']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class PrescribedMedicationForm(forms.ModelForm):
    class Meta:
        model = PrescribedMedication
        fields = ['medication_name', 'dosage', 'frequency', 'duration_days', 'instructions']
        widgets = {
            'medication_name': forms.TextInput(attrs={'class': 'form-control'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control'}),
            'frequency': forms.TextInput(attrs={'class': 'form-control'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


MedicationFormSet = inlineformset_factory(
    Prescription,
    PrescribedMedication,
    form=PrescribedMedicationForm,
    extra=3,
    can_delete=True
)
