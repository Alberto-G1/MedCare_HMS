from django import forms
from .models import Department, Room
from django.core.validators import MaxValueValidator


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Check for case-insensitive uniqueness
        # Exclude the current instance if we are updating an existing department
        if Department.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('A department with this name already exists.')
        return name
    

class RoomForm(forms.ModelForm):
    # Enforce a max capacity limit at the form level
    capacity = forms.IntegerField(
        min_value=1, # Ensures capacity > 0
        max_value=50, # Sets max capacity
        initial=1
    )

    class Meta:
        model = Room
        fields = ['room_number', 'room_type', 'department', 'capacity', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rule: Can only assign a room to an ACTIVE department.
        self.fields['department'].queryset = Department.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')

        # This is where we'll check for occupancy before changing status.
        # This part depends on the Patient/Admission model, which doesn't exist yet.
        # Added it as a placeholder for future integration.
        if self.instance.pk: # Only check for existing rooms being updated
            # active_admissions = Admission.objects.filter(room=self.instance, is_discharged=False).count()
            active_admissions = 0 # Placeholder value

            if active_admissions > 0 and status == 'MAINTENANCE':
                self.add_error('status', f"Cannot set status to 'Under Maintenance'. The room is currently occupied by {active_admissions} patient(s).")
            
            # Consistency Check: if status is 'Occupied', there should be patients.
            # if status == 'AVAILABLE' and active_admissions > 0:
            #     self.add_error('status', "Cannot set status to 'Available'. The room is still marked as occupied.")

        return cleaned_data