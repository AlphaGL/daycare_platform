from django import forms
from .models import Room, LessonPlan, DailyActivity


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'room_type', 'description', 'capacity', 
                  'min_age_months', 'max_age_months', 'assigned_staff']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'room_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'assigned_staff': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }


class LessonPlanForm(forms.ModelForm):
    class Meta:
        model = LessonPlan
        fields = ['room', 'week_start_date', 'week_end_date', 'theme', 'objectives']
        widgets = {
            'week_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'week_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'theme': forms.TextInput(attrs={'class': 'form-control'}),
            'objectives': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }