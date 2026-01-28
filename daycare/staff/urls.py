from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('', views.staff_list, name='list'),
    path('schedules/', views.staff_schedule, name='schedules'),
    path('timecards/', views.timecard_list, name='timecards'),
]