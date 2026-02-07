"""
School Profile & Settings Models
Controls the entire system behavior
"""
from django.db import models
from cloudinary.models import CloudinaryField


class SchoolProfile(models.Model):
    """
    School Profile - Single instance
    Contains all school information
    """
    
    # Basic Information
    school_name = models.CharField(max_length=200)
    tagline = models.CharField(max_length=300, blank=True)
    logo = CloudinaryField('school_logos', blank=True, null=True)
    
    # Contact Information
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # Address
    address_line_1 = models.CharField(max_length=200)
    address_line_2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Nigeria')
    
    # About
    description = models.TextField(blank=True)
    established_year = models.PositiveIntegerField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'School Profile'
        verbose_name_plural = 'School Profile'
    
    def __str__(self):
        return self.school_name
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        if not self.pk and SchoolProfile.objects.exists():
            raise ValueError('Only one School Profile can exist')
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        """Get or create the single school profile instance"""
        instance, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'school_name': 'Sugamama sugababies Daycare',
                'phone': '+234 XXX XXX XXXX',
                'email': 'info@daycare.com',
                'address_line_1': 'Your Address',
                'city': 'Port Harcourt',
                'state': 'Rivers',
                'country': 'Nigeria'
            }
        )
        return instance


class SchoolSettings(models.Model):
    """
    School Settings - Controls system behavior
    Boolean flags for features
    """
    
    school = models.OneToOneField(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    
    # Check-in Settings
    checkin_enabled = models.BooleanField(
        default=True,
        help_text="Enable/disable check-in kiosk mode"
    )
    require_checkin_code = models.BooleanField(
        default=True,
        help_text="Require check-in code for kiosk access"
    )
    
    # Room Settings
    auto_assign_rooms = models.BooleanField(
        default=False,
        help_text="Automatically assign students to rooms based on age"
    )
    max_students_per_room = models.PositiveIntegerField(
        default=20,
        help_text="Maximum students per room"
    )
    
    # Learning Framework
    learning_framework = models.CharField(
        max_length=100,
        default='Montessori',
        help_text="Primary learning framework (e.g., Montessori, Reggio Emilia)"
    )
    
    # Parent Permissions
    parents_can_edit_student_info = models.BooleanField(
        default=False,
        help_text="Allow parents to edit their child's information"
    )
    parents_can_add_activities = models.BooleanField(
        default=False,
        help_text="Allow parents to add activities for their children"
    )
    
    # Staff Permissions
    default_activities_to_staff_only = models.BooleanField(
        default=True,
        help_text="Show default activities only to staff members"
    )
    
    # Communication
    enable_parent_messaging = models.BooleanField(
        default=True,
        help_text="Enable messaging between parents and staff"
    )
    enable_staff_messaging = models.BooleanField(
        default=True,
        help_text="Enable messaging between staff members"
    )
    
    # Registration
    registration_enabled = models.BooleanField(
        default=True,
        help_text="Allow new parent registrations"
    )
    registration_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Registration fee amount"
    )
    
    # Notifications
    send_welcome_emails = models.BooleanField(
        default=True,
        help_text="Send welcome emails to new users"
    )
    send_activity_notifications = models.BooleanField(
        default=True,
        help_text="Send notifications for important activities"
    )
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='settings_updates'
    )
    
    class Meta:
        verbose_name = 'School Settings'
        verbose_name_plural = 'School Settings'
    
    def __str__(self):
        return f"Settings for {self.school.school_name}"
    
    @classmethod
    def get_instance(cls):
        """Get or create settings for the school"""
        school = SchoolProfile.get_instance()
        settings, created = cls.objects.get_or_create(school=school)
        return settings


class Reminder(models.Model):
    """
    System Reminders for Admin
    """
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'
    
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='reminders_created'
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    
    # Reminder date/time
    remind_at = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Notification
    send_email = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['is_completed', '-priority', 'remind_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_priority_display()}"