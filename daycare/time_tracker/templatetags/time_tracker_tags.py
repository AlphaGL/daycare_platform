"""
time_tracker/templatetags/time_tracker_tags.py

Custom template tags used by analytics.html.

Usage in template:
    {% load time_tracker_tags %}
    {% for d in "7,14,30,60,90"|split:"," %}
"""
from django import template

register = template.Library()


@register.filter(name='split')
def split_filter(value, delimiter=','):
    """Split a string by delimiter and return a list.
    
    Usage: {{ "a,b,c"|split:"," }}
    """
    return value.split(delimiter)