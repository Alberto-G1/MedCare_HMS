# medcare_hms/doctors/views.py (UPDATED FILE)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Import the decorator from the accounts app
from accounts.decorators import doctor_required

from .models import DoctorProfile
from .forms import DoctorProfileForm


@login_required
@doctor_required
def doctor_profile_view(request):
    """
    Displays the doctor's profile information.
    """
    try:
        profile = request.user.doctorprofile
    except DoctorProfile.DoesNotExist:
        profile = DoctorProfile.objects.create(user=request.user)

    context = {
        'profile': profile
    }
    # UPDATE TEMPLATE PATH
    return render(request, 'doctors/doctor_profile.html', context)


@login_required
@doctor_required
def edit_doctor_profile_view(request):
    """
    Handles editing the doctor's profile.
    """
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('doctors:doctor_profile')  # UPDATE REDIRECT
    else:
        form = DoctorProfileForm(instance=profile)

    context = {
        'form': form
    }
    # UPDATE TEMPLATE PATH
    return render(request, 'doctors/edit_doctor_profile.html', context)