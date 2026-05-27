"""
time_tracker/apps.py

Connects the signals in signals.py so that TimeSession rows are
automatically created/closed whenever attendance check-in/out happens.

Without this file the signals are never registered and the live dashboard
shows nothing.
"""
from django.apps import AppConfig


class TimeTrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'time_tracker'
    verbose_name = 'Time Tracker'

    def ready(self):
        # Importing the signals module here registers all @receiver decorators.
        import time_tracker.signals  # noqa: F401