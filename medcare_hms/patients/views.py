# patients/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import patient_required, receptionist_required
from .models import PatientProfile, Appointment
from .forms import PatientProfileForm, AppointmentBookingForm
from datetime import date

# --- Profile Views ---
@login_required
@patient_required
def patient_profile_view(request):
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    return render(request, 'patients/patient_profile.html', {'profile': profile})

@login_required
@patient_required
def edit_patient_profile_view(request):
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('patients:patient_profile')
    else:
        form = PatientProfileForm(instance=profile)
    return render(request, 'patients/edit_patient_profile.html', {'form': form})

# --- Appointment Views ---
@login_required
@patient_required
@receptionist_required
def book_appointment_view(request):
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST, request.FILES)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient_profile
            appointment.created_by = request.user
            appointment.save()
            messages.success(request, 'Your appointment has been successfully booked and is pending approval.')
            return redirect('patients:my_appointments') # CORRECTED REDIRECT
    else:
        form = AppointmentBookingForm()
    return render(request, 'patients/book_appointment.html', {'form': form})

@login_required
@patient_required
def my_appointments_view(request):
    patient = get_object_or_404(PatientProfile, user=request.user)
    today = date.today()
    
    upcoming_appointments = Appointment.objects.filter(
        patient=patient, 
        appointment_date__gte=today
    ).order_by('appointment_date', 'appointment_time')
    
    past_appointments = Appointment.objects.filter(
        patient=patient, 
        appointment_date__lt=today
    ).order_by('-appointment_date', '-appointment_time')
    
    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments
    }
    return render(request, 'patients/my_appointments.html', context)