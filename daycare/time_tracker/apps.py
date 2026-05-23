"""
time_tracker/apps.py
"""
from django.apps import AppConfig


class TimeTrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'time_tracker'
    verbose_name = 'Time Tracker'

    def ready(self):
        import time_tracker.signals  # noqa — connects all signal receivers
