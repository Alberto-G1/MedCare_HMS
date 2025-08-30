# medcare_hms/receptionist/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from accounts.models import UserProfile
from patients.models import Patient
from .models import ReceptionistProfile
from .forms import ManualPatientRegistrationForm, ReceptionistAppointmentForm, ReceptionistProfileForm
from accounts.decorators import receptionist_required


@login_required
@receptionist_required
def profile_view(request):
    # Get or create the profile instance for the logged-in user
    profile, created = ReceptionistProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update the first and last name on the core User model, just like the patient profile
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.save()
        
        # Update the profile-specific fields using the form
        form = ReceptionistProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('receptionist_dashboard')
    else:
        # For a GET request, create a form instance with the current profile data
        form = ReceptionistProfileForm(instance=profile)
        
    context = {
        'form': form,
        'user': request.user
    }
    return render(request, 'receptionist/profile.html', context)


def get_receptionist_profile(user):
    try:
        # Try to get the existing profile
        profile = user.receptionistprofile
    except ReceptionistProfile.DoesNotExist:
        # If it doesn't exist, create one
        profile = ReceptionistProfile.objects.create(user=user)
    return profile


@login_required
@receptionist_required
def receptionist_profile_view(request):
    """ Displays the receptionist's profile information. """
    profile = get_receptionist_profile(request.user)
    context = {'profile': profile}
    return render(request, 'receptionist/profile.html', context)


@login_required
@receptionist_required
def edit_receptionist_profile_view(request):
    """ Handles editing the receptionist's profile. """
    profile = get_receptionist_profile(request.user) # Use the helper function

    if request.method == 'POST':
        form = ReceptionistProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('receptionist_profile')
    else:
        # This part should now work reliably
        form = ReceptionistProfileForm(instance=profile)

    context = {'form': form}
    return render(request, 'receptionist/edit_profile.html', context)


@login_required
@receptionist_required
def add_patient_view(request):
    if request.method == 'POST':
        form = ManualPatientRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                is_active=True
            )
            UserProfile.objects.create(
                user=user,
                role='PATIENT',
                contact=form.cleaned_data['contact']
            )
            Patient.objects.create(user=user)
            messages.success(request, f"Patient '{user.username}' has been successfully registered.")
            return redirect('receptionist_dashboard')
    else:
        form = ManualPatientRegistrationForm()

    return render(request, 'receptionist/add_patient.html', {'form': form})


@login_required
@receptionist_required
def book_appointment_view(request):
    if request.method == 'POST':
        form = ReceptionistAppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.status = 'Confirmed'
            appointment.save()
            messages.success(request, f"Appointment for {appointment.patient.user.username} with {appointment.doctor} has been confirmed.")
            return redirect('receptionist_dashboard')
    else:
        form = ReceptionistAppointmentForm()

    return render(request, 'receptionist/book_appointment.html', {'form': form})