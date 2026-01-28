"""
Staff Management Models
Schedules, timecards, health checks
"""
from django.db import models
from django.utils import timezone
from accounts.models import User


class StaffSchedule(models.Model):
    """
    Staff work schedules
    """
    
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 1, 'Monday'
        TUESDAY = 2, 'Tuesday'
        WEDNESDAY = 3, 'Wednesday'
        THURSDAY = 4, 'Thursday'
        FRIDAY = 5, 'Friday'
        SATURDAY = 6, 'Saturday'
        SUNDAY = 7, 'Sunday'
    
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='schedules',
        limit_choices_to={'role': User.Role.STAFF}
    )
    
    # Schedule details
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Room assignment for this shift
    room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='schedules'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = ['staff', 'day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.staff.get_full_name()} - {self.get_day_of_week_display()} ({self.start_time}-{self.end_time})"


class Timecard(models.Model):
    """
    Staff clock in/out records
    """
    
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='timecards',
        limit_choices_to={'role': User.Role.STAFF}
    )
    
    # Date and times
    date = models.DateField()
    clock_in = models.TimeField()
    clock_out = models.TimeField(null=True, blank=True)
    
    # Break times
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Approved
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timecards_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-clock_in']
        unique_together = ['staff', 'date', 'clock_in']
    
    def __str__(self):
        return f"{self.staff.get_full_name()} - {self.date}"
    
    @property
    def total_hours(self):
        """Calculate total hours worked"""
        if not self.clock_out:
            return 0
        
        from datetime import datetime, timedelta
        
        # Combine date with times
        clock_in_dt = datetime.combine(self.date, self.clock_in)
        clock_out_dt = datetime.combine(self.date, self.clock_out)
        
        # Calculate work duration
        work_duration = clock_out_dt - clock_in_dt
        
        # Subtract break time if exists
        if self.break_start and self.break_end:
            break_start_dt = datetime.combine(self.date, self.break_start)
            break_end_dt = datetime.combine(self.date, self.break_end)
            break_duration = break_end_dt - break_start_dt
            work_duration -= break_duration
        
        # Return hours as float
        return work_duration.total_seconds() / 3600


class HealthCheck(models.Model):
    """
    Daily health checks for staff
    """
    
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='health_checks',
        limit_choices_to={'role': User.Role.STAFF}
    )
    
    # Date
    check_date = models.DateField()
    
    # Health questions
    has_fever = models.BooleanField(default=False)
    has_cough = models.BooleanField(default=False)
    has_symptoms = models.BooleanField(
        default=False,
        help_text="Any COVID-19 or illness symptoms"
    )
    
    # Temperature
    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Temperature in Celsius"
    )
    
    # Additional notes
    notes = models.TextField(blank=True)
    
    # Cleared for work
    cleared_for_work = models.BooleanField(default=True)
    
    # Who performed check
    checked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='health_checks_performed'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-check_date']
        unique_together = ['staff', 'check_date']
    
    def __str__(self):
        status = "✓ Cleared" if self.cleared_for_work else "✗ Not Cleared"
        return f"{self.staff.get_full_name()} - {self.check_date} ({status})"


class StaffDocument(models.Model):
    """
    Staff documents (certificates, training, etc.)
    """
    
    class DocumentType(models.TextChoices):
        ID = 'ID', 'Identification'
        CERTIFICATE = 'CERTIFICATE', 'Certificate'
        TRAINING = 'TRAINING', 'Training Record'
        MEDICAL = 'MEDICAL', 'Medical Record'
        BACKGROUND = 'BACKGROUND', 'Background Check'
        OTHER = 'OTHER', 'Other'
    
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='documents',
        limit_choices_to={'role': User.Role.STAFF}
    )
    
    # Document info
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # File (Cloudinary)
    from cloudinary.models import CloudinaryField
    file = CloudinaryField('staff_documents', resource_type='raw')
    
    # Expiry (for certificates, etc.)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Uploaded by
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents_uploaded'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.staff.get_full_name()} - {self.title}"
    
    @property
    def is_expired(self):
        """Check if document is expired"""
        if not self.expiry_date:
            return False
        from datetime import date
        return date.today() > self.expiry_date