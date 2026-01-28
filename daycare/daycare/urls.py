"""
Main URL Configuration for Daycare Management System
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Core apps
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('school.urls')),
    path('students/', include('students.urls')),
    path('rooms/', include('rooms.urls')),
    path('staff/', include('staff.urls')),
    path('messages/', include('notifications.urls')),
]

# Customize admin site
admin.site.site_header = f"{settings.SITE_NAME} - Administration"
admin.site.site_title = f"{settings.SITE_NAME} Admin"
admin.site.index_title = "Dashboard"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)