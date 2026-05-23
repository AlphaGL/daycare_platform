"""
students/urls.py  —  FULL REPLACEMENT
Includes all original routes + complete immunization CRUD routes.
"""
from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [

    # ── Student CRUD ──────────────────────────────────────────────────────────
    path('',                        views.student_list,   name='list'),
    path('<int:pk>/',               views.student_detail, name='detail'),
    path('register/',               views.student_register, name='register'),
    path('create/',                 views.student_create,   name='create'),
    path('<int:pk>/update/',        views.student_update,   name='update'),
    path('<int:pk>/delete/',        views.student_delete,   name='delete'),

    # ── Registration review (admin/staff) ────────────────────────────────────
    path('registrations/',                          views.registration_list,    name='registration_list'),
    path('registrations/<int:pk>/',                 views.registration_detail,  name='registration_detail'),
    path('registrations/<int:pk>/approve/',         views.registration_approve, name='registration_approve'),
    path('registrations/<int:pk>/reject/',          views.registration_reject,  name='registration_reject'),

    # ── Contact management ────────────────────────────────────────────────────
    path('<int:student_pk>/contacts/add/',          views.contact_create,       name='contact_create'),
    path('contacts/<int:pk>/update/',               views.contact_update,       name='contact_update'),
    path('contacts/<int:pk>/delete/',               views.contact_delete,       name='contact_delete'),

    # ── Custom fields ─────────────────────────────────────────────────────────
    path('<int:student_pk>/custom-fields/add/',     views.custom_field_create,  name='custom_field_create'),

    # ── Incident reports ──────────────────────────────────────────────────────
    path('<int:student_pk>/incident-reports/add/',  views.incident_report_create, name='incident_report_create'),

    # ══ IMMUNIZATION CRUD (admin/staff) ══════════════════════════════════════

    # Overview list — all students' statuses
    path(
        'immunizations/',
        views.immunization_list,
        name='immunization_list',
    ),

    # Single student — full detail + quick-add panel
    path(
        '<int:student_pk>/immunizations/',
        views.immunization_detail,
        name='immunization_detail',
    ),

    # Add any dose (known or brand-new vaccine type)
    path(
        '<int:student_pk>/immunizations/add-dose/',
        views.immunization_add_dose,
        name='immunization_add_dose',
    ),

    # Exemption / catch-up settings
    path(
        '<int:student_pk>/immunizations/settings/',
        views.immunization_settings,
        name='immunization_settings',
    ),

    # Bulk-update selected doses
    path(
        '<int:student_pk>/immunizations/bulk-update/',
        views.vaccine_dose_bulk_update,
        name='vaccine_bulk_update',
    ),

    # Edit a single dose
    path(
        'vaccine-dose/<int:dose_pk>/update/',
        views.vaccine_dose_update,
        name='vaccine_dose_update',
    ),

    # Delete / clear a single dose
    path(
        'vaccine-dose/<int:dose_pk>/delete/',
        views.vaccine_dose_delete,
        name='vaccine_dose_delete',
    ),

    # ── Vaccine type catalogue (admin only) ───────────────────────────────────
    path('vaccine-types/',                      views.vaccine_type_list,   name='vaccine_type_list'),
    path('vaccine-types/create/',               views.vaccine_type_create, name='vaccine_type_create'),
    path('vaccine-types/<int:pk>/update/',      views.vaccine_type_update, name='vaccine_type_update'),
    path('vaccine-types/<int:pk>/delete/',      views.vaccine_type_delete, name='vaccine_type_delete'),

    # ── Attendance ────────────────────────────────────────────────────────────
    path('mark-absent/', views.mark_absent, name='mark_absent'),
]