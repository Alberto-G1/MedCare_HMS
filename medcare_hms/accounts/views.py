from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from patients.models import Appointment, PatientProfile
from doctors.models import DoctorProfile
from django.views.generic import DetailView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin 
from django.urls import reverse_lazy
from .forms import RegistrationForm, StaffUpdateForm 
from .models import UserProfile
from .decorators import admin_required, doctor_required, receptionist_required, patient_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from billing.models import Bill


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Create user
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            role = form.cleaned_data.get('role')
            contact = form.cleaned_data.get('contact')

            # Admin approval workflow
            if role in ['DOCTOR', 'RECEPTIONIST']:
                user.is_active = False  # Staff must be approved by an Admin
            else:
                user.is_active = True  # Patients are auto-approved

            user.save()

            # Create profile
            UserProfile.objects.create(user=user, role=role, contact=contact)

            messages.success(request, 'Registration successful!')

            if user.is_active:
                login(request, user)
                return redirect('dashboard_redirect')
            else:
                messages.info(request, 'Your account is pending approval from an administrator.')
                return redirect('login')  # Redirect to login page to show messages
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('dashboard_redirect')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')


@login_required
def dashboard_redirect_view(request):
    """Redirects user to their respective dashboard after login."""
    if hasattr(request.user, 'userprofile'):
        profile = request.user.userprofile
        if profile.role == 'ADMIN':
            return redirect('admin_dashboard')
        elif profile.role == 'DOCTOR':
            return redirect('doctor_dashboard')
        elif profile.role == 'RECEPTIONIST':
            return redirect('receptionist_dashboard')
        elif profile.role == 'PATIENT':
            return redirect('patient_dashboard')

    # Fallback for users without a profile or if something goes wrong
    messages.error(request, "Could not determine user role. Logging out.")
    logout(request)
    return redirect('login')


# --- Admin Views ---
@login_required
@admin_required
def admin_dashboard(request):
    # Count of active users by role
    active_doctors_count = UserProfile.objects.filter(role='DOCTOR', user__is_active=True).count()
    active_receptionists_count = UserProfile.objects.filter(role='RECEPTIONIST', user__is_active=True).count()
    active_patients_count = UserProfile.objects.filter(role='PATIENT', user__is_active=True).count()
    
    # Count of pending staff for approval
    pending_staff_count = UserProfile.objects.filter(
        role__in=['DOCTOR', 'RECEPTIONIST'], 
        user__is_active=False
    ).count()

    # --- NEW: CALCULATIONS MOVED FROM TEMPLATE TO VIEW ---
    total_users = active_doctors_count + active_receptionists_count + active_patients_count

    if total_users > 0:
        patient_percent = int((active_patients_count / total_users) * 100)
        doctor_percent = int((active_doctors_count / total_users) * 100)
        receptionist_percent = int((active_receptionists_count / total_users) * 100)
    else:
        # Avoid division by zero if there are no users
        patient_percent = 0
        doctor_percent = 0
        receptionist_percent = 0

    context = {
        'active_doctors_count': active_doctors_count,
        'active_receptionists_count': active_receptionists_count,
        'active_patients_count': active_patients_count,
        'pending_staff_count': pending_staff_count,
        
        # Add the new calculated values to the context
        'total_users': total_users,
        'patient_percent': patient_percent,
        'doctor_percent': doctor_percent,
        'receptionist_percent': receptionist_percent,
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
@admin_required
def approve_user(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
        user.is_active = True
        user.save()
        messages.success(request, f"User '{user.username}' has been approved.")
    except User.DoesNotExist:
        messages.error(request, "User not found.")
    return redirect('staff_management_list')


@login_required
@admin_required
def reject_user(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
        username = user.username
        user.delete()
        messages.success(request, f"User '{username}' has been rejected and their account deleted.")
    except User.DoesNotExist:
        messages.error(request, "User not found.")
    return redirect('staff_management_list')


# --- Other Role Dashboards ---
@login_required
@doctor_required
def doctor_dashboard(request):
    # Ensure a doctor profile exists, which is crucial for querying
    doctor_profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    
    today = date.today()

    # --- Fetching data for Statistic Cards ---
    todays_appointments = Appointment.objects.filter(doctor=doctor_profile, appointment_date=today)
    
    todays_appointments_count = todays_appointments.count()
    completed_today_count = todays_appointments.filter(status='Completed').count()
    
    # "Waiting" could be defined as 'Approved' but not yet 'Completed'
    waiting_patients_count = todays_appointments.filter(status='Approved').count()

    # --- Fetching data for Actionable Lists ---
    # Appointments for today's table view
    upcoming_appointments_today = todays_appointments.order_by('appointment_time')


    context = {
        'todays_appointments_count': todays_appointments_count,
        'completed_today_count': completed_today_count,
        'waiting_patients_count': waiting_patients_count,
        'upcoming_appointments_today': upcoming_appointments_today,
        # Dummy data for features not yet implemented
        'unread_messages_count': 7, 
        'pending_lab_results_count': 4,
        'current_time': timezone.now(),
    }
    return render(request, 'accounts/doctor_dashboard.html', context)


@login_required
@receptionist_required
def receptionist_dashboard(request):
    today = date.today()

    # --- Fetching data for Statistic Cards ---
    todays_appointments = Appointment.objects.filter(appointment_date=today)
    todays_appointments_count = todays_appointments.count()
    
    new_patients_count = UserProfile.objects.filter(
        role='PATIENT', 
        user__date_joined__date=today
    ).count()

    available_doctors_count = DoctorProfile.objects.filter(user__is_active=True).count()
    
    # ADDITION: Get total number of patients
    total_patients_count = PatientProfile.objects.count()

    # --- Fetching data for Actionable Lists ---
    upcoming_appointments_today = todays_appointments.order_by('appointment_time')[:10]
    pending_appointments = Appointment.objects.filter(status='Pending').order_by('appointment_date', 'appointment_time')
    pending_appointments_count = pending_appointments.count()

    context = {
        'todays_appointments_count': todays_appointments_count,
        'new_patients_count': new_patients_count,
        'available_doctors_count': available_doctors_count,
        'pending_appointments_count': pending_appointments_count,
        'upcoming_appointments_today': upcoming_appointments_today,
        'pending_appointments': pending_appointments,
        'total_patients_count': total_patients_count, # Pass the new variable
        'current_time': timezone.now(),
    }
    return render(request, 'accounts/receptionist_dashboard.html', context)

@login_required
@patient_required
def patient_dashboard(request):
    patient_profile, created = PatientProfile.objects.get_or_create(user=request.user)

    # --- Fetching data for Statistic Cards & Lists ---
    today = date.today()
    
    # Upcoming appointments (from today onwards)
    upcoming_appointments = Appointment.objects.filter(
        patient=patient_profile, 
        appointment_date__gte=today
    ).order_by('appointment_date', 'appointment_time')

    # Count of unpaid bills
    unpaid_bills_count = Bill.objects.filter(
        patient=patient_profile,
        status='Unpaid'
    ).count()

    # Check if essential profile fields are filled
    profile_is_complete = all([
        patient_profile.date_of_birth,
        patient_profile.gender,
        patient_profile.address,
        patient_profile.emergency_contact_number,
    ])

    context = {
        'profile': patient_profile,
        'upcoming_appointments': upcoming_appointments,
        'unpaid_bills_count': unpaid_bills_count,
        'profile_is_complete': profile_is_complete,
        'current_time': timezone.now(),
    }
    return render(request, 'accounts/patient_dashboard.html', context)

@admin_required
def staff_management_list(request):
    """ Main view, shows ONLY ACTIVE staff """
    staff_profiles = UserProfile.objects.filter(
        role__in=['DOCTOR', 'RECEPTIONIST'],
        user__is_active=True
    ).select_related('user').order_by('user__username')
    
    return render(request, 'accounts/staff_management_list.html', {'staff_profiles': staff_profiles})


@admin_required
def toggle_staff_status(request, user_id):
    """
    Activates or deactivates a staff member's account.
    Prevents deactivating the only active admin.
    """
    user_to_toggle = get_object_or_404(User, pk=user_id)

    # Safety Check: Prevent deactivating the last active Admin account
    if user_to_toggle.userprofile.role == 'ADMIN':
        if UserProfile.objects.filter(role='ADMIN', user__is_active=True).count() == 1 and user_to_toggle.is_active:
            messages.error(request, "Cannot deactivate the last active administrator.")
            return redirect('staff_management_list')

    user_to_toggle.is_active = not user_to_toggle.is_active
    user_to_toggle.save()

    status = "activated" if user_to_toggle.is_active else "deactivated"
    messages.success(request, f"User '{user_to_toggle.username}' has been successfully {status}.")
    return redirect('staff_management_list')


@admin_required
def pending_staff_list(request):
    """ New view for PENDING staff """
    staff_profiles = UserProfile.objects.filter(
        role__in=['DOCTOR', 'RECEPTIONIST'],
        user__is_active=False,
        user__last_login__isnull=True # Differentiates pending from deactivated
    ).select_related('user').order_by('user__date_joined')
    
    return render(request, 'accounts/pending_staff_list.html', {'staff_profiles': staff_profiles})

@admin_required
def deactivated_staff_list(request):
    """ New view for DEACTIVATED staff """
    staff_profiles = UserProfile.objects.filter(
        role__in=['DOCTOR', 'RECEPTIONIST'],
        user__is_active=False,
        user__last_login__isnull=False # They have logged in before
    ).select_related('user').order_by('user__username')
    
    return render(request, 'accounts/deactivated_staff_list.html', {'staff_profiles': staff_profiles})

@method_decorator(admin_required, name='dispatch')
class StaffDetailView(DetailView):
    model = User
    template_name = 'accounts/staff_detail.html'
    context_object_name = 'staff_member'

@method_decorator(admin_required, name='dispatch')
class StaffUpdateView(SuccessMessageMixin, UpdateView):
    model = User
    form_class = StaffUpdateForm
    template_name = 'accounts/staff_update_form.html'
    success_url = reverse_lazy('staff_management_list')
    success_message = "Staff member '%(username)s' was updated successfully."

# --- Update toggle_staff_status for smarter redirects ---

@admin_required
def toggle_staff_status(request, user_id):
    user_to_toggle = get_object_or_404(User, pk=user_id)
    
    # Determine where the request came from to redirect back appropriately
    redirect_url = request.META.get('HTTP_REFERER', 'staff_management_list')
    
    # ... (safety check for last admin) ...

    user_to_toggle.is_active = not user_to_toggle.is_active
    user_to_toggle.save()
    
    status = "activated" if user_to_toggle.is_active else "deactivated"
    messages.success(request, f"User '{user_to_toggle.username}' has been successfully {status}.")
    
    # Redirect back to the page the admin was on
    return redirect(redirect_url)