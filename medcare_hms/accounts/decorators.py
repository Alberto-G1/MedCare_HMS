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

            # 2. Check if the user has a UserProfile
            # The hasattr check is crucial for newly created users or superusers
            if not hasattr(request.user, 'userprofile'):
                raise PermissionDenied("You do not have a role assigned.")
            
            # 3. Check if the user's role is in the allowed list
            if request.user.userprofile.role in allowed_roles:
                # If they have the role, let them access the view
                return view_func(request, *args, **kwargs)
            else:
                # If they are logged in but have the wrong role, deny permission
                raise PermissionDenied("You do not have permission to access this page.")
        
        return _wrapped_view
    return decorator

# --- Create specific decorators for convenience ---
admin_required = role_required(allowed_roles=['ADMIN'])
doctor_required = role_required(allowed_roles=['DOCTOR'])
receptionist_required = role_required(allowed_roles=['RECEPTIONIST'])
patient_required = role_required(allowed_roles=['PATIENT'])