from django.contrib import admin
from .models import StaffSchedule, Timecard, HealthCheck, StaffDocument


@admin.register(StaffSchedule)
class StaffScheduleAdmin(admin.ModelAdmin):
    list_display = ['staff', 'day_of_week', 'start_time', 'end_time', 'room', 'is_active']
    list_filter = ['day_of_week', 'is_active']
    search_fields = ['staff__username', 'room__name']


@admin.register(Timecard)
class TimecardAdmin(admin.ModelAdmin):
    list_display = ['staff', 'date', 'clock_in', 'clock_out', 'total_hours', 'is_approved']
    list_filter = ['is_approved', 'date']
    search_fields = ['staff__username']


@admin.register(HealthCheck)
class HealthCheckAdmin(admin.ModelAdmin):
    list_display = ['staff', 'check_date', 'cleared_for_work', 'has_fever', 'temperature']
    list_filter = ['cleared_for_work', 'check_date']
    search_fields = ['staff__username']


@admin.register(StaffDocument)
class StaffDocumentAdmin(admin.ModelAdmin):
    list_display = ['staff', 'document_type', 'title', 'issue_date', 'expiry_date', 'is_expired']
    list_filter = ['document_type']
    search_fields = ['staff__username', 'title']