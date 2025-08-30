from django import forms
from .models import DoctorProfile

class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = ['specialization', 'qualifications', 'availability']
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Cardiologist'}),
            'qualifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., MBBS, MD'}),
            'availability': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., Mon-Fri, 9am-5pm'}),
        }