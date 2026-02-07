"""
Enhanced Student Forms
Including Immunization Management
"""
from django import forms
from .models import (
    Student, StudentRegistration, Attendance, StudentContact,
    CustomField, IncidentReport, Immunization, VaccineDose,
    VaccineType, VaccineDoseSchedule
)
from accounts.models import User


class StudentForm(forms.ModelForm):
    """Enhanced form for creating/editing students (used by admin/staff)"""
    
    # Override parent field to only show parents
    parent = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.PARENT),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the parent/guardian for this student"
    )
    
    class Meta:
        model = Student
        fields = [
            'parent',
            'first_name', 
            'last_name', 
            'middle_name', 
            'date_of_birth', 
            'gender', 
            'photo', 
            'room',
            # Demographics
            'race',
            'ethnicity',
            # Medical
            'allergies', 
            'medical_conditions',
            'medications',
            'doctor_name',
            'doctor_phone',
            'doctor_address',
            # Emergency Contact
            'emergency_contact_name', 
            'emergency_contact_phone',
            'emergency_contact_relationship',
            # Address
            'address_line_1',
            'address_line_2',
            'city',
            'state',
            'postal_code',
            # Financial (Admin only)
            'parent_employer',
            'family_income',
            'has_subsidy',
            'subsidy_details',
            # School Details
            'status',
            'meal_type',
            'custom_student_id',
            # Enrollment Details
            'first_contact_date',
            'toured_date',
            'paperwork_date',
            'desired_start_date',
            'enrollment_date',
            'set_active_on_enrollment',
            'graduation_date',
            'expected_birth_date',
            'sibling_attending',
            'programs',
            'additional_details',
            'notes',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter middle name (optional)'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'room': forms.Select(attrs={
                'class': 'form-control'
            }),
            'race': forms.Select(attrs={
                'class': 'form-control'
            }),
            'ethnicity': forms.Select(attrs={
                'class': 'form-control'
            }),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'List any known allergies'
            }),
            'medical_conditions': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Describe any medical conditions'
            }),
            'medications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List current medications'
            }),
            'doctor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Doctor's name"
            }),
            'doctor_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Doctor's phone"
            }),
            'doctor_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': "Doctor's address"
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact full name'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact phone number'
            }),
            'emergency_contact_relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Relationship to child (e.g., Grandmother, Uncle)'
            }),
            'address_line_1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Street address'
            }),
            'address_line_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apt, Suite, etc. (optional)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postal code'
            }),
            'parent_employer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Parent's employer"
            }),
            'family_income': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Annual family income'
            }),
            'has_subsidy': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'subsidy_details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Subsidy program details'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'meal_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'custom_student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Custom student ID'
            }),
            'first_contact_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'toured_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'paperwork_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'desired_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'enrollment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'set_active_on_enrollment': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'graduation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expected_birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'sibling_attending': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name of sibling(s) attending'
            }),
            'programs': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Programs enrolled in'
            }),
            'additional_details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional details'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'General notes'
            }),
        }


class StudentContactForm(forms.ModelForm):
    """Form for adding/editing student contacts"""
    
    class Meta:
        model = StudentContact
        fields = [
            'full_name',
            'relationship',
            'email',
            'phone',
            'can_pickup',
            'is_emergency_contact',
            'can_view_brightwheel',
            'is_billing_contact',
            'notes'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name'
            }),
            'relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Mother, Father, Grandparent'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'can_pickup': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_emergency_contact': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_view_brightwheel': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_billing_contact': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }


class CustomFieldForm(forms.ModelForm):
    """Form for adding custom fields"""
    
    class Meta:
        model = CustomField
        fields = ['field_name', 'field_value']
        widgets = {
            'field_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Field name'
            }),
            'field_value': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Field value'
            }),
        }


class IncidentReportForm(forms.ModelForm):
    """Form for creating incident reports"""
    
    class Meta:
        model = IncidentReport
        fields = [
            'report_number',
            'report_date',
            'description',
            'follow_up_required',
            'follow_up_notes'
        ]
        widgets = {
            'report_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Report number (1, 2, 3...)'
            }),
            'report_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the incident'
            }),
            'follow_up_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'follow_up_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Follow-up notes'
            }),
        }


# ========== IMMUNIZATION FORMS ==========

class ImmunizationForm(forms.ModelForm):
    """Form for managing immunization settings"""
    
    class Meta:
        model = Immunization
        fields = [
            'is_exempt',
            'exemption_reason',
            'on_catch_up_schedule',
            'catch_up_notes',
            'notes'
        ]
        widgets = {
            'is_exempt': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'exemption_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Reason for exemption'
            }),
            'on_catch_up_schedule': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'catch_up_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Catch-up schedule notes'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'General immunization notes'
            }),
        }


class VaccineDoseForm(forms.ModelForm):
    """Form for recording individual vaccine doses"""
    
    class Meta:
        model = VaccineDose
        fields = [
            'date_administered',
            'administered_by',
            'location',
            'lot_number',
            'notes'
        ]
        widgets = {
            'date_administered': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'administered_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Healthcare provider name'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Clinic/hospital name'
            }),
            'lot_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vaccine lot number'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }


class BulkVaccineDoseUpdateForm(forms.Form):
    """Form for updating multiple vaccine doses at once"""
    
    date_administered = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Date Administered'
    )
    
    administered_by = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Healthcare provider'
        }),
        label='Administered By'
    )
    
    location = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Clinic/hospital'
        }),
        label='Location'
    )


# ========== ATTENDANCE FORMS ==========

class StudentRegistrationForm(forms.ModelForm):
    """Form for parent registration (public-facing)"""
    
    class Meta:
        model = StudentRegistration
        fields = [
            'child_first_name', 
            'child_last_name', 
            'child_middle_name',
            'child_dob', 
            'child_gender', 
            'medical_info', 
            'special_needs'
        ]
        widgets = {
            'child_first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Child\'s first name',
                'required': True
            }),
            'child_last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Child\'s last name',
                'required': True
            }),
            'child_middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Child\'s middle name (optional)'
            }),
            'child_dob': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'required': True
            }),
            'child_gender': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'medical_info': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Any medical information, allergies, or medications we should know about'
            }),
            'special_needs': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Any special needs or accommodations required'
            }),
        }
        labels = {
            'child_first_name': 'First Name',
            'child_last_name': 'Last Name',
            'child_middle_name': 'Middle Name',
            'child_dob': 'Date of Birth',
            'child_gender': 'Gender',
            'medical_info': 'Medical Information',
            'special_needs': 'Special Needs',
        }


class AttendanceForm(forms.ModelForm):
    """Form for recording student attendance"""
    
    class Meta:
        model = Attendance
        fields = [
            'student', 
            'date', 
            'status', 
            'check_in_time', 
            'check_out_time', 
            'notes'
        ]
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'check_in_time': forms.TimeInput(attrs={
                'class': 'form-control', 
                'type': 'time'
            }),
            'check_out_time': forms.TimeInput(attrs={
                'class': 'form-control', 
                'type': 'time'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about attendance'
            }),
        }


class MarkAbsentForm(forms.Form):
    """Form for marking students absent"""
    
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.filter(status='ACTIVE'),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Select Students to Mark Absent'
    )
    
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Date'
    )
    
    reason = forms.ChoiceField(
        choices=[
            ('ABSENT', 'Absent (Unexcused)'),
            ('EXCUSED', 'Excused Absence'),
        ],
        widget=forms.RadioSelect,
        label='Absence Type'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Reason for absence (optional)'
        }),
        label='Notes'
    )