"""
Student Management Models
Student registration, profiles, and parent linking
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField
from accounts.models import User
from rooms.models import Room
import uuid


class Student(models.Model):
    """
    Student Model - Core entity
    """
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        GRADUATED = 'GRADUATED', 'Graduated'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'
    
    # Unique identifier
    student_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    
    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=10,
        choices=[
            ('MALE', 'Male'),
            ('FEMALE', 'Female'),
        ]
    )
    
    # Photo
    photo = CloudinaryField('student_photos', blank=True, null=True)
    
    # Parent/Guardian
    parent = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='children',
        limit_choices_to={'role': User.Role.PARENT}
    )
    
    # Room Assignment
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    
    # Medical Information
    allergies = models.TextField(blank=True, help_text="List any allergies")
    medical_conditions = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Status
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    enrollment_date = models.DateField(auto_now_add=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['room']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} (ID: {self.student_id})"
    
    def get_full_name(self):
        """Return full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate age in years"""
        from datetime import date
        today = date.today()
        age = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or \
           (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1
        return age
    
    @property
    def age_in_months(self):
        """Calculate age in months"""
        from datetime import date
        today = date.today()
        months = (today.year - self.date_of_birth.year) * 12
        months += today.month - self.date_of_birth.month
        return months


class StudentRegistration(models.Model):
    """
    Student Registration Requests
    For new student enrollments with payment
    """
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        PAYMENT_PENDING = 'PAYMENT_PENDING', 'Payment Pending'
    
    # Registration ID
    registration_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    
    # Parent
    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='registration_requests'
    )
    
    # Student Information (before Student object is created)
    child_first_name = models.CharField(max_length=100)
    child_last_name = models.CharField(max_length=100)
    child_middle_name = models.CharField(max_length=100, blank=True)
    child_dob = models.DateField()
    child_gender = models.CharField(
        max_length=10,
        choices=[('MALE', 'Male'), ('FEMALE', 'Female')]
    )
    
    # Additional Info
    medical_info = models.TextField(blank=True)
    special_needs = models.TextField(blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Payment
    registration_fee_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # WhatsApp redirect
    whatsapp_redirected = models.BooleanField(default=False)
    whatsapp_redirect_at = models.DateTimeField(null=True, blank=True)
    
    # Created student (after approval)
    student = models.OneToOneField(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registration'
    )
    
    # Notes
    admin_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_registrations'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Registration: {self.child_first_name} {self.child_last_name} (ID: {self.registration_id})"
    
    def get_whatsapp_url(self):
        """Generate WhatsApp URL with pre-filled message"""
        from django.conf import settings
        message = settings.WHATSAPP_MESSAGE_TEMPLATE.format(
            registration_id=self.registration_id
        )
        # URL encode the message
        from urllib.parse import quote
        encoded_message = quote(message)
        whatsapp_number = settings.WHATSAPP_NUMBER
        return f"https://wa.me/{whatsapp_number}?text={encoded_message}"


class Attendance(models.Model):
    """
    Daily attendance tracking
    """
    
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LATE = 'LATE', 'Late'
        EXCUSED = 'EXCUSED', 'Excused Absence'
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PRESENT
    )
    
    # Check-in/out times
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    
    # Who checked in/out
    checked_in_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='check_ins'
    )
    checked_out_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='check_outs'
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['student', 'date']
        indexes = [
            models.Index(fields=['student', '-date']),
            models.Index(fields=['date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.date} ({self.get_status_display()})"