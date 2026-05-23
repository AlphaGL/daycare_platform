"""
time_tracker/admin.py
"""
from django.contrib import admin
from .models import TimeSession, DailySummary


@admin.register(TimeSession)
class TimeSessionAdmin(admin.ModelAdmin):
    list_display  = ['display_name', 'session_type', 'date', 'clock_in', 'clock_out',
                     'elapsed_display', 'status']
    list_filter   = ['session_type', 'status', 'date']
    search_fields = ['student_checkin__student__first_name',
                     'student_checkin__student__last_name',
                     'staff__first_name', 'staff__last_name',
                     'parent__first_name', 'parent__last_name']
    readonly_fields = ['elapsed_seconds', 'elapsed_display', 'duration_hours',
                       'created_at', 'updated_at']
    date_hierarchy  = 'date'

    actions = ['force_close_selected']

    def force_close_selected(self, request, queryset):
        closed = 0
        for session in queryset.filter(status=TimeSession.Status.ACTIVE):
            session.close(notes='Bulk closed by admin.')
            closed += 1
        self.message_user(request, f"{closed} session(s) closed.")
    force_close_selected.short_description = 'Force-close selected active sessions'


@admin.register(DailySummary)
class DailySummaryAdmin(admin.ModelAdmin):
    list_display = ['date', 'person_type', 'user', 'student',
                    'total_sessions', 'total_hours', 'first_arrival', 'last_departure']
    list_filter  = ['person_type', 'date']
    date_hierarchy = 'date'
