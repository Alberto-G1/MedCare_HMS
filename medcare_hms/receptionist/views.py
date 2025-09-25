# receptionist/views.py (FINAL VERSION)
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from accounts.models import UserProfile as AccountUserProfile
from patients.models import PatientProfile, Appointment
from .models import ReceptionistProfile
from .forms import ReceptionistProfileForm, ManualPatientRegistrationForm, AppointmentBookingForm
from patients.forms import PatientProfileForm as PatientUpdateForm # Reuse the patient's own edit form
from accounts.decorators import receptionist_required


# --- Profile Views ---
@login_required
@receptionist_required
def receptionist_profile_view(request):
    profile, created = ReceptionistProfile.objects.get_or_create(user=request.user)
    return render(request, 'receptionist/receptionist_profile.html', {'profile': profile})

@login_required
@receptionist_required
def edit_receptionist_profile_view(request):
    profile, created = ReceptionistProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ReceptionistProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('receptionist:receptionist_profile')
    else:
        form = ReceptionistProfileForm(instance=profile)
    return render(request, 'receptionist/edit_receptionist_profile.html', {'form': form})

# --- Patient Management Views ---
@login_required
@receptionist_required
def patient_list_view(request):
    query = request.GET.get('q')
    if query:
        patients = PatientProfile.objects.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__userprofile__contact__icontains=query)
        ).select_related('user', 'user__userprofile')
    else:
        patients = PatientProfile.objects.all().select_related('user', 'user__userprofile')
    return render(request, 'receptionist/patient_list.html', {'patients': patients, 'query': query})

@login_required
@receptionist_required
def add_patient_view(request):
    if request.method == 'POST':
        form = ManualPatientRegistrationForm(request.POST)
        if form.is_valid():
            # Create User
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
            )
            # Create AccountUserProfile
            AccountUserProfile.objects.create(user=user, role='PATIENT', contact=form.cleaned_data['contact'])
            # Create PatientProfile
            PatientProfile.objects.create(user=user)
            messages.success(request, f"Patient '{user.username}' was successfully registered.")
            return redirect('receptionist:patient_list')
    else:
        form = ManualPatientRegistrationForm()
    return render(request, 'receptionist/add_patient.html', {'form': form})

@login_required
@receptionist_required
def edit_patient_view(request, pk):
    patient_profile = get_object_or_404(PatientProfile, pk=pk)
    if request.method == 'POST':
        form = PatientUpdateForm(request.POST, request.FILES, instance=patient_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient profile updated successfully.')
            return redirect('receptionist:patient_list')
    else:
        form = PatientUpdateForm(instance=patient_profile)
    return render(request, 'receptionist/edit_patient.html', {'form': form, 'patient': patient_profile})

# --- Appointment Management Views ---
@login_required
@receptionist_required
def appointment_list_view(request):
    # This view now supports filtering
    filter_by = request.GET.get('filter', 'all')
    today = date.today()

    if filter_by == 'pending':
        appointments = Appointment.objects.filter(status='Pending')
    elif filter_by == 'today':
        appointments = Appointment.objects.filter(appointment_date=today)
    else:
        appointments = Appointment.objects.all()

    appointments = appointments.select_related('patient__user', 'doctor__user').order_by('-appointment_date', '-appointment_time')
    return render(request, 'receptionist/appointment_list.html', {'appointments': appointments, 'filter_by': filter_by})

@login_required
@receptionist_required
def book_appointment_view(request):
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.created_by = request.user
            appointment.status = 'Approved' # Receptionist bookings are auto-approved
            appointment.save()
            messages.success(request, 'Appointment successfully booked and confirmed.')
            return redirect('receptionist:appointment_list')
    else:
        form = AppointmentBookingForm()
    return render(request, 'receptionist/book_appointment.html', {'form': form})

@login_required
@receptionist_required
def update_appointment_status_view(request, pk, status):
    """
    Allows a receptionist to approve or reject appointments.
    """
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check if the new status is valid
    valid_statuses = ['Approved', 'Rejected']
    if status not in valid_statuses:
        messages.error(request, "Invalid status update.")
        return redirect('receptionist:appointment_list')
        
    appointment.status = status
    appointment.save()
    messages.success(request, f"Appointment for {appointment.patient.user.get_full_name()} has been {status.lower()}.")
    return redirect('receptionist:appointment_list')

@login_required
@receptionist_required
def cancel_appointment_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.status = 'Cancelled'
    appointment.save()
    messages.info(request, 'The appointment has been cancelled.')
    return redirect('receptionist:appointment_list')