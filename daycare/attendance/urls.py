"""
URL patterns for Attendance app
"""
from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Check-In/Check-Out
    path('checkin/', views.student_checkin, name='checkin'),
    path('checkout/<int:pk>/', views.student_checkout, name='checkout'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/<int:pk>/', views.attendance_detail, name='attendance_detail'),
    
    # Schedules
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/create/', views.schedule_create, name='schedule_create'),
    path('schedules/<int:pk>/', views.schedule_detail, name='schedule_detail'),
    path('schedules/<int:pk>/update/', views.schedule_update, name='schedule_update'),
    path('schedules/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),
    
    # Staff Timecards
    path('timecards/', views.timecard_list, name='timecard_list'),
    path('timecards/clock-in/', views.staff_clock_in, name='staff_clock_in'),
    path('timecards/<int:pk>/clock-out/', views.staff_clock_out, name='staff_clock_out'),
]