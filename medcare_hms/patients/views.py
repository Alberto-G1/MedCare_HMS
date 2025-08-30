

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Patient, Appointment, Bill
from .forms import PatientProfileForm, AppointmentBookingForm
from accounts.decorators import patient_required
from datetime import date

@login_required
@patient_required
def patient_profile_view(request):
    # Use get_or_create to handle new patients gracefully
    patient, created = Patient.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, instance=patient)
        # Update the first and last name on the core User model
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.save()
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('patient_profile')
    else:
        form = PatientProfileForm(instance=patient)
        
    return render(request, 'patient/patient_profile.html', {'form': form, 'user': request.user})

@login_required
@patient_required
def book_appointment_view(request):
    patient = get_object_or_404(Patient, user=request.user)
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.save()
            messages.success(request, f"Appointment with {appointment.doctor} on {appointment.appointment_date} has been booked. It is pending confirmation.")
            return redirect('my_appointments')
    else:
        form = AppointmentBookingForm()
    return render(request, 'patient/appointment.html', {'form': form})

@login_required
@patient_required
def my_appointments_view(request):
    patient = get_object_or_404(Patient, user=request.user)
    today = date.today()
    upcoming_appointments = Appointment.objects.filter(patient=patient, appointment_date__gte=today).order_by('appointment_date', 'appointment_time')
    past_appointments = Appointment.objects.filter(patient=patient, appointment_date__lt=today).order_by('-appointment_date', '-appointment_time')
    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments
    }
    return render(request, 'patient/my_appointments.html', context)

@login_required
@patient_required
def my_bills_view(request):
    patient = get_object_or_404(Patient, user=request.user)
    bills = Bill.objects.filter(appointment__patient=patient).order_by('-appointment__appointment_date')
    return render(request, 'patient/billing.html', {'bills': bills})