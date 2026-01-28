from django.urls import path
from . import views

app_name = 'school'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.school_profile_view, name='profile'),
    path('settings/', views.school_settings_view, name='settings'),
    path('reminders/', views.reminder_list, name='reminder_list'),
    path('reminders/create/', views.reminder_create, name='reminder_create'),
]