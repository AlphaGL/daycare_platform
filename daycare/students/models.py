"""
Enhanced Student Management Models
With Immunizations, Extended Fields, and Contact Management
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField
from accounts.models import User
from rooms.models import Room
import uuid
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class Student(models.Model):
    """
    Enhanced Student Model with Additional Fields
    """
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        GRADUATED = 'GRADUATED', 'Graduated'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'
    
    class Race(models.TextChoices):
        WHITE = 'WHITE', 'White'
        BLACK = 'BLACK', 'Black or African American'
        ASIAN = 'ASIAN', 'Asian'
        NATIVE_AMERICAN = 'NATIVE_AMERICAN', 'American Indian or Alaska Native'
        PACIFIC_ISLANDER = 'PACIFIC_ISLANDER', 'Native Hawaiian or Other Pacific Islander'
        TWO_OR_MORE = 'TWO_OR_MORE', 'Two or More Races'
        OTHER = 'OTHER', 'Other'
        PREFER_NOT = 'PREFER_NOT', 'Prefer not to say'
    
    class Ethnicity(models.TextChoices):
        HISPANIC = 'HISPANIC', 'Hispanic, Latino or Spanish Origin'
        NOT_HISPANIC = 'NOT_HISPANIC', 'Not of Hispanic, Latino or Spanish Origin'
        PREFER_NOT = 'PREFER_NOT', 'Prefer not to say'
    
    class MealType(models.TextChoices):
        NOT_SPECIFIED = 'NOT_SPECIFIED', 'Not specified'
        BREAKFAST = 'BREAKFAST', 'Breakfast'
        LUNCH = 'LUNCH', 'Lunch'
        SNACK = 'SNACK', 'Snack'
        DINNER = 'DINNER', 'Dinner'
        ALL_MEALS = 'ALL_MEALS', 'All Meals'
    
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
    
    # ========== NEW FIELDS ==========
    
    # Demographics (Not visible to parents)
    race = models.CharField(
        max_length=20,
        choices=Race.choices,
        blank=True,
        default='PREFER_NOT'
    )
    ethnicity = models.CharField(
        max_length=20,
        choices=Ethnicity.choices,
        blank=True,
        default='PREFER_NOT'
    )
    
    # Medical Information
    allergies = models.TextField(blank=True, help_text="List any allergies")
    medical_conditions = models.TextField(blank=True)
    medications = models.TextField(blank=True, help_text="Current medications")
    doctor_name = models.CharField(max_length=200, blank=True)
    doctor_phone = models.CharField(max_length=20, blank=True)
    doctor_address = models.TextField(blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Address
    address_line_1 = models.CharField(max_length=200, blank=True)
    address_line_2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Financial Details (Not visible to parents)
    parent_employer = models.CharField(max_length=200, blank=True)
    family_income = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    has_subsidy = models.BooleanField(default=False)
    subsidy_details = models.TextField(blank=True)
    
    # School Details (Not visible to parents)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    meal_type = models.CharField(
        max_length=20,
        choices=MealType.choices,
        default=MealType.NOT_SPECIFIED,
        blank=True
    )
    custom_student_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Custom student ID"
    )
    
    # Enrollment Details (Not visible to parents)
    first_contact_date = models.DateField(null=True, blank=True)
    toured_date = models.DateField(null=True, blank=True)
    paperwork_date = models.DateField(null=True, blank=True)
    desired_start_date = models.DateField(null=True, blank=True)
    enrollment_date = models.DateField(null=True, blank=True)
    set_active_on_enrollment = models.BooleanField(default=False)
    graduation_date = models.DateField(null=True, blank=True)
    expected_birth_date = models.DateField(
        null=True,
        blank=True,
        help_text="For unborn children"
    )
    sibling_attending = models.CharField(max_length=200, blank=True)
    programs = models.TextField(blank=True)
    additional_details = models.TextField(blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
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
        today = date.today()
        age = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or \
           (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1
        return age
    
    @property
    def age_in_months(self):
        """Calculate age in months"""
        today = date.today()
        months = (today.year - self.date_of_birth.year) * 12
        months += today.month - self.date_of_birth.month
        return months
    
    @property
    def age_display(self):
        """Return age as 'X years Y months'"""
        years = self.age
        total_months = self.age_in_months
        remaining_months = total_months - (years * 12)
        
        if years == 0:
            return f"{remaining_months} months old"
        elif remaining_months == 0:
            return f"{years} years old"
        else:
            return f"{years} years {remaining_months} months old"


class StudentContact(models.Model):
    """
    Additional contacts for students (beyond primary parent)
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    
    # Contact Information
    full_name = models.CharField(max_length=200)
    relationship = models.CharField(
        max_length=100,
        help_text="e.g., Mother, Father, Grandparent, Aunt, Authorized Pickup"
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    
    # Permissions
    can_pickup = models.BooleanField(
        default=False,
        help_text="Authorized to pick up child"
    )
    is_emergency_contact = models.BooleanField(default=False)
    can_view_brightwheel = models.BooleanField(
        default=False,
        help_text="Can sign in to view child info"
    )
    
    # Access code (if can_view_brightwheel is True)
    access_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="Code to add child in app"
    )
    
    # User account (if they've signed up)
    user_account = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authorized_children'
    )
    has_signed_up = models.BooleanField(default=False)
    
    # Billing
    is_billing_contact = models.BooleanField(default=False)
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['full_name']
    
    def __str__(self):
        return f"{self.full_name} ({self.relationship}) - {self.student.get_full_name()}"
    
    def generate_access_code(self):
        """Generate unique access code"""
        import random
        import string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        self.access_code = code
        self.save(update_fields=['access_code'])
        return code


