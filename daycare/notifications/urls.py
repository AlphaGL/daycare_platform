"""
URL patterns for notifications/messages app - FIXED & EXTENDED
Added: unread-count API, announcement create, reply (handled in detail view), mark-all-read
"""
from django.urls import path
from . import views

app_name = 'messages'

urlpatterns = [
    # Inbox & messaging
    path('inbox/', views.inbox, name='inbox'),
    path('<int:pk>/', views.message_detail, name='detail'),
    path('compose/', views.compose_message, name='compose'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),

    # Announcements
    path('announcements/', views.announcements, name='announcements'),
    path('announcements/create/', views.announcement_create, name='announcement_create'),

    # API endpoint used by base.html JavaScript
    path('unread-count/', views.unread_count, name='unread_count'),
]