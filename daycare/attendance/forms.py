"""
Attendance and Schedule Forms
FIXED: CheckOutForm now handles empty check_in_code gracefully,
       and falls back to staff override when no code is set.
"""
from django import forms
from .models import AttendanceCheckIn, Schedule, StaffTimecard
from students.models import Student
from rooms.models import Room
from accounts.models import User


class CheckInForm(forms.ModelForm):
    """
    Student Check-In Form
    Parents check in their own children with their check-in code
    """
    
    parent_check_in_code = forms.CharField(
        max_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': 'Enter 6-digit code',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'autofocus': True,
            'style': 'letter-spacing: 0.5rem; font-size: 2rem; font-weight: bold;'
        }),
        help_text="Enter your check-in code"
    )
    
    class Meta:
        model = AttendanceCheckIn
        fields = ['student', 'room', 'is_healthy', 'health_notes', 'notes']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-control form-control-lg',
                'required': True
            }),
            'room': forms.Select(attrs={
                'class': 'form-control form-control-lg',
                'required': True
            }),
            'is_healthy': forms.RadioSelect(
                choices=[(True, 'Yes - Child is healthy'), (False, 'No - Child has health concerns')],
                attrs={'class': 'form-check-input'}
            ),
            'health_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any health concerns or notes (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes (optional)'
            }),
        }
        labels = {
            'student': 'Select Student',
            'room': 'Select Room',
            'is_healthy': 'Is the child healthy today?',
            'health_notes': 'Health Notes',
            'notes': 'Additional Notes',
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            if self.user.is_parent:
                self.fields['student'].queryset = Student.objects.filter(
                    parent=self.user,
                    status='ACTIVE'
                ).order_by('first_name', 'last_name')
            else:
                self.fields['student'].queryset = Student.objects.filter(
                    status='ACTIVE'
                ).order_by('first_name', 'last_name')
        
        self.fields['room'].queryset = Room.objects.filter(is_active=True).order_by('name')
    
    def clean_parent_check_in_code(self):
        """Validate the check-in code"""
        code = self.cleaned_data.get('parent_check_in_code')
        
        if self.user and self.user.is_parent:
            # BUG FIX: if the parent has no code set, block check-in and
            # tell them to set one — don't silently fail or always pass.
            if not self.user.check_in_code:
                raise forms.ValidationError(
                    "You have not set a check-in code yet. "
                    "Please go to your profile and set a 6-digit check-in code first."
                )
            if self.user.check_in_code != code:
                raise forms.ValidationError(
                    "Invalid check-in code. Please verify your code and try again."
                )
        
        return code


class CheckOutForm(forms.Form):
    """
    Student Check-Out Form
    With parent code verification.

    FIXED BUGS:
    1. Empty check_in_code on the parent caused silent validation failure —
       we now detect this and show a clear error message.
    2. Staff/Admin users do NOT need a parent code — they can check out
       any student directly (previously the form always demanded a code,
       blocking staff checkouts entirely).
    3. Added `performed_by_user` kwarg so the form knows who is acting,
       and skips code validation for staff/admin.
    """

    parent_check_in_code = forms.CharField(
        max_length=6,
        required=False,          # FIX: not always required — staff don't need it
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': 'Enter 6-digit code',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'autofocus': True,
            'style': 'letter-spacing: 0.5rem; font-size: 2rem; font-weight: bold;'
        }),
        help_text="Enter the parent's check-in code to authorize check-out"
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Check-out notes (optional)'
        }),
        label='Check-out Notes'
    )
    
    def __init__(self, student, *args, **kwargs):
        # FIX: accept the acting user so we can skip code check for staff/admin
        self.student = student
        self.performed_by_user = kwargs.pop('performed_by_user', None)
        super().__init__(*args, **kwargs)

        # If the acting user is staff or admin, make the code field optional
        # and update the placeholder to reflect that.
        user = self.performed_by_user
        if user and (user.is_staff_member or user.is_admin):
            self.fields['parent_check_in_code'].required = False
            self.fields['parent_check_in_code'].help_text = (
                "Staff/Admin: leave blank to check out without a code, "
                "or enter the parent's code to verify."
            )
        else:
            # For parents checking out their own child, code IS required
            self.fields['parent_check_in_code'].required = True
    
    def clean_parent_check_in_code(self):
        """Validate the check-in code"""
        code = self.cleaned_data.get('parent_check_in_code', '').strip()
        user = self.performed_by_user

        # Staff and Admin: if they left it blank, that's fine — no code needed
        if user and (user.is_staff_member or user.is_admin):
            return code  # blank or filled, either is accepted for staff

        # Parents: code is required
        if not code:
            raise forms.ValidationError("Please enter your check-in code.")

        if self.student and self.student.parent:
            parent = self.student.parent

            # FIX: if the parent never set a code, give a clear error instead
            # of silently comparing "" != code and failing every time.
            if not parent.check_in_code:
                raise forms.ValidationError(
                    f"This student's parent has not set a check-in code yet. "
                    f"Please ask them to set one from their profile, or have a "
                    f"staff member perform the check-out."
                )

            if parent.check_in_code != code:
                raise forms.ValidationError(
                    "Invalid check-in code. Please verify the code and try again."
                )

        return code


class ScheduleForm(forms.ModelForm):
    """
    Custom Schedule Form
    For creating flexible schedules
    """
    
    class Meta:
        model = Schedule
        fields = [
            'title', 'description', 'schedule_type', 
            'start_date', 'end_date', 'start_time', 'end_time',
            'recurrence_type', 'assigned_staff', 'assigned_students', 
            'assigned_room', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Morning Shift, Nap Time, Circle Time'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the schedule details...'
            }),
            'schedule_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'recurrence_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'assigned_staff': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '5'
            }),
            'assigned_students': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '5'
            }),
            'assigned_room': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        help_texts = {
            'end_date': 'Leave blank for one-time or ongoing schedules',
            'assigned_staff': 'Hold Ctrl (Cmd on Mac) to select multiple',
            'assigned_students': 'Hold Ctrl (Cmd on Mac) to select multiple',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_staff'].queryset = User.objects.filter(
            role__in=[User.Role.STAFF, User.Role.ADMIN],
            is_active=True
        ).order_by('first_name', 'last_name')
        
        self.fields['assigned_students'].queryset = Student.objects.filter(
            status='ACTIVE'
        ).order_by('first_name', 'last_name')
        
        self.fields['assigned_room'].queryset = Room.objects.filter(
            is_active=True
        ).order_by('name')
        
        self.fields['assigned_staff'].required = False
        self.fields['assigned_students'].required = False
        self.fields['assigned_room'].required = False
        self.fields['end_date'].required = False


class QuickCheckInForm(forms.Form):
    """
    Quick Check-In Form (for kiosk mode)
    """
    
    check_in_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '● ● ● ● ● ●',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'autofocus': True,
            'style': 'letter-spacing: 1rem; font-size: 3rem; font-weight: bold;'
        }),
        label='Enter Your Check-In Code'
    )


class StaffTimecardForm(forms.ModelForm):
    """
    Staff Timecard Form
    """
    
    class Meta:
        model = StaffTimecard
        fields = ['staff', 'assigned_room', 'notes']
        widgets = {
            'staff': forms.Select(attrs={
                'class': 'form-control'
            }),
            'assigned_room': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Shift notes (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['staff'].queryset = User.objects.filter(
            role=User.Role.STAFF,
            is_active=True
        ).order_by('first_name', 'last_name')
        
        self.fields['assigned_room'].queryset = Room.objects.filter(
            is_active=True
        ).order_by('name')
        
        self.fields['assigned_room'].required = False