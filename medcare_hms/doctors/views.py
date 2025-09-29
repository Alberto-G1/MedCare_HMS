from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import doctor_required
from .models import DoctorProfile
from .forms import DoctorProfileForm
from patients.models import Appointment, MedicalRecord
from prescriptions.models import Prescription  # linkage for existing prescriptions
from patients.forms import MedicalRecordForm
from django.urls import reverse
from notifications.utils import create_notification
from .forms import DoctorAvailabilityForm
from .models import DoctorAvailability
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.db import IntegrityError


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
    
    # Get the status from the URL, default to showing all
    status_filter = request.GET.get('status', '')
    
    appointment_list = Appointment.objects.filter(doctor=doctor_profile)
    
    if status_filter in ['Pending', 'Approved', 'Completed', 'Cancelled', 'Rejected']:
        appointment_list = appointment_list.filter(status=status_filter)
        
    appointments = appointment_list.order_by('appointment_date', 'appointment_time')
    
    return render(request, 'doctors/doctor_appointments.html', {
        'appointments': appointments,
        'status_filter': status_filter
    })

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
def medical_record_detail_view(request, pk):
    """Detailed view of a single medical record for the authoring doctor.

    Shows legacy text prescription and any structured prescription(s) linked.
    Provides a button to create a structured prescription if none exist yet.
    """
    record = get_object_or_404(
        MedicalRecord.objects.select_related('patient__user', 'doctor__user', 'appointment'),
        pk=pk,
        doctor__user=request.user
    )
    linked_prescriptions = record.linked_prescriptions.all().select_related('doctor__user', 'patient__user')
    can_create_structured = not linked_prescriptions.exists()
    return render(request, 'doctors/medical_record_detail.html', {
        'record': record,
        'linked_prescriptions': linked_prescriptions,
        'can_create_structured': can_create_structured,
    })


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
            # Redirect doctor straight into structured prescription creation, passing medical_record id
            return redirect(reverse('prescriptions:create_prescription', args=[appointment.patient.id]) + f"?medical_record={record.id}")
    else:
        form = MedicalRecordForm()

    return render(request, 'doctors/add_medical_record.html', {'form': form, 'appointment': appointment})

# --- Doctor Availability Views ---
@login_required
@doctor_required
def manage_availability_view(request):
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    
    if request.method == 'POST':
        form = DoctorAvailabilityForm(request.POST)
        if form.is_valid():
            day_of_week = form.cleaned_data['day_of_week']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']

            # --- EXPLICIT VALIDATION ---
            if start_time >= end_time:
                messages.error(request, "Validation Error: End time must be after start time.")
            else:
                overlapping_slots = DoctorAvailability.objects.filter(
                    doctor=doctor_profile, day_of_week=day_of_week,
                    start_time__lt=end_time, end_time__gt=start_time
                )
                if overlapping_slots.exists():
                    messages.error(request, "Validation Error: This time slot overlaps with an existing slot.")
                else:
                    try:
                        DoctorAvailability.objects.create(
                            doctor=doctor_profile, day_of_week=day_of_week,
                            start_time=start_time, end_time=end_time
                        )
                        messages.success(request, "New time slot added successfully.")
                    except IntegrityError:
                        messages.error(request, "Validation Error: This exact start time already exists for this day.")
            
            return redirect('doctors:manage_availability')

    else: # GET request
        form = DoctorAvailabilityForm()
        
    slots = DoctorAvailability.objects.filter(doctor=doctor_profile).order_by('day_of_week', 'start_time')
    
    context = {'form': form, 'slots': slots}
    return render(request, 'doctors/manage_availability.html', context)




# --- NEW API VIEW ---
@login_required
def get_doctor_availability_api(request):
    doctor_id = request.GET.get('doctor_id')
    selected_date_str = request.GET.get('date')

    if not doctor_id or not selected_date_str:
        return JsonResponse({'error': 'Missing doctor ID or date'}, status=400)

    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        doctor = DoctorProfile.objects.get(pk=doctor_id)
    except (ValueError, DoctorProfile.DoesNotExist):
        return JsonResponse({'error': 'Invalid doctor ID or date format'}, status=400)

    day_of_week = selected_date.weekday()
    
    # Get the doctor's general availability for that day
    availability_slots = DoctorAvailability.objects.filter(doctor=doctor, day_of_week=day_of_week)
    
    # Get all appointments already booked for this doctor on this day
    booked_appointments = Appointment.objects.filter(doctor=doctor, appointment_date=selected_date)
    booked_times = [appt.appointment_time for appt in booked_appointments]

    available_time_slots = []
    appointment_duration = timedelta(minutes=30)

    for slot in availability_slots:
        current_time = datetime.combine(selected_date, slot.start_time)
        end_time = datetime.combine(selected_date, slot.end_time)
        
        while current_time + appointment_duration <= end_time:
            time_slot = current_time.time()
            # Check if this specific time slot is NOT already booked
            if time_slot not in booked_times:
                available_time_slots.append({
                    'value': time_slot.strftime('%H:%M:%S'), # Use H:M:S for consistency
                    'display': time_slot.strftime('%I:%M %p')
                })
            current_time += appointment_duration
    
    return JsonResponse({'available_slots': available_time_slots})

# --- VIEW for editing a slot ---
@login_required
@doctor_required
def edit_availability_view(request, pk):
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    slot = get_object_or_404(DoctorAvailability, pk=pk, doctor=doctor_profile)
    
    if request.method == 'POST':
        form = DoctorAvailabilityForm(request.POST, instance=slot)
        if form.is_valid():
            day_of_week = form.cleaned_data['day_of_week']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']

            # --- EXPLICIT VALIDATION FOR EDIT ---
            if start_time >= end_time:
                messages.error(request, "Validation Error: End time must be after start time.")
            else:
                overlapping_slots = DoctorAvailability.objects.filter(
                    doctor=doctor_profile, day_of_week=day_of_week,
                    start_time__lt=end_time, end_time__gt=start_time
                ).exclude(pk=pk) # Exclude the current slot from the check

                if overlapping_slots.exists():
                    messages.error(request, "Validation Error: This time slot overlaps with another slot.")
                else:
                    # If all checks pass, save the form changes
                    form.save()
                    messages.success(request, "Time slot updated successfully.")
            
    return redirect('doctors:manage_availability')

# --- VIEW for deleting a slot ---
@login_required
@doctor_required
def delete_availability_view(request, pk):
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    slot = get_object_or_404(DoctorAvailability, pk=pk, doctor=doctor_profile) # Security check
    
    if request.method == 'POST':
        slot.delete()
        messages.success(request, "Time slot deleted successfully.")
    
    return redirect('doctors:manage_availability')