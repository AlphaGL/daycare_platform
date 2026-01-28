"""
Custom User Model with Role-Based Access Control
Foundation for security and accountability
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from cloudinary.models import CloudinaryField


class User(AbstractUser):
    """
    Custom User Model - Foundation of the entire system
    Supports: Admin, Staff, Parent roles
    """
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        STAFF = 'STAFF', 'Staff Member'
        PARENT = 'PARENT', 'Parent/Guardian'
    
    # Core fields
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.PARENT
    )
    
    # Profile information
    phone = models.CharField(max_length=20, blank=True)
    profile_photo = CloudinaryField('profile_photos', blank=True, null=True)
    
    # Security & Tracking
    check_in_code = models.CharField(
        max_length=6,
        blank=True,
        help_text="Personal check-in code (can be changed)"
    )
    last_activity = models.DateTimeField(auto_now=True)
    is_active_user = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active_user']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    def get_full_name(self):
        """Return full name or username"""
        full_name = super().get_full_name()
        return full_name if full_name else self.username
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_staff_member(self):
        return self.role == self.Role.STAFF
    
    @property
    def is_parent(self):
        return self.role == self.Role.PARENT
    
    def generate_check_in_code(self):
        """Generate a random 6-digit check-in code"""
        import random
        self.check_in_code = str(random.randint(100000, 999999))
        self.save(update_fields=['check_in_code'])
        return self.check_in_code


class UserActivity(models.Model):
    """
    Digital Footprint - Track all user actions
    For accountability and security
    """
    
    class ActionType(models.TextChoices):
        LOGIN = 'LOGIN', 'Login'
        LOGOUT = 'LOGOUT', 'Logout'
        CREATE = 'CREATE', 'Create Record'
        UPDATE = 'UPDATE', 'Update Record'
        DELETE = 'DELETE', 'Delete Record'
        VIEW = 'VIEW', 'View Record'
        EXPORT = 'EXPORT', 'Export Data'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    action_type = models.CharField(
        max_length=10,
        choices=ActionType.choices
    )
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Optional: What was affected
    content_type = models.CharField(max_length=100, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'User Activities'
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action_type} - {self.timestamp}"


class ParentProfile(models.Model):
    """
    Extended profile for parents
    Linked to students
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='parent_profile',
        limit_choices_to={'role': User.Role.PARENT}
    )
    
    # Additional parent info
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    relationship_to_child = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g., Mother, Father, Guardian"
    )
    
    # Preferences (from school settings)
    can_edit_student_info = models.BooleanField(default=False)
    can_add_activities = models.BooleanField(default=False)
    
    # Notifications
    receive_email_notifications = models.BooleanField(default=True)
    receive_sms_notifications = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Parent: {self.user.get_full_name()}"
    
    @property
    def children(self):
        """Get all children linked to this parent"""
        return self.user.children.all()


class StaffProfile(models.Model):
    """
    Extended profile for staff members
    With digital footprint
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='staff_profile',
        limit_choices_to={'role': User.Role.STAFF}
    )
    
    # Professional info
    position = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50, unique=True, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    
    # Access level
    access_level = models.CharField(
        max_length=20,
        choices=[
            ('BASIC', 'Basic Access'),
            ('ADVANCED', 'Advanced Access'),
            ('FULL', 'Full Access'),
        ],
        default='BASIC'
    )
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    # Status
    is_active_staff = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Staff Profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"
    
    @property
    def assigned_rooms(self):
        """Get rooms assigned to this staff member"""
        return self.user.assigned_rooms.all()