# patients/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import patient_required, receptionist_required, admin_required
from .models import PatientProfile, Appointment, MedicalRecord 
from .forms import PatientProfileForm, AppointmentBookingForm
from datetime import date
from doctors.models import DoctorProfile
from django.utils import timezone
from billing.models import Bill 
from django.db.models import Q

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
            return redirect('patients:my_appointments')
    else:
        form = AppointmentBookingForm()

    available_doctors = DoctorProfile.objects.filter(user__is_active=True).select_related('user')
    
    context = {
        'form': form,
        'doctors': available_doctors # Pass the list of doctors to the template
    }
    return render(request, 'patients/book_appointment.html', context)



@login_required
@patient_required
def my_appointments_view(request):
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    today = timezone.now().date()

    # Get two separate querysets: one for upcoming, one for past
    upcoming_appointments = Appointment.objects.filter(
        patient=patient_profile,
        appointment_date__gte=today
    ).order_by('appointment_date', 'appointment_time')

    past_appointments = Appointment.objects.filter(
        patient=patient_profile,
        appointment_date__lt=today
    ).order_by('-appointment_date', '-appointment_time')

    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
    }
    return render(request, 'patients/my_appointments.html', context)

# patients/views.py

@login_required
def doctor_list_view(request):
    # Get all active doctors
    doctors = DoctorProfile.objects.filter(user__is_active=True).select_related('user', 'department')
    return render(request, 'patients/doctor_list.html', {'doctors': doctors})

@login_required
@patient_required
def my_bills_list_view(request):
    """
    Displays a list of only the logged-in patient's bills.
    """
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    bills = Bill.objects.filter(patient=patient_profile).order_by('-bill_date')
    return render(request, 'patients/my_bills_list.html', {'bills': bills})

@login_required
@patient_required
def my_bill_detail_view(request, pk):
    """
    Displays the details of a single bill, ensuring it belongs to the logged-in patient.
    """
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    bill = get_object_or_404(Bill, pk=pk, patient=patient_profile) # Security check
    return render(request, 'patients/my_bill_detail.html', {'bill': bill})

@login_required
@patient_required
def my_bill_receipt_view(request, pk):
    """
    Displays a printable receipt for a single bill, ensuring it belongs to the logged-in patient.
    """
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    bill = get_object_or_404(Bill, pk=pk, patient=patient_profile) # Security check
    return render(request, 'billing/bill_receipt.html', {'bill': bill}) 

# --- Patient-Facing Medical Record Views ---
@login_required
@patient_required
def my_medical_records_list_view(request):
    """
    Displays a list of all medical records for the logged-in patient.
    """
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    
    # Fetch all records for this patient, ordering by the most recent date.
    # Use select_related to optimize the query by pre-fetching doctor details.
    records = MedicalRecord.objects.filter(patient=patient_profile)\
                                   .select_related('doctor__user')\
                                   .order_by('-record_date')
                                   
    return render(request, 'patients/my_medical_records_list.html', {'records': records})


@login_required
@patient_required
def my_medical_record_detail_view(request, pk):
    """
    Displays the details of a single medical record, ensuring it belongs to the logged-in patient.
    """
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    
    # Security check: Ensure the patient can only access their own records.
    record = get_object_or_404(
        MedicalRecord.objects.select_related('doctor__user', 'appointment'), 
        pk=pk, 
        patient=patient_profile
    )
    
    return render(request, 'patients/my_medical_record_detail.html', {'record': record})