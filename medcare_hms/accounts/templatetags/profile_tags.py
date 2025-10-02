from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def get_profile_image_url(user):
    """
    Get the profile image URL for any user type, with fallbacks
    """
    try:
        # Check if user has a doctor profile
        if hasattr(user, 'doctorprofile') and user.doctorprofile.profile_picture:
            return user.doctorprofile.profile_picture.url
        # Check if user has a patient profile
        elif hasattr(user, 'patientprofile') and user.patientprofile.profile_picture:
            return user.patientprofile.profile_picture.url
        # Check if user has a receptionist profile
        elif hasattr(user, 'receptionistprofile') and user.receptionistprofile.profile_picture:
            return user.receptionistprofile.profile_picture.url
    except (AttributeError, ValueError):
        pass
    
    # Return default image path
    return '/static/profile_pictures/default.jpeg'

@register.simple_tag
def get_user_initials(user):
    """
    Get user initials for fallback avatars
    """
    if user.first_name and user.last_name:
        return f"{user.first_name[0]}{user.last_name[0]}".upper()
    elif user.first_name:
        return user.first_name[0].upper()
    elif user.username:
        return user.username[0].upper()
    return "U"

@register.simple_tag
def get_user_role_color(user):
    """
    Get the theme color for user role
    """
    try:
        if hasattr(user, 'doctorprofile'):
            return '#14B8A6'  # Teal accent for doctors
        elif hasattr(user, 'patientprofile'):
            return '#0E7490'  # Primary teal for patients
        elif hasattr(user, 'receptionistprofile'):
            return '#5ce9f6'  # Purple accent for receptionists
    except AttributeError:
        pass
    
    return '#14B8A6'  # Default to teal

@register.inclusion_tag('components/profile_image.html')
def profile_image(user, size="40", css_class="user-avatar", show_fallback=True):
    """
    Render a profile image with fallback handling
    """
    return {
        'user': user,
        'size': size,
        'css_class': css_class,
        'show_fallback': show_fallback,
        'image_url': get_profile_image_url(user),
        'initials': get_user_initials(user),
        'role_color': get_user_role_color(user),
    }