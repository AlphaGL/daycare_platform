from .models import SchoolProfile, SchoolSettings


def school_settings(request):
    """
    Makes school profile & settings available globally in templates
    """
    profile = SchoolProfile.get_instance()
    settings = SchoolSettings.get_instance()

    return {
        'school_profile': profile,
        'school_settings': settings,
    }
