# accounts/decorators.py (NEW AND IMPROVED)

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def role_required(allowed_roles=[]):
    """
    Decorator for views that checks that the user is logged in and has the correct role.
    - allowed_roles: A list of role strings that are allowed to access the view.
    
    If the user is not logged in, they are redirected to the login page.
    If the user is logged in but does not have the required role, a 403 Permission Denied
    error is raised.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # 1. Check if user is authenticated at all
            if not request.user.is_authenticated:
                return redirect('login') # Or your login URL

            # 2. Superusers always allowed (admin override)
            if request.user.is_superuser:
                # Optionally ensure a profile exists for consistency
                from accounts.models import UserProfile
                if not hasattr(request.user, 'userprofile'):
                    # Create a synthetic ADMIN profile so role-based UI works
                    UserProfile.objects.create(user=request.user, role='ADMIN')
                return view_func(request, *args, **kwargs)

            # 3. Ensure profile exists; if not, deny
            if not hasattr(request.user, 'userprofile'):
                raise PermissionDenied("You do not have a role assigned.")

            # 4. Check role membership
            if request.user.userprofile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to access this page.")
        
        return _wrapped_view
    return decorator

# --- Create specific decorators for convenience ---
admin_required = role_required(allowed_roles=['ADMIN'])
doctor_required = role_required(allowed_roles=['DOCTOR'])
receptionist_required = role_required(allowed_roles=['RECEPTIONIST'])
patient_required = role_required(allowed_roles=['PATIENT'])