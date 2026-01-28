from django.contrib import admin
from .models import Room, LessonPlan, DailyActivity, RoomDeviceMode


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'room_type', 'capacity', 'current_enrollment', 'is_active']
    list_filter = ['room_type', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['assigned_staff']


@admin.register(LessonPlan)
class LessonPlanAdmin(admin.ModelAdmin):
    list_display = ['room', 'week_start_date', 'week_end_date', 'theme']
    list_filter = ['room', 'week_start_date']
    search_fields = ['theme', 'room__name']


@admin.register(DailyActivity)
class DailyActivityAdmin(admin.ModelAdmin):
    list_display = ['lesson_plan', 'date', 'morning_activity']
    list_filter = ['date', 'lesson_plan__room']


@admin.register(RoomDeviceMode)
class RoomDeviceModeAdmin(admin.ModelAdmin):
    list_display = ['room', 'is_kiosk_mode', 'allow_checkin', 'last_used']
    list_filter = ['is_kiosk_mode']