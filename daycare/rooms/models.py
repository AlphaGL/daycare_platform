"""
Room (Classroom) Management Models
Room setup, capacity, staff assignment
"""
from django.db import models
from accounts.models import User


class Room(models.Model):
    """
    Classroom/Room Model
    Central to ratios, attendance, learning
    """
    
    class RoomType(models.TextChoices):
        INFANT = 'INFANT', 'Infant Room (0-12 months)'
        TODDLER = 'TODDLER', 'Toddler Room (1-2 years)'
        PRESCHOOL = 'PRESCHOOL', 'Preschool (3-4 years)'
        PREKINDERGARTEN = 'PREKINDERGARTEN', 'Pre-K (4-5 years)'
        MIXED = 'MIXED', 'Mixed Age'
    
    # Basic Information
    name = models.CharField(max_length=100, unique=True)
    room_type = models.CharField(
        max_length=20,
        choices=RoomType.choices,
        default=RoomType.MIXED
    )
    description = models.TextField(blank=True)
    
    # Capacity
    capacity = models.PositiveIntegerField(
        default=20,
        help_text="Maximum number of students"
    )
    
    # Age Range
    min_age_months = models.PositiveIntegerField(
        default=0,
        help_text="Minimum age in months"
    )
    max_age_months = models.PositiveIntegerField(
        default=60,
        help_text="Maximum age in months"
    )
    
    # Staff Assignment
    assigned_staff = models.ManyToManyField(
        User,
        related_name='assigned_rooms',
        limit_choices_to={'role': User.Role.STAFF},
        blank=True
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='rooms_created'
    )
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def current_enrollment(self):
        """Count active students in this room"""
        return self.students.filter(status='ACTIVE').count()
    
    @property
    def available_spots(self):
        """Calculate available spots"""
        return max(0, self.capacity - self.current_enrollment)
    
    @property
    def is_full(self):
        """Check if room is at capacity"""
        return self.current_enrollment >= self.capacity
    
    @property
    def staff_count(self):
        """Count assigned staff members"""
        return self.assigned_staff.filter(is_active=True, staff_profile__is_active_staff=True).count()
    
    @property
    def student_staff_ratio(self):
        """Calculate student-to-staff ratio"""
        staff = self.staff_count
        if staff == 0:
            return "N/A"
        ratio = self.current_enrollment / staff
        return f"{ratio:.1f}:1"
    
    def get_students(self):
        """Get all active students in this room"""
        return self.students.filter(status='ACTIVE')


class LessonPlan(models.Model):
    """
    Weekly lesson plans for rooms
    """
    
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='lesson_plans'
    )
    
    # Week information
    week_start_date = models.DateField()
    week_end_date = models.DateField()
    
    # Content
    theme = models.CharField(max_length=200, blank=True)
    objectives = models.TextField(blank=True)
    
    # Created by
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='lesson_plans_created'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-week_start_date']
        unique_together = ['room', 'week_start_date']
    
    def __str__(self):
        return f"{self.room.name} - Week of {self.week_start_date}"


class DailyActivity(models.Model):
    """
    Daily learning activities within a lesson plan
    """
    
    lesson_plan = models.ForeignKey(
        LessonPlan,
        on_delete=models.CASCADE,
        related_name='daily_activities'
    )
    
    # Day
    date = models.DateField()
    
    # Activities
    morning_activity = models.TextField(blank=True)
    afternoon_activity = models.TextField(blank=True)
    learning_goals = models.TextField(blank=True)
    materials_needed = models.TextField(blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date']
        unique_together = ['lesson_plan', 'date']
        verbose_name_plural = 'Daily Activities'
    
    def __str__(self):
        return f"{self.lesson_plan.room.name} - {self.date}"


class RoomDeviceMode(models.Model):
    """
    Device mode settings for rooms (for kiosk mode)
    """
    
    room = models.OneToOneField(
        Room,
        on_delete=models.CASCADE,
        related_name='device_mode'
    )
    
    # Device info
    device_name = models.CharField(max_length=100, blank=True)
    is_kiosk_mode = models.BooleanField(default=False)
    
    # Check-in settings
    allow_checkin = models.BooleanField(default=True)
    allow_checkout = models.BooleanField(default=True)
    require_signature = models.BooleanField(default=False)
    
    # Last activity
    last_used = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Device Mode: {self.room.name}"