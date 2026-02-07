"""
Enhanced Attendance Models
Check-in/Check-out with Code Verification and Health Screening
"""
from django.db import models
from django.utils import timezone
from students.models import Student
from rooms.models import Room
from accounts.models import User


class AttendanceCheckIn(models.Model):
    """
    Student Check-In/Check-Out Records
    With parent code verification and health screening
    """
    
    class Status(models.TextChoices):
        CHECKED_IN = 'CHECKED_IN', 'Checked In'
        CHECKED_OUT = 'CHECKED_OUT', 'Checked Out'
    
    # Student & Date
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='checkin_records'
    )
    date = models.DateField(default=timezone.now)
    
    # Check-in Details
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_in_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='checkins_performed'
    )
    check_in_code_verified = models.BooleanField(default=False)
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        related_name='daily_checkins'
    )
    
    # Health Screening
    is_healthy = models.BooleanField(
        default=True,
        help_text="Is the child healthy today?"
    )
    health_notes = models.TextField(
        blank=True,
        help_text="Additional health notes if needed"
    )
    
    # Check-out Details
    check_out_time = models.DateTimeField(null=True, blank=True)
    check_out_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='checkouts_performed'
    )
    check_out_code_verified = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.CHECKED_IN
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-check_in_time']
        unique_together = ['student', 'date']
        indexes = [
            models.Index(fields=['student', '-date']),
            models.Index(fields=['date', 'status']),
            models.Index(fields=['room', 'date']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.date} ({self.get_status_display()})"
    
    @property
    def duration(self):
        """Calculate time spent at daycare"""
        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            hours = delta.total_seconds() / 3600
            return f"{hours:.1f} hours"
        return "In progress"
    
    def perform_checkout(self, user, code_verified=False):
        """Perform checkout"""
        self.check_out_time = timezone.now()
        self.check_out_by = user
        self.check_out_code_verified = code_verified
        self.status = self.Status.CHECKED_OUT
        self.save()


class Schedule(models.Model):
    """
    Custom Schedules for Staff and Students
    Flexible scheduling system
    """
    
    class ScheduleType(models.TextChoices):
        STAFF_SHIFT = 'STAFF_SHIFT', 'Staff Shift'
        STUDENT_SCHEDULE = 'STUDENT_SCHEDULE', 'Student Schedule'
        ACTIVITY = 'ACTIVITY', 'Activity Schedule'
        ROOM_SCHEDULE = 'ROOM_SCHEDULE', 'Room Schedule'
        OTHER = 'OTHER', 'Other'
    
    class RecurrenceType(models.TextChoices):
        ONCE = 'ONCE', 'One Time'
        DAILY = 'DAILY', 'Daily'
        WEEKLY = 'WEEKLY', 'Weekly'
        MONTHLY = 'MONTHLY', 'Monthly'
    
    # Basic Info
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    schedule_type = models.CharField(
        max_length=20,
        choices=ScheduleType.choices,
        default=ScheduleType.OTHER
    )
    
    # Date & Time
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Recurrence
    recurrence_type = models.CharField(
        max_length=10,
        choices=RecurrenceType.choices,
        default=RecurrenceType.ONCE
    )
    
    # Assignments (optional - depends on schedule type)
    assigned_staff = models.ManyToManyField(
        User,
        related_name='attendance_schedules',
        blank=True,
        limit_choices_to={'role__in': [User.Role.STAFF, User.Role.ADMIN]}
    )
    assigned_students = models.ManyToManyField(
        Student,
        related_name='attendance_schedules',
        blank=True
    )
    assigned_room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_schedules'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Creator
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='schedules_created'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_date', 'start_time']
    
    def __str__(self):
        return f"{self.title} - {self.start_date} ({self.get_schedule_type_display()})"
    
    @property
    def duration(self):
        """Calculate duration in hours"""
        from datetime import datetime, timedelta
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        
        if end < start:
            end += timedelta(days=1)
        
        delta = end - start
        hours = delta.total_seconds() / 3600
        return f"{hours:.1f} hours"


class StaffTimecard(models.Model):
    """
    Staff Clock-In/Clock-Out Records
    For tracking staff attendance and hours
    """
    
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendance_timecards',
        limit_choices_to={'role': User.Role.STAFF}
    )
    
    date = models.DateField(default=timezone.now)
    
    # Clock times
    clock_in_time = models.DateTimeField()
    clock_out_time = models.DateTimeField(null=True, blank=True)
    
    # Break times
    break_start = models.DateTimeField(null=True, blank=True)
    break_end = models.DateTimeField(null=True, blank=True)
    
    # Assignment
    assigned_room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-clock_in_time']
        unique_together = ['staff', 'date', 'clock_in_time']
    
    def __str__(self):
        return f"{self.staff.get_full_name()} - {self.date}"
    
    @property
    def total_hours(self):
        """Calculate total hours worked"""
        if not self.clock_out_time:
            return "Still clocked in"
        
        total = self.clock_out_time - self.clock_in_time
        
        # Subtract break time if applicable
        if self.break_start and self.break_end:
            break_time = self.break_end - self.break_start
            total -= break_time
        
        hours = total.total_seconds() / 3600
        return f"{hours:.2f} hours"