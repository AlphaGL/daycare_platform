"""
Django Admin Configuration for Enhanced Student Models
Including Immunization Management
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Student, StudentRegistration, StudentContact, CustomField,
    IncidentReport, Immunization, VaccineDose, VaccineType,
    VaccineDoseSchedule, Attendance
)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'parent', 'room', 'age', 'status', 'enrollment_date']
    list_filter = ['status', 'gender', 'room', 'enrollment_date']
    search_fields = ['first_name', 'last_name', 'parent__username', 'parent__email']
    readonly_fields = ['student_id', 'created_at', 'updated_at', 'age_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('parent', 'first_name', 'last_name', 'middle_name', 
                      'date_of_birth', 'gender', 'photo', 'room')
        }),
        ('Demographics (Not visible to parents)', {
            'fields': ('race', 'ethnicity'),
            'classes': ('collapse',)
        }),
        ('Medical Information', {
            'fields': ('allergies', 'medical_conditions', 'medications',
                      'doctor_name', 'doctor_phone', 'doctor_address'),
            'classes': ('collapse',)
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone',
                      'emergency_contact_relationship'),
            'classes': ('collapse',)
        }),
        ('Address', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'state', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('Financial Details (Not visible to parents)', {
            'fields': ('parent_employer', 'family_income', 'has_subsidy', 'subsidy_details'),
            'classes': ('collapse',)
        }),
        ('School Details', {
            'fields': ('status', 'meal_type', 'custom_student_id'),
        }),
        ('Enrollment Details', {
            'fields': ('first_contact_date', 'toured_date', 'paperwork_date',
                      'desired_start_date', 'enrollment_date', 'set_active_on_enrollment',
                      'graduation_date', 'expected_birth_date', 'sibling_attending',
                      'programs', 'additional_details'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('student_id', 'created_at', 'updated_at', 'age_display'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudentContact)
class StudentContactAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'student', 'relationship', 'phone', 'can_pickup', 'is_emergency_contact']
    list_filter = ['can_pickup', 'is_emergency_contact', 'can_view_brightwheel', 'is_billing_contact']
    search_fields = ['full_name', 'student__first_name', 'student__last_name', 'phone', 'email']


@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    list_display = ['student', 'field_name', 'field_value']
    search_fields = ['student__first_name', 'student__last_name', 'field_name']


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ['student', 'report_number', 'report_date', 'reported_by', 'follow_up_required']
    list_filter = ['follow_up_required', 'report_date']
    search_fields = ['student__first_name', 'student__last_name', 'description']
    readonly_fields = ['created_at', 'updated_at']


# ========== IMMUNIZATION ADMIN ==========

@admin.register(VaccineType)
class VaccineTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'full_name', 'total_doses', 'is_active', 'display_order']
    list_filter = ['is_active']
    search_fields = ['name', 'full_name']
    ordering = ['display_order', 'name']


@admin.register(VaccineDoseSchedule)
class VaccineDoseScheduleAdmin(admin.ModelAdmin):
    list_display = ['vaccine_type', 'dose_number', 'cdc_recommendation_text', 
                   'recommended_age_months', 'is_catch_up']
    list_filter = ['vaccine_type', 'is_catch_up']
    ordering = ['vaccine_type__display_order', 'dose_number']


class VaccineDoseInline(admin.TabularInline):
    model = VaccineDose
    extra = 0
    readonly_fields = ['vaccine_type', 'dose_schedule', 'status_display', 'is_overdue']
    fields = ['vaccine_type', 'dose_schedule', 'date_administered', 'administered_by', 
             'location', 'status_display']
    
    def status_display(self, obj):
        if obj.is_administered:
            return format_html('<span style="color: green;">✓ Completed</span>')
        elif obj.is_overdue:
            return format_html('<span style="color: red;">⚠ Overdue</span>')
        else:
            return format_html('<span style="color: orange;">○ Pending</span>')
    status_display.short_description = 'Status'


@admin.register(Immunization)
class ImmunizationAdmin(admin.ModelAdmin):
    list_display = ['student', 'get_completion', 'is_exempt', 'on_catch_up_schedule', 'updated_at']
    list_filter = ['is_exempt', 'on_catch_up_schedule']
    search_fields = ['student__first_name', 'student__last_name']
    readonly_fields = ['created_at', 'updated_at', 'get_completion', 'get_overdue_count']
    inlines = [VaccineDoseInline]
    
    fieldsets = (
        ('Student', {
            'fields': ('student',)
        }),
        ('Exemption', {
            'fields': ('is_exempt', 'exemption_reason'),
        }),
        ('Catch-up Schedule', {
            'fields': ('on_catch_up_schedule', 'catch_up_notes'),
        }),
        ('Notes', {
            'fields': ('notes',),
        }),
        ('System Information', {
            'fields': ('last_updated_by', 'get_completion', 'get_overdue_count', 
                      'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_completion(self, obj):
        percentage = obj.get_completion_percentage()
        if percentage == 100:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} %</span>',
            color, percentage
        )
    get_completion.short_description = 'Completion'
    
    def get_overdue_count(self, obj):
        count = len(obj.get_overdue_vaccines())
        if count == 0:
            return format_html('<span style="color: green;">0 overdue</span>')
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} overdue</span>',
                count
            )
    get_overdue_count.short_description = 'Overdue Vaccines'


@admin.register(VaccineDose)
class VaccineDoseAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'vaccine_type', 'dose_number', 'date_administered', 
                   'status_display', 'is_overdue']
    list_filter = ['vaccine_type', 'date_administered']
    search_fields = ['immunization__student__first_name', 'immunization__student__last_name']
    readonly_fields = ['immunization', 'vaccine_type', 'dose_schedule', 
                      'status_display', 'is_overdue', 'recommended_date']
    
    fieldsets = (
        ('Vaccine Information', {
            'fields': ('immunization', 'vaccine_type', 'dose_schedule', 'recommended_date')
        }),
        ('Administration Details', {
            'fields': ('date_administered', 'administered_by', 'location', 'lot_number')
        }),
        ('Notes', {
            'fields': ('notes',),
        }),
        ('Status', {
            'fields': ('status_display', 'is_overdue', 'recorded_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_student(self, obj):
        return obj.immunization.student.get_full_name()
    get_student.short_description = 'Student'
    get_student.admin_order_field = 'immunization__student__last_name'
    
    def dose_number(self, obj):
        return obj.dose_schedule.dose_number
    dose_number.short_description = 'Dose #'
    
    def status_display(self, obj):
        status = obj.status_display
        if status == 'Completed':
            return format_html('<span style="color: green; font-weight: bold;">✓ {}</span>', status)
        elif status == 'Overdue':
            return format_html('<span style="color: red; font-weight: bold;">⚠ {}</span>', status)
        elif status == 'Due Soon':
            return format_html('<span style="color: orange; font-weight: bold;">○ {}</span>', status)
        else:
            return format_html('<span style="color: gray;">○ {}</span>', status)
    status_display.short_description = 'Status'


# ========== OTHER MODELS ==========

@admin.register(StudentRegistration)
class StudentRegistrationAdmin(admin.ModelAdmin):
    list_display = ['registration_id', 'parent', 'child_first_name', 'child_last_name',
                   'child_dob', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['parent__username', 'child_first_name', 'child_last_name']
    readonly_fields = ['registration_id', 'created_at', 'updated_at']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'check_in_time', 'check_out_time']
    list_filter = ['status', 'date']
    search_fields = ['student__first_name', 'student__last_name']
    date_hierarchy = 'date'