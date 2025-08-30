from django import forms
from .models import Patient, Appointment, Doctor
from datetime import date

class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['date_of_birth', 'gender', 'address', 'blood_group']
        widgets = {
        'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-input form-control'}),
        'gender': forms.Select(attrs={'class': 'form-select'}),
        'address': forms.Textarea(attrs={'class': 'form-input form-control', 'rows': 3, 'placeholder': 'Enter your full address'}),
        'blood_group': forms.Select(attrs={'class': 'form-select'}),
    }
class AppointmentBookingForm(forms.ModelForm):
    # Query only users with the 'DOCTOR' role for the doctor field
    doctor = forms.ModelChoiceField(
    queryset=Doctor.objects.all(),
    widget=forms.Select(attrs={'class': 'form-select'})
    )
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'reason']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input form-control'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-textarea form-control', 'rows': 4, 'placeholder': 'Describe your symptoms or reason for the visit.'}),
        }

def __init__(self, *args, **kwargs):
    super(AppointmentBookingForm, self).__init__(*args, **kwargs)
    self.fields['appointment_date'].widget.attrs['min'] = date.today().strftime('%Y-%m-%d')