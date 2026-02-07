"""
Context Processors
Makes common data available across all templates
"""
from .models import SchoolProfile, SchoolSettings


def school_context(request):
    """
    Add school profile and settings to all template contexts
    """
    try:
        school = SchoolProfile.get_instance()
        settings = SchoolSettings.get_instance()
    except:
        school = None
        settings = None
    
    return {
        'school': school,
        'school_settings': settings,
    }