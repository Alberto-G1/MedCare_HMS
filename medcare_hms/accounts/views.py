from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

from .forms import RegistrationForm
from .models import UserProfile
from .decorators import admin_required, doctor_required, receptionist_required, patient_required

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
                return redirect('login') # Redirect to login page to show messages
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
    pending_staff = UserProfile.objects.filter(user__is_active=False, role__in=['DOCTOR', 'RECEPTIONIST'])
    return render(request, 'accounts/admin_dashboard.html', {'pending_staff': pending_staff})

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
    return redirect('admin_dashboard')

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
    return redirect('admin_dashboard')

# --- Other Role Dashboards ---
@login_required
@doctor_required
def doctor_dashboard(request):
    return render(request, 'accounts/doctor_dashboard.html')

@login_required
@receptionist_required
def receptionist_dashboard(request):
    return render(request, 'accounts/receptionist_dashboard.html')

@login_required
@patient_required
def patient_dashboard(request):
    return render(request, 'accounts/patient_dashboard.html')