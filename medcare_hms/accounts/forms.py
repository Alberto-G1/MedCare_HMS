# accounts/forms.py (REWRITTEN)

from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


class RegistrationForm(forms.Form):
    ROLE_CHOICES = (
        ('PATIENT', 'Patient'),
        ('DOCTOR', 'Doctor'),
        ('RECEPTIONIST', 'Receptionist'),
    )
    
    username = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    contact = forms.CharField(max_length=20, required=True, label="Contact Number")
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True, label="Confirm Password")
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    # Validation for unique username
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username is already taken.")
        return username

    # Validation for unique email
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    # Validation for password matching
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        
        return cleaned_data

class StaffUpdateForm(forms.ModelForm):
    # Fields from UserProfile model
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES)
    contact = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate initial data for profile fields from the user's profile
        if self.instance.pk and hasattr(self.instance, 'userprofile'):
            self.fields['role'].initial = self.instance.userprofile.role
            self.fields['contact'].initial = self.instance.userprofile.contact
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = user.userprofile
            profile.role = self.cleaned_data['role']
            profile.contact = self.cleaned_data['contact']
            profile.save()
        return user