from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import doctor_required
from .models import DoctorProfile
from .forms import DoctorProfileForm
from patients.models import Appointment, MedicalRecord
from patients.forms import MedicalRecordForm
from django.urls import reverse
from notifications.utils import create_notification

# --- Profile Views ---
@login_required
@doctor_required
def doctor_profile_view(request):
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    return render(request, 'doctors/doctor_profile.html', {'profile': profile})

@login_required
@doctor_required
def edit_doctor_profile_view(request):
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        # Don't forget request.FILES for the profile picture
        form = DoctorProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('doctors:doctor_profile')
    else:
        form = DoctorProfileForm(instance=profile)
    return render(request, 'doctors/edit_doctor_profile.html', {'form': form})

# --- Appointment Views ---
@login_required
@doctor_required
def doctor_appointments_view(request):
    doctor_profile = DoctorProfile.objects.get(user=request.user)
    appointments = Appointment.objects.filter(doctor=doctor_profile).order_by('appointment_date', 'appointment_time')
    return render(request, 'doctors/doctor_appointments.html', {'appointments': appointments})

@login_required
@doctor_required
def appointment_detail_view(request, pk):
    """
    Displays a detailed view of a single appointment.
    """
    # Use select_related to efficiently fetch related patient and user data in one query
    appointment = get_object_or_404(
        Appointment.objects.select_related('patient__user', 'patient__user__userprofile'), 
        pk=pk
    )

    # Security check: Ensure the logged-in doctor is the one assigned to this appointment
    if appointment.doctor.user != request.user:
        messages.error(request, "You are not authorized to view this appointment.")
        return redirect('doctors:doctor_appointments')

    context = {
        'appointment': appointment,
    }
    return render(request, 'doctors/appointment_detail.html', context)


@login_required
@doctor_required
def update_appointment_status_view(request, pk, status):
    appointment = get_object_or_404(Appointment, pk=pk)
    # Security check: ensure the doctor owns this appointment
    if appointment.doctor.user != request.user:
        messages.error(request, "You are not authorized to modify this appointment.")
        return redirect('doctors:doctor_appointments')
    
    # Update status and provide feedback
    appointment.status = status
    appointment.save()
    # --- NOTIFICATION LOGIC ---
    patient_user = appointment.patient.user
    message = f"Your appointment with Dr. {request.user.get_full_name()} on {appointment.appointment_date} has been {status.lower()}."
    create_notification(recipient=patient_user, message=message, link=reverse('patients:my_appointments'))
    # --- END NOTIFICATION LOGIC ---
    messages.success(request, f"Appointment status updated to '{status}'.")
    return redirect('doctors:doctor_appointments')

# --- Medical Record View ---
@login_required
@doctor_required
def medical_record_list_view(request):
    """
    Displays a list of all medical records created by the logged-in doctor.
    """
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    
    # Fetch records, ordering by the most recent first.
    # Use select_related to optimize the query and prevent extra database hits.
    records = MedicalRecord.objects.filter(doctor=doctor_profile)\
                                   .select_related('patient__user', 'appointment')\
                                   .order_by('-record_date')
    
    context = {
        'records': records
    }
    return render(request, 'doctors/medical_record_list.html', context)


@login_required
@doctor_required
def add_medical_record_view(request, appointment_pk):
    appointment = get_object_or_404(Appointment, pk=appointment_pk)
    # Security check
    if appointment.doctor.user != request.user:
        messages.error(request, "You are not authorized to add a record for this appointment.")
        return redirect('doctors:doctor_appointments')

    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES)
        if form.is_valid():
            record = form.save(commit=False)
            record.patient = appointment.patient
            record.doctor = appointment.doctor
            record.appointment = appointment
            record.save()
            # Mark the appointment as Completed
            appointment.status = 'Completed'
            appointment.save()
            messages.success(request, "Medical record added and appointment marked as completed.")
            return redirect('doctors:doctor_appointments')
    else:
        form = MedicalRecordForm()

    return render(request, 'doctors/add_medical_record.html', {'form': form, 'appointment': appointment})