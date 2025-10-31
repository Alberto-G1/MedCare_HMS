from django import forms
from django.contrib.auth.models import User
from .models import DoctorProfile
from management.models import Department
from .models import DoctorAvailability
from django.core.exceptions import ValidationError


class DoctorProfileForm(forms.ModelForm):
    # --- Fields from the User model ---
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control-custom'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control-custom'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control-custom'}))
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control-custom form-select-custom'})
    )

    class Meta:
        model = DoctorProfile
        fields = [
            'profile_picture', 'specialization', 'department', 
            'license_number', 'years_of_experience', 'availability'
        ]
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-control-custom', 'placeholder': 'e.g., Cardiology, Neurology'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control-custom', 'placeholder': 'Medical license number'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control-custom', 'min': '0', 'max': '50'}),
            'availability': forms.Textarea(attrs={'class': 'form-control-custom form-textarea-custom', 'placeholder': 'Describe your availability schedule (e.g., Mon-Fri, 9am-5pm)'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control-custom'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            profile.save()
        return profile

class DoctorAvailabilityForm(forms.ModelForm):
    class Meta:
        model = DoctorAvailability
        fields = ['day_of_week', 'start_time', 'end_time']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }