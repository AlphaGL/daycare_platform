"""
time_tracker/urls.py
"""
from django.urls import path
from . import views

app_name = 'time_tracker'

urlpatterns = [
    # Admin / Staff
    path('',                        views.live_dashboard,       name='live_dashboard'),
    path('analytics/',              views.analytics_view,       name='analytics'),

    # All authenticated users
    path('my-sessions/',            views.my_sessions,          name='my_sessions'),

    # JSON polling (called by JS every 30 s)
    path('api/status/',             views.session_status_api,   name='session_status_api'),

    # Admin safety net
    path('sessions/<int:session_id>/force-close/',
                                    views.force_close_session,  name='force_close_session'),
]
