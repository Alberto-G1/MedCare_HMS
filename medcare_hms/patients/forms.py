import re
from django import forms
from django.core.exceptions import ValidationError
from .models import PatientProfile
from datetime import date, datetime
from .models import Appointment
from doctors.models import DoctorProfile
from datetime import date
from .models import MedicalRecord


class PatientProfileForm(forms.ModelForm):
    # --- Fields from the User model ---
    first_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = PatientProfile
        # Include all fields from PatientProfile EXCEPT the user link
        exclude = ['user']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'medical_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'insurance_provider': forms.TextInput(attrs={'class': 'form-control'}),
            'insurance_policy_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Populate the first_name and last_name fields with initial data from the User model.
        """
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
    
    def save(self, commit=True):
        """
        Save the PatientProfile instance and update the related User instance.
        """
        # Save the PatientProfile part
        profile = super().save(commit=commit)
        
        # Update the User part
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            
        return profile

    # --- Your existing validation methods ---
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob >= date.today():
            raise ValidationError("Date of birth must be in the past.")
        return dob

    def clean_emergency_contact_number(self):
        number = self.cleaned_data.get('emergency_contact_number')
        if number:
            if not re.match(r'^\+?1?\d{9,15}$', number):
                raise ValidationError("Enter a valid phone number format (e.g., +1234567890).")
        return number

    def clean(self):
        cleaned_data = super().clean()
        emergency_contact = cleaned_data.get('emergency_contact_number')
        # We get the user's main contact from the related UserProfile object in the accounts app
        user_contact = self.instance.user.userprofile.contact
        if emergency_contact and user_contact and emergency_contact == user_contact:
            raise ValidationError({"emergency_contact_number": "Emergency contact cannot be the same as your own contact number."})
        return cleaned_data


class AppointmentBookingForm(forms.ModelForm):
    # Filter to show only active doctors
    doctor = forms.ModelChoiceField(
        queryset=DoctorProfile.objects.filter(user__is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'reason', 'attachment']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date and appointment_date < date.today():
            raise ValidationError("Appointment date cannot be in the past.")
        return appointment_date

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')

        if doctor and appointment_date and appointment_time:
            # Check for double booking
            existing_appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time
            ).exclude(pk=self.instance.pk) # Exclude self if updating

            if existing_appointments.exists():
                raise ValidationError("This time slot with the selected doctor is already booked.")
        return cleaned_data
    

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['diagnosis', 'notes', 'prescription', 'report_file']
        widgets = {
            'diagnosis': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prescription': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'report_file': forms.FileInput(attrs={'class': 'form-control'}),
        }