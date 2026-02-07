"""
Enhanced URL Patterns for Students App
Including Immunization Routes
"""
from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Student CRUD
    path('', views.student_list, name='list'),
    path('<int:pk>/', views.student_detail, name='detail'),
    path('register/', views.student_register, name='register'),
    path('create/', views.student_create, name='create'),
    path('<int:pk>/update/', views.student_update, name='update'),
    path('<int:pk>/delete/', views.student_delete, name='delete'),
    
    # Contact Management
    path('<int:student_pk>/contacts/add/', views.contact_create, name='contact_create'),
    path('contacts/<int:pk>/update/', views.contact_update, name='contact_update'),
    path('contacts/<int:pk>/delete/', views.contact_delete, name='contact_delete'),
    
    # Custom Fields
    path('<int:student_pk>/custom-fields/add/', views.custom_field_create, name='custom_field_create'),
    
    # Incident Reports
    path('<int:student_pk>/incident-reports/add/', views.incident_report_create, name='incident_report_create'),
    
    # Immunizations (Admin/Staff Only)
    path('<int:student_pk>/immunizations/', views.immunization_detail, name='immunization_detail'),
    path('<int:student_pk>/immunizations/settings/', views.immunization_settings, name='immunization_settings'),
    path('vaccine-dose/<int:dose_pk>/update/', views.vaccine_dose_update, name='vaccine_dose_update'),
    path('<int:student_pk>/immunizations/bulk-update/', views.vaccine_dose_bulk_update, name='vaccine_bulk_update'),
    
    # Attendance
    path('mark-absent/', views.mark_absent, name='mark_absent'),
]