class CustomField(models.Model):
    """
    Custom fields for students (admin-defined)
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='custom_fields'
    )
    
    field_name = models.CharField(max_length=200)
    field_value = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['field_name']
    
    def __str__(self):
        return f"{self.field_name}: {self.field_value}"


class IncidentReport(models.Model):
    """
    Incident reports for students
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='incident_reports'
    )
    
    report_date = models.DateField(default=date.today)
    report_number = models.PositiveIntegerField(
        help_text="Incident Report #1, #2, etc."
    )
    description = models.TextField()
    
    # Staff who reported
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='incident_reports_created'
    )
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-report_date', 'report_number']
        unique_together = ['student', 'report_number']
    
    def __str__(self):
        return f"Incident Report #{self.report_number} - {self.student.get_full_name()}"


# ========== IMMUNIZATION MODELS ==========

class VaccineType(models.Model):
    """
    Vaccine types based on CDC recommendations
    """
    name = models.CharField(max_length=100, unique=True)
    full_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # CDC recommended doses
    total_doses = models.PositiveIntegerField(default=1)
    
    # Is this vaccine active/in use?
    is_active = models.BooleanField(default=True)
    
    # Display order
    display_order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.full_name}"


class VaccineDoseSchedule(models.Model):
    """
    CDC recommended schedule for each vaccine dose
    """
    vaccine_type = models.ForeignKey(
        VaccineType,
        on_delete=models.CASCADE,
        related_name='dose_schedules'
    )
    
    dose_number = models.PositiveIntegerField()
    
    # Age recommendations
    recommended_age_months = models.PositiveIntegerField(
        help_text="Recommended age in months"
    )
    min_age_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum age for this dose"
    )
    max_age_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum age for this dose"
    )
    
    # CDC recommendation text
    cdc_recommendation_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g., '2 mos', '12-15 mos', '4-6 yrs'"
    )
    
    # Is this a catch-up dose?
    is_catch_up = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['vaccine_type', 'dose_number']
        unique_together = ['vaccine_type', 'dose_number']
    
    def __str__(self):
        return f"{self.vaccine_type.name} - Dose {self.dose_number} ({self.cdc_recommendation_text})"


class Immunization(models.Model):
    """
    Student immunization records
    NOT VISIBLE TO PARENTS - Admin/Staff only
    """
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name='immunization_record'
    )
    
    # Exemption settings
    is_exempt = models.BooleanField(
        default=False,
        help_text="Student exempt from immunizations"
    )
    exemption_reason = models.TextField(blank=True)
    
    # Catch-up schedule
    on_catch_up_schedule = models.BooleanField(default=False)
    catch_up_notes = models.TextField(blank=True)
    
    # General notes
    notes = models.TextField(blank=True)
    
    # Last updated
    last_updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='immunization_updates'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Immunization Record'
        verbose_name_plural = 'Immunization Records'
    
    def __str__(self):
        return f"Immunizations - {self.student.get_full_name()}"
    
    def get_overdue_vaccines(self):
        """Get list of overdue vaccine doses"""
        overdue = []
        doses = self.vaccine_doses.select_related('vaccine_type', 'dose_schedule')
        
        for dose in doses:
            if dose.is_overdue:
                overdue.append(dose)
        
        return overdue
    
    def get_due_soon_vaccines(self, days=30):
        """Get vaccines due within specified days"""
        due_soon = []
        doses = self.vaccine_doses.select_related('vaccine_type', 'dose_schedule')
        
        for dose in doses:
            if dose.is_due_soon(days):
                due_soon.append(dose)
        
        return due_soon
    
    def get_completion_percentage(self):
        """Calculate immunization completion percentage"""
        total_doses = self.vaccine_doses.count()
        if total_doses == 0:
            return 0
        
        completed = self.vaccine_doses.filter(
            date_administered__isnull=False
        ).count()
        
        return int((completed / total_doses) * 100)


class VaccineDose(models.Model):
    """
    Individual vaccine dose records for a student
    """
    immunization = models.ForeignKey(
        Immunization,
        on_delete=models.CASCADE,
        related_name='vaccine_doses'
    )
    
    vaccine_type = models.ForeignKey(
        VaccineType,
        on_delete=models.PROTECT
    )
    
    dose_schedule = models.ForeignKey(
        VaccineDoseSchedule,
        on_delete=models.PROTECT,
        help_text="CDC recommended schedule for this dose"
    )
    
    # Administration details
    date_administered = models.DateField(
        null=True,
        blank=True,
        help_text="Date this dose was given"
    )
    administered_by = models.CharField(
        max_length=200,
        blank=True,
        help_text="Healthcare provider who administered"
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Clinic/hospital where administered"
    )
    lot_number = models.CharField(max_length=100, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Recorded by (staff member who entered the data)
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vaccine_doses_recorded'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['vaccine_type', 'dose_schedule__dose_number']
        unique_together = ['immunization', 'vaccine_type', 'dose_schedule']
    
    def __str__(self):
        status = "✓" if self.date_administered else "✗"
        return f"{status} {self.vaccine_type.name} Dose {self.dose_schedule.dose_number} - {self.immunization.student.get_full_name()}"
    
    @property
    def is_administered(self):
        """Check if dose has been given"""
        return self.date_administered is not None
    
    @property
    def is_overdue(self):
        """Check if dose is overdue based on student's age and CDC schedule"""
        if self.is_administered:
            return False
        
        if self.immunization.is_exempt:
            return False
        
        student = self.immunization.student
        student_age_months = student.age_in_months
        
        # Check if student is past the recommended age
        recommended_age = self.dose_schedule.recommended_age_months
        
        # Add grace period of 2 months
        grace_period_months = 2
        
        if student_age_months > (recommended_age + grace_period_months):
            return True
        
        return False
    
    def is_due_soon(self, days=30):
        """Check if dose is due within specified days"""
        if self.is_administered:
            return False
        
        if self.immunization.is_exempt:
            return False
        
        student = self.immunization.student
        student_age_months = student.age_in_months
        recommended_age = self.dose_schedule.recommended_age_months
        
        # Calculate when dose is due
        months_until_due = recommended_age - student_age_months
        days_until_due = months_until_due * 30  # Approximate
        
        return 0 < days_until_due <= days
    
    @property
    def status_display(self):
        """Human-readable status"""
        if self.is_administered:
            return "Completed"
        elif self.is_overdue:
            return "Overdue"
        elif self.is_due_soon(30):
            return "Due Soon"
        else:
            return "Upcoming"
    
    @property
    def recommended_date(self):
        """Calculate recommended date based on student DOB"""
        student = self.immunization.student
        recommended_date = student.date_of_birth + relativedelta(
            months=self.dose_schedule.recommended_age_months
        )
        return recommended_date


# ========== EXISTING MODELS (Updated) ==========

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