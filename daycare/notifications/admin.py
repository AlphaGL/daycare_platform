from django.contrib import admin
from .models import Message, Announcement, MessageTemplate


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'is_flagged', 'created_at']
    search_fields = ['sender__username', 'recipient__username', 'subject', 'body']
    readonly_fields = ['sender', 'created_at', 'read_at']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'target_audience', 'is_published', 'publish_date']
    list_filter = ['priority', 'target_audience', 'is_published']
    search_fields = ['title', 'content']


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'is_active', 'created_by']
    list_filter = ['is_active']
    search_fields = ['name', 'subject']