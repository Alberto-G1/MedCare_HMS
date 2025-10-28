from django import forms
from django.contrib.auth.models import User
from .models import ReceptionistProfile
from patients.models import PatientProfile, Appointment
from doctors.models import DoctorProfile
from management.models import Department
from accounts.models import UserProfile as AccountUserProfile

class ReceptionistProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    
    class Meta:
        model = ReceptionistProfile
        fields = [
            'profile_picture', 'department', 'shift',
            'date_of_birth', 'gender',
            'phone_number', 'email_address',
            'emergency_contact_name', 'emergency_contact_relationship', 'emergency_contact_phone',
            'residential_address', 'postal_code',
            'national_id_passport'
        ]
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'shift': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+256 XXX XXX XXX'}),
            'email_address': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Name'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Spouse, Parent, Sibling'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+256 XXX XXX XXX'}),
            'residential_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full residential address'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
            'national_id_passport': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID or Passport Number'}),
        }
        labels = {
            'profile_picture': 'Profile Picture',
            'date_of_birth': 'Date of Birth',
            'phone_number': 'Phone Number',
            'email_address': 'Email Address',
            'emergency_contact_name': 'Emergency Contact Name',
            'emergency_contact_relationship': 'Relationship',
            'emergency_contact_phone': 'Emergency Contact Phone',
            'residential_address': 'Residential Address',
            'postal_code': 'Postal Code',
            'national_id_passport': 'National ID / Passport Number',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            # Pre-fill email_address from user email if not already set
            if not self.instance.email_address:
                self.fields['email_address'].initial = self.instance.user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            profile.save()
        return profile

class ManualPatientRegistrationForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    contact = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), help_text="Set an initial password for the patient.")

    class Meta:
        model = PatientProfile
        # All fields are custom, so we just link the model
        fields = []

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

class AppointmentBookingForm(forms.ModelForm):
    # Patient is now a searchable dropdown
    patient = forms.ModelChoiceField(
        queryset=PatientProfile.objects.all().select_related('user'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    # Doctor is now a hidden input, selected via cards
    doctor = forms.ModelChoiceField(
        queryset=DoctorProfile.objects.filter(user__is_active=True),
        widget=forms.HiddenInput(),
        required=True
    )
    # Time is an empty dropdown, populated by JavaScript
    appointment_time = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta:
        model = Appointment
        # Order the fields for a logical workflow
        fields = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'reason', 'attachment']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'appointment_time' in self.data:
            self.fields['appointment_time'].choices = [
                (self.data.get('appointment_time'), self.data.get('appointment_time'))
            ]