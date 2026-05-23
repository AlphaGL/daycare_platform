"""
time_tracker/templatetags/time_tracker_tags.py

Custom template filters for the time_tracker app.

Usage in templates:
    {% load time_tracker_tags %}
    {% for d in "7,14,30,60,90"|split:"," %}
        ...
    {% endfor %}
"""
from django import template

register = template.Library()


@register.filter
def split(value, delimiter=','):
    """Split a string by a delimiter and return a list."""
    return value.split(delimiter)