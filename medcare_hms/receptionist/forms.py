# medcare_hms/receptionist/forms.py

from django import forms
from django.contrib.auth.models import User
from patients.models import Patient, Appointment, Doctor
from datetime import date
from management.models import Department
from .models import ReceptionistProfile


class ManualPatientRegistrationForm(forms.Form):
    username = forms.CharField(max_length=100, required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    contact = forms.CharField(max_length=20, required=True, label="Contact Number")
    password = forms.CharField(widget=forms.PasswordInput, required=True, help_text="Set an initial password for the patient.")

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

class ReceptionistAppointmentForm(forms.ModelForm):
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'reason']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['appointment_date'].widget.attrs['min'] = date.today().strftime('%Y-%m-%d')

class ReceptionistProfileForm(forms.ModelForm):
    class Meta:
        model = ReceptionistProfile
        fields = ['department', 'shift']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'shift': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Morning, 9am-5pm'}),
        }