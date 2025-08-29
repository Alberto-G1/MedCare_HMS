# accounts/forms.py (REWRITTEN)

from django import forms
from django.contrib.auth.models import User

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