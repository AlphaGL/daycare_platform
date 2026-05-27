"""
time_tracker/signals.py

Automatically creates a TimeSession when a student is checked in,
and closes it when they check out — no extra code needed in attendance/views.py.

Also wires up staff clock-in/out from attendance.StaffTimecard.

Connected in time_tracker/apps.py → ready() method.

FIXED: Uses timezone.localdate() so session dates match America/Chicago,
       not the OS system clock.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


# ── Student check-in → open a TimeSession ─────────────────────────────────────

@receiver(post_save, sender='attendance.AttendanceCheckIn')
def sync_student_session(sender, instance, created, **kwargs):
    """
    post_save on AttendanceCheckIn:
      - CHECKED_IN  → create an ACTIVE TimeSession (if not already present)
      - CHECKED_OUT → close the TimeSession
    """
    from .models import TimeSession

    if instance.status == 'CHECKED_IN':
        TimeSession.objects.get_or_create(
            student_checkin=instance,
            defaults={
                'session_type': TimeSession.SessionType.STUDENT,
                'clock_in': instance.check_in_time or timezone.now(),
                'date': instance.date,   # date is already set correctly in the view
                'status': TimeSession.Status.ACTIVE,
            },
        )

    elif instance.status == 'CHECKED_OUT':
        try:
            session = TimeSession.objects.get(
                student_checkin=instance,
                status=TimeSession.Status.ACTIVE,
            )
            session.close()
            if instance.check_out_time:
                session.clock_out = instance.check_out_time
                session.save(update_fields=['clock_out', 'updated_at'])
        except TimeSession.DoesNotExist:
            pass


# ── Staff timecard → open/close TimeSession ────────────────────────────────────

@receiver(post_save, sender='attendance.StaffTimecard')
def sync_staff_session(sender, instance, created, **kwargs):
    """
    post_save on attendance.StaffTimecard:
      - created with no clock_out → open a staff TimeSession
      - clock_out set             → close the TimeSession
    """
    from .models import TimeSession

    if created and not instance.clock_out_time:
        TimeSession.objects.get_or_create(
            staff=instance.staff,
            date=instance.date,
            clock_in=instance.clock_in_time,
            defaults={
                'session_type': TimeSession.SessionType.STAFF,
                'status': TimeSession.Status.ACTIVE,
            },
        )

    elif instance.clock_out_time:
        session_qs = TimeSession.objects.filter(
            staff=instance.staff,
            date=instance.date,
            status=TimeSession.Status.ACTIVE,
        )
        for session in session_qs:
            session.close()
            session.clock_out = instance.clock_out_time
            session.save(update_fields=['clock_out', 'updated_at'])


# ── Parent portal visit tracking (optional) ───────────────────────────────────

def open_parent_session(user, request=None):
    """
    Call from accounts/views.py → user_login() after a successful parent login
    if you want to track portal visit durations.
    """
    from .models import TimeSession
    today = timezone.localdate()

    already = TimeSession.objects.filter(
        parent=user,
        date=today,
        status=TimeSession.Status.ACTIVE,
    ).exists()

    if not already:
        TimeSession.objects.create(
            session_type=TimeSession.SessionType.PARENT,
            parent=user,
            date=today,
            clock_in=timezone.now(),
            status=TimeSession.Status.ACTIVE,
        )


def close_parent_session(user):
    """Call from accounts/views.py → user_logout() for parents."""
    from .models import TimeSession
    today = timezone.localdate()
    for session in TimeSession.objects.filter(
        parent=user,
        date=today,
        status=TimeSession.Status.ACTIVE,
    ):
        session.close()