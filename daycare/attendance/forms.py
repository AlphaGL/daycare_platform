"""
Attendance and Schedule Forms
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
        
        # Filter students based on user role
        if self.user:
            if self.user.is_parent:
                # Parents see only their own children
                self.fields['student'].queryset = Student.objects.filter(
                    parent=self.user,
                    status='ACTIVE'
                ).order_by('first_name', 'last_name')
            else:
                # Staff/Admin see all active students
                self.fields['student'].queryset = Student.objects.filter(
                    status='ACTIVE'
                ).order_by('first_name', 'last_name')
        
        # Only show active rooms
        self.fields['room'].queryset = Room.objects.filter(is_active=True).order_by('name')
    
    def clean_parent_check_in_code(self):
        """Validate the check-in code"""
        code = self.cleaned_data.get('parent_check_in_code')
        
        # Verify the code matches the logged-in user's code (if parent)
        if self.user and self.user.is_parent:
            if self.user.check_in_code != code:
                raise forms.ValidationError("Invalid check-in code. Please verify your code and try again.")
        
        return code


class CheckOutForm(forms.Form):
    """
    Student Check-Out Form
    With parent code verification
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
        self.student = student
        super().__init__(*args, **kwargs)
    
    def clean_parent_check_in_code(self):
        """Validate the check-in code"""
        code = self.cleaned_data.get('parent_check_in_code')
        
        if code and self.student:
            # Verify the code matches the student's parent's code
            if self.student.parent.check_in_code != code:
                raise forms.ValidationError("Invalid check-in code. Please verify the code and try again.")
        
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
        # Filter querysets
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
        
        # Make fields optional based on schedule type
        self.fields['assigned_staff'].required = False
        self.fields['assigned_students'].required = False
        self.fields['assigned_room'].required = False
        self.fields['end_date'].required = False


class QuickCheckInForm(forms.Form):
    """
    Quick Check-In Form (for kiosk mode)
    Streamlined check-in process
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
    For staff clock-in/out
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