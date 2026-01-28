from django.contrib import admin
from .models import Student, StudentRegistration, Attendance


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'parent', 'room', 'status', 'enrollment_date']
    list_filter = ['status', 'gender', 'room']
    search_fields = ['first_name', 'last_name', 'parent__username']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('first_name', 'last_name', 'middle_name', 'date_of_birth', 'gender', 'photo')
        }),
        ('Parent & Room', {
            'fields': ('parent', 'room')
        }),
        ('Medical Information', {
            'fields': ('allergies', 'medical_conditions', 'emergency_contact_name', 
                      'emergency_contact_phone', 'emergency_contact_relationship')
        }),
        ('Status', {
            'fields': ('status',)
        }),
    ]


@admin.register(StudentRegistration)
class StudentRegistrationAdmin(admin.ModelAdmin):
    list_display = ['registration_id', 'child_first_name', 'child_last_name', 'parent', 'status', 'created_at']
    list_filter = ['status', 'child_gender', 'registration_fee_paid']
    search_fields = ['child_first_name', 'child_last_name', 'parent__username']
    readonly_fields = ['registration_id', 'created_at', 'whatsapp_redirected']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'check_in_time', 'check_out_time']
    list_filter = ['status', 'date']
    search_fields = ['student__first_name', 'student__last_name']