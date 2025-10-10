from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.simple_tag(takes_context=True)
def get_user_theme(context):
    """
    Automatically detect the user's role and return the appropriate theme class
    This allows shared templates to dynamically adapt their styling
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return 'public-theme'  # Default theme for non-authenticated users
    
    user = request.user
    
    # Check if user is admin/superuser
    if user.is_superuser or user.is_staff:
        return 'admin-theme'
    
    # Check for specific role profiles
    try:
        # Check for doctor profile
        if hasattr(user, 'doctorprofile'):
            return 'doctor-theme'
        
        # Check for patient profile  
        elif hasattr(user, 'patientprofile'):
            return 'patient-theme'
            
        # Check for receptionist profile
        elif hasattr(user, 'receptionistprofile'):
            return 'receptionist-theme'
            
        # Check for general user profile with role
        elif hasattr(user, 'userprofile'):
            role = user.userprofile.role.lower() if user.userprofile.role else None
            if role == 'doctor':
                return 'doctor-theme'
            elif role == 'patient':
                return 'patient-theme'
            elif role == 'receptionist':
                return 'receptionist-theme'
            
    except Exception:
        pass
    
    # Default fallback
    return 'patient-theme'


@register.simple_tag(takes_context=True)
def get_theme_css_file(context):
    """
    Returns the appropriate CSS file path for the user's theme
    """
    theme = get_user_theme(context)
    
    theme_files = {
        'doctor-theme': 'css/themes/doctor-theme.css',
        'patient-theme': 'css/themes/patient-theme.css', 
        'receptionist-theme': 'css/themes/receptionist-theme.css',
        'admin-theme': 'css/themes/doctor-theme.css',  # Admins use doctor theme
        'public-theme': 'css/themes/patient-theme.css'  # Public uses patient theme
    }
    
    return theme_files.get(theme, 'css/themes/patient-theme.css')


@register.simple_tag(takes_context=True)
def get_theme_colors(context):
    """
    Returns the primary colors for the current user's theme
    Useful for inline styling when needed
    """
    theme = get_user_theme(context)
    
    colors = {
        'doctor-theme': {
            'primary': '#14B8A6',
            'primary_dark': '#0F766E',
            'primary_light': '#5EEAD4',
            'secondary': '#0284C7'
        },
        'patient-theme': {
            'primary': '#0E7490',
            'primary_dark': '#0C4A6E', 
            'primary_light': '#67E8F9',
            'secondary': '#0284C7'
        },
        'receptionist-theme': {
            'primary': '#5ce9f6',
            'primary_dark': '#0891b2',
            'primary_light': '#a5f3fc',
            'secondary': '#0284C7'
        },
        'admin-theme': {
            'primary': '#14B8A6',
            'primary_dark': '#0F766E',
            'primary_light': '#5EEAD4',
            'secondary': '#0284C7'
        }
    }
    
    return colors.get(theme, colors['patient-theme'])


@register.simple_tag(takes_context=True)
def theme_button_class(context, button_type='primary'):
    """
    Returns the appropriate button class for the current theme
    Usage: {% theme_button_class 'primary' %} or {% theme_button_class 'secondary' %}
    """
    theme = get_user_theme(context)
    
    button_classes = {
        'doctor-theme': {
            'primary': 'btn-primary-custom',
            'secondary': 'btn-secondary-custom',
            'outline': 'btn-outline-custom'
        },
        'patient-theme': {
            'primary': 'btn-primary-custom',
            'secondary': 'btn-sky',
            'outline': 'btn-outline-custom',
            'wellness': 'btn-wellness'
        },
        'receptionist-theme': {
            'primary': 'btn-primary-custom', 
            'secondary': 'btn-admin',
            'outline': 'btn-outline-custom',
            'efficiency': 'btn-efficiency'
        },
        'admin-theme': {
            'primary': 'btn-primary-custom',
            'secondary': 'btn-secondary-custom',
            'outline': 'btn-outline-custom'
        }
    }
    
    theme_buttons = button_classes.get(theme, button_classes['patient-theme'])
    return theme_buttons.get(button_type, 'btn-primary')


@register.simple_tag(takes_context=True)
def theme_card_class(context):
    """
    Returns the appropriate card class for the current theme
    """
    theme = get_user_theme(context)
    return 'card-custom'  # All themes use the same base card class


@register.inclusion_tag('components/theme_detector.html', takes_context=True)
def load_theme_css(context):
    """
    Inclusion tag that loads the appropriate theme CSS file
    Usage: {% load_theme_css %}
    """
    return {
        'theme_class': get_user_theme(context),
        'theme_css': get_theme_css_file(context),
        'theme_colors': get_theme_colors(context)
    }


@register.simple_tag(takes_context=True)
def get_user_role_display(context):
    """
    Returns a human-readable role name for the current user
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return 'Guest'
    
    user = request.user
    
    if user.is_superuser:
        return 'Administrator'
    
    try:
        if hasattr(user, 'doctorprofile'):
            return 'Doctor'
        elif hasattr(user, 'patientprofile'):
            return 'Patient'
        elif hasattr(user, 'receptionistprofile'):
            return 'Receptionist'
        elif hasattr(user, 'userprofile'):
            role = user.userprofile.role
            if role:
                return role.title()
    except Exception:
        pass
    
    return 'User'