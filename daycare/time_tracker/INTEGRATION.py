# Time Tracker — Integration Guide
# ====================================================================
# Follow these steps in order. Nothing in your existing code breaks.
# ====================================================================


# ── STEP 1: Copy the new app ─────────────────────────────────────────
# Place the `time_tracker/` folder alongside your other apps
# (accounts/, attendance/, students/, staff/, …)


# ── STEP 2: Register the app ─────────────────────────────────────────
# settings.py → INSTALLED_APPS

INSTALLED_APPS = [
    ...
    'time_tracker.apps.TimeTrackerConfig',   # ← add this
]


# ── STEP 3: Wire up URLs ─────────────────────────────────────────────
# project/urls.py

from django.urls import path, include

urlpatterns = [
    ...
    path('time/', include('time_tracker.urls', namespace='time_tracker')),
]


# ── STEP 4: Run migrations ───────────────────────────────────────────
#   python manage.py makemigrations time_tracker
#   python manage.py migrate


# ── STEP 5: (Optional) Track parent portal sessions ──────────────────
# Open accounts/views.py.  In user_login(), after `login(request, user)`:

    from time_tracker.signals import open_parent_session
    if user.is_parent:
        open_parent_session(user)

# In user_logout(), before `logout(request)`:

    from time_tracker.signals import close_parent_session
    if request.user.is_parent:
        close_parent_session(request.user)


# ── STEP 6: Add nav links ────────────────────────────────────────────
# In your base navbar template, add:

{% if user.is_admin or user.is_staff_member %}
  <a href="{% url 'time_tracker:live_dashboard' %}">⏱ Live Tracker</a>
  <a href="{% url 'time_tracker:analytics' %}">📊 Analytics</a>
{% endif %}
<a href="{% url 'time_tracker:my_sessions' %}">My Sessions</a>


# ====================================================================
# TEMPLATES NEEDED (all in templates/time_tracker/)
# ====================================================================
#
# 1. live_dashboard.html   — Admin/Staff: real-time everyone on site
# 2. analytics.html        — Admin/Staff: charts, breakdowns, trends
# 3. parent_sessions.html  — Parents: their children's live timers + history
# 4. staff_sessions.html   — Staff: their own clock-in history + weekly hours
#
# All four templates extend your existing `base.html`.
# They expect Bootstrap 5 + Chart.js (loaded from CDN in extra_js block).


# ====================================================================
# HOW IT WORKS (no existing code changed)
# ====================================================================
#
# Signal flow:
#   AttendanceCheckIn saved (status=CHECKED_IN)
#       → post_save signal → TimeSession.objects.get_or_create(ACTIVE)
#
#   AttendanceCheckIn saved (status=CHECKED_OUT)
#       → post_save signal → open TimeSession.close()
#
#   attendance.StaffTimecard saved (created, no clock_out)
#       → post_save signal → TimeSession(STAFF, ACTIVE) created
#
#   attendance.StaffTimecard saved (clock_out set)
#       → post_save signal → open staff TimeSession.close()
#
# Front-end:
#   - JS ticks every second locally (no server load)
#   - Every 30 s it calls /time/api/status/ to re-sync elapsed seconds
#     and update the on-site counts (picks up new arrivals/departures)
