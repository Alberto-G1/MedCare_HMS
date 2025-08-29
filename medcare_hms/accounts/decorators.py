

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test

def role_required(allowed_roles=[]):
    """
    Decorator for views that checks that the user is logged in and has one of the allowed roles.
    """
    def check_role(user):
        if user.is_authenticated and hasattr(user, 'userprofile'):
            return user.userprofile.role in allowed_roles
        return False
    
    return user_passes_test(check_role)

# Specific decorators for convenience
admin_required = role_required(allowed_roles=['ADMIN'])
doctor_required = role_required(allowed_roles=['DOCTOR'])
receptionist_required = role_required(allowed_roles=['RECEPTIONIST'])
patient_required = role_required(allowed_roles=['PATIENT'])