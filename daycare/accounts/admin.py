"""
Admin interface for User Management
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserActivity, ParentProfile, StaffProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin with role display"""
    
    list_display = ['username', 'email', 'role', 'is_active_user', 'last_activity', 'created_at']
    list_filter = ['role', 'is_active_user', 'is_staff', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Access', {
            'fields': ('role', 'check_in_code', 'is_active_user')
        }),
        ('Profile', {
            'fields': ('phone', 'profile_photo')
        }),
        ('Activity', {
            'fields': ('last_activity', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['last_activity', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('parent_profile', 'staff_profile')


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Track all user activities"""
    
    list_display = ['user', 'action_type', 'description', 'ip_address', 'timestamp']
    list_filter = ['action_type', 'timestamp']
    search_fields = ['user__username', 'user__email', 'description']
    readonly_fields = ['user', 'action_type', 'description', 'ip_address', 'user_agent', 'timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    """Parent profile management"""
    
    list_display = ['user', 'relationship_to_child', 'emergency_contact', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    list_filter = ['can_edit_student_info', 'can_add_activities', 'receive_email_notifications']
    
    fieldsets = [
        ('User', {
            'fields': ('user',)
        }),
        ('Contact Information', {
            'fields': ('address', 'emergency_contact', 'relationship_to_child')
        }),
        ('Permissions', {
            'fields': ('can_edit_student_info', 'can_add_activities')
        }),
        ('Notifications', {
            'fields': ('receive_email_notifications', 'receive_sms_notifications')
        }),
    ]
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    """Staff profile management"""
    
    list_display = ['user', 'position', 'employee_id', 'hire_date', 'is_active_staff']
    search_fields = ['user__username', 'user__email', 'position', 'employee_id']
    list_filter = ['position', 'access_level', 'is_active_staff', 'hire_date']
    
    fieldsets = [
        ('User', {
            'fields': ('user',)
        }),
        ('Professional Information', {
            'fields': ('position', 'employee_id', 'hire_date', 'access_level')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Status', {
            'fields': ('is_active_staff',)
        }),
    ]
    
    readonly_fields = ['created_at', 'updated_at']