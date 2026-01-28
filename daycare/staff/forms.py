from django import forms
from .models import StaffSchedule, Timecard, HealthCheck


class StaffScheduleForm(forms.ModelForm):
    class Meta:
        model = StaffSchedule
        fields = ['staff', 'day_of_week', 'start_time', 'end_time', 'room', 'notes']
        widgets = {
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }


class TimecardForm(forms.ModelForm):
    class Meta:
        model = Timecard
        fields = ['staff', 'date', 'clock_in', 'clock_out', 'break_start', 'break_end', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'clock_in': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'clock_out': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }