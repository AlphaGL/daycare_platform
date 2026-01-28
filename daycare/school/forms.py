from django import forms
from .models import SchoolProfile, SchoolSettings, Reminder


class SchoolProfileForm(forms.ModelForm):
    """Form for editing school profile"""
    
    class Meta:
        model = SchoolProfile
        fields = [
            'school_name', 'tagline', 'logo', 'phone', 'email', 'website',
            'address_line_1', 'address_line_2', 'city', 'state', 
            'postal_code', 'country', 'description', 'established_year'
        ]
        widgets = {
            'school_name': forms.TextInput(attrs={'class': 'form-control'}),
            'tagline': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'address_line_1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'established_year': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class SchoolSettingsForm(forms.ModelForm):
    """Form for editing school settings"""
    
    class Meta:
        model = SchoolSettings
        exclude = ['school', 'updated_by', 'updated_at']


class ReminderForm(forms.ModelForm):
    """Form for creating/editing reminders"""
    
    class Meta:
        model = Reminder
        fields = ['title', 'description', 'priority', 'remind_at', 'send_email']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'remind_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'send_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }