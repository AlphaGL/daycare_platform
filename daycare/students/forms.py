from django import forms
from .models import Student, StudentRegistration, Attendance


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'middle_name', 'date_of_birth', 
                  'gender', 'photo', 'room', 'allergies', 'medical_conditions',
                  'emergency_contact_name', 'emergency_contact_phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = StudentRegistration
        fields = ['child_first_name', 'child_last_name', 'child_middle_name',
                  'child_dob', 'child_gender', 'medical_info', 'special_needs']
        widgets = {
            'child_first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'child_last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'child_dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'child_gender': forms.Select(attrs={'class': 'form-control'}),
            'medical_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'status', 'check_in_time', 'check_out_time', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'check_in_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'check_out_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }