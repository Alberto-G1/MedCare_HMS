"""
Context processor for dynamic theming across MedCare HMS
Adds theme-related variables to all template contexts
"""

def theme_context(request):
    """
    Context processor that adds theme information to all templates
    """
    theme_data = {
        'theme_class': 'patient-theme',  # Default theme
        'theme_css': 'css/themes/patient-theme.css',
        'theme_colors': {
            'primary': '#0E7490',
            'primary_dark': '#0C4A6E',
            'primary_light': '#67E8F9',
            'secondary': '#0284C7'
        },
        'user_role': 'User'
    }
    
    if request.user.is_authenticated:
        user = request.user
        
        # Determine user role and theme
        if user.is_superuser or user.is_staff:
            theme_data.update({
                'theme_class': 'admin-theme',
                'theme_css': 'css/themes/doctor-theme.css',  # Admin uses doctor theme
                'theme_colors': {
                    'primary': '#14B8A6',
                    'primary_dark': '#0F766E',
                    'primary_light': '#5EEAD4',
                    'secondary': '#0284C7'
                },
                'user_role': 'Administrator'
            })
        else:
            try:
                # Check for specific role profiles
                if hasattr(user, 'doctorprofile'):
                    theme_data.update({
                        'theme_class': 'doctor-theme',
                        'theme_css': 'css/themes/doctor-theme.css',
                        'theme_colors': {
                            'primary': '#14B8A6',
                            'primary_dark': '#0F766E',
                            'primary_light': '#5EEAD4',
                            'secondary': '#0284C7'
                        },
                        'user_role': 'Doctor'
                    })
                elif hasattr(user, 'patientprofile'):
                    theme_data.update({
                        'theme_class': 'patient-theme',
                        'theme_css': 'css/themes/patient-theme.css',
                        'theme_colors': {
                            'primary': '#0E7490',
                            'primary_dark': '#0C4A6E',
                            'primary_light': '#67E8F9',
                            'secondary': '#0284C7'
                        },
                        'user_role': 'Patient'
                    })
                elif hasattr(user, 'receptionistprofile'):
                    theme_data.update({
                        'theme_class': 'receptionist-theme',
                        'theme_css': 'css/themes/receptionist-theme.css',
                        'theme_colors': {
                            'primary': '#5ce9f6',
                            'primary_dark': '#0891b2',
                            'primary_light': '#a5f3fc',
                            'secondary': '#0284C7'
                        },
                        'user_role': 'Receptionist'
                    })
                elif hasattr(user, 'userprofile'):
                    # Fallback to userprofile role
                    role = user.userprofile.role.lower() if user.userprofile.role else 'patient'
                    if role == 'doctor':
                        theme_data.update({
                            'theme_class': 'doctor-theme',
                            'theme_css': 'css/themes/doctor-theme.css',
                            'theme_colors': {
                                'primary': '#14B8A6',
                                'primary_dark': '#0F766E',
                                'primary_light': '#5EEAD4',
                                'secondary': '#0284C7'
                            },
                            'user_role': 'Doctor'
                        })
                    elif role == 'receptionist':
                        theme_data.update({
                            'theme_class': 'receptionist-theme',
                            'theme_css': 'css/themes/receptionist-theme.css',
                            'theme_colors': {
                                'primary': '#5ce9f6',
                                'primary_dark': '#0891b2',
                                'primary_light': '#a5f3fc',
                                'secondary': '#0284C7'
                            },
                            'user_role': 'Receptionist'
                        })
                        
            except Exception:
                # If any error occurs, keep default patient theme
                pass
    
    return theme_data