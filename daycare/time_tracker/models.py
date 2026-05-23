"""
Time Tracker Models
Real-time session tracking for Students, Staff, and Parents.
Extends the existing AttendanceCheckIn without breaking it.
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta


class TimeSession(models.Model):
    """
    Universal live time-tracking session.

    One row = one person on the premises right now (or in the past).
    Works for:
      - Students  (linked via student_checkin FK to AttendanceCheckIn)
      - Staff     (linked via staff ForeignKey to User)
      - Parents   (linked via parent ForeignKey to User — optional drop-off visits)

    Only ONE of (student_checkin, staff, parent) should be set per row.
    """

    class SessionType(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        STAFF   = 'STAFF',   'Staff'
        PARENT  = 'PARENT',  'Parent'

    class Status(models.TextChoices):
        ACTIVE   = 'ACTIVE',   'Active (On Site)'
        CLOSED   = 'CLOSED',   'Closed (Left)'
        VOID     = 'VOID',     'Void (Error / Removed)'

    # ── Who ──────────────────────────────────────────────────────────────────
    session_type = models.CharField(max_length=10, choices=SessionType.choices)

    # Student path — links to the existing check-in record
    student_checkin = models.OneToOneField(
        'attendance.AttendanceCheckIn',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='time_session',
    )

    # Staff / Parent path
    staff = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='time_sessions_as_staff',
        limit_choices_to={'role__in': ['STAFF', 'ADMIN']},
    )
    parent = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='time_sessions_as_parent',
        limit_choices_to={'role': 'PARENT'},
    )

    # ── When ─────────────────────────────────────────────────────────────────
    clock_in  = models.DateTimeField(default=timezone.now)
    clock_out = models.DateTimeField(null=True, blank=True)

    # ── State ────────────────────────────────────────────────────────────────
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    # ── Meta ─────────────────────────────────────────────────────────────────
    date       = models.DateField(default=timezone.localdate)
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-clock_in']
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['session_type', 'status']),
            models.Index(fields=['staff', 'date']),
            models.Index(fields=['parent', 'date']),
        ]

    # ── Helpers ──────────────────────────────────────────────────────────────
    def __str__(self):
        who = self.display_name
        state = '⏳' if self.is_active else '✓'
        return f"{state} {who} — {self.clock_in:%d %b %Y %H:%M}"

    @property
    def display_name(self):
        if self.session_type == self.SessionType.STUDENT and self.student_checkin:
            return self.student_checkin.student.get_full_name()
        if self.session_type == self.SessionType.STAFF and self.staff:
            return self.staff.get_full_name()
        if self.session_type == self.SessionType.PARENT and self.parent:
            return self.parent.get_full_name()
        return 'Unknown'

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    @property
    def elapsed_seconds(self):
        """Seconds since clock-in (live if active, fixed if closed)."""
        end = self.clock_out if self.clock_out else timezone.now()
        delta = end - self.clock_in
        return max(int(delta.total_seconds()), 0)

    @property
    def elapsed_display(self):
        """Human-readable elapsed time, e.g. '2h 34m'."""
        s = self.elapsed_seconds
        h, rem = divmod(s, 3600)
        m, _   = divmod(rem, 60)
        if h:
            return f"{h}h {m}m"
        return f"{m}m"

    @property
    def duration_hours(self):
        """Float hours — used for analytics."""
        return round(self.elapsed_seconds / 3600, 2)

    def close(self, notes=''):
        """Cleanly close a session."""
        if not self.is_active:
            return
        self.clock_out = timezone.now()
        self.status    = self.Status.CLOSED
        if notes:
            self.notes = notes
        self.save(update_fields=['clock_out', 'status', 'notes', 'updated_at'])

    # ── Validators ───────────────────────────────────────────────────────────
    def clean(self):
        filled = [
            bool(self.student_checkin),
            bool(self.staff_id),
            bool(self.parent_id),
        ]
        if sum(filled) > 1:
            raise ValidationError(
                "A TimeSession must link to exactly one of: student_checkin, staff, or parent."
            )


class DailySummary(models.Model):
    """
    Aggregated per-person daily stats (built by a management command or signal).
    Lets the analytics dashboard run fast queries without scanning all sessions.
    """

    class PersonType(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        STAFF   = 'STAFF',   'Staff'
        PARENT  = 'PARENT',  'Parent'

    date        = models.DateField()
    person_type = models.CharField(max_length=10, choices=PersonType.choices)

    # Generic reference (one of these will be set)
    user    = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='daily_summaries',
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='daily_summaries',
    )

    total_sessions    = models.PositiveIntegerField(default=0)
    total_hours       = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    first_arrival     = models.TimeField(null=True, blank=True)
    last_departure    = models.TimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['date', 'person_type', 'user'], ['date', 'person_type', 'student']]
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date', 'person_type']),
        ]

    def __str__(self):
        who = self.student or self.user
        return f"{who} — {self.date} ({self.total_hours}h)"
