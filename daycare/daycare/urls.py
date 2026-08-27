"""
Main URL Configuration for Sugamama sugababies Daycare
"""
import io
import traceback
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.shortcuts import redirect


def _server_error(request):
    """TEMPORARY: shows the real traceback to a logged-in superuser only;
    everyone else still gets a generic error page. Remove once debugging is done."""
    if getattr(request, 'user', None) and request.user.is_authenticated and request.user.is_superuser:
        return HttpResponseServerError(
            '<pre style="white-space:pre-wrap">' + traceback.format_exc() + '</pre>'
        )
    return HttpResponseServerError('Server Error (500)')


handler500 = _server_error


@staff_member_required
def _export_full_backup(request):
    """TEMPORARY: full-database export for migrating off this hosting account.
    Remove this view + URL once the data has been downloaded."""
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access required.")

    buffer = io.StringIO()
    call_command(
        'dumpdata',
        exclude=['contenttypes', 'auth.permission', 'sessions.session', 'admin.logentry'],
        indent=2,
        stdout=buffer,
    )
    response = HttpResponse(buffer.getvalue(), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="daycare_full_backup.json"'
    return response


# TEMPORARY — one-time fix to add Luna-Royale Hayes's remaining vaccine doses
# (the two vaccines that aren't on the standard CDC bulk-update grid, and that
# crashed the normal Add Dose form). Remove this view + URL once used.
_LUNA_STUDENT_PK = 16
_LUNA_DOSE_ENTRIES = [
    # (vaccine name, dose number, date administered)
    ('Rotavirus, Monovalent', 1, '2025-11-05'),
    ('Rotavirus, Monovalent', 2, '2026-01-21'),
    ('RSV Vac Nirsevimab (Beyfortus)', 1, '2025-10-09'),
]


@staff_member_required
def _fix_luna_immunizations(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access required.")

    import datetime
    from django.db import transaction
    from django.middleware.csrf import get_token
    from django.shortcuts import get_object_or_404
    from students.models import Student, Immunization, VaccineType, VaccineDoseSchedule, VaccineDose

    student = get_object_or_404(Student, pk=_LUNA_STUDENT_PK)

    if request.method != 'POST':
        rows = ''.join(f'<li>{name} — dose {n} — {d}</li>' for name, n, d in _LUNA_DOSE_ENTRIES)
        token = get_token(request)
        return HttpResponse(f'''
            <h3>Add remaining vaccine doses for {student.get_full_name()}?</h3>
            <ul>{rows}</ul>
            <form method="post">
                <input type="hidden" name="csrfmiddlewaretoken" value="{token}">
                <button type="submit">Confirm &amp; Add All</button>
            </form>
        ''')

    immunization, _ = Immunization.objects.get_or_create(student=student)
    results = []

    with transaction.atomic():
        for name, dose_num, date_str in _LUNA_DOSE_ENTRIES:
            vaccine_type, _ = VaccineType.objects.get_or_create(
                name=name,
                defaults={
                    'full_name': name,
                    'total_doses': dose_num,
                    'is_active': True,
                    'display_order': 999,
                },
            )
            schedule, _ = VaccineDoseSchedule.objects.get_or_create(
                vaccine_type=vaccine_type,
                dose_number=dose_num,
                defaults={
                    'cdc_recommendation_text': f'Dose {dose_num}',
                    'recommended_age_months': 0,
                },
            )
            dose, created = VaccineDose.objects.get_or_create(
                immunization=immunization,
                vaccine_type=vaccine_type,
                dose_schedule=schedule,
            )
            dose.date_administered = datetime.date.fromisoformat(date_str)
            dose.recorded_by = request.user
            dose.save()
            results.append(f"{name} dose {dose_num}: {'created' if created else 'updated'} ({date_str})")

    results_html = ''.join(f'<li>{r}</li>' for r in results)
    return HttpResponse(f'''
        <h3>Done!</h3>
        <ul>{results_html}</ul>
        <a href="/students/{student.pk}/immunizations/">Back to {student.get_full_name()}'s profile</a>
    ''')


urlpatterns = [
    # Admin
    path('custom-admin/', admin.site.urls),

    # TEMPORARY — remove after migrating the database, see comment above.
    path('export-full-backup-8271/', _export_full_backup, name='temp_export_full_backup'),
    path('fix-luna-immunizations-8271/', _fix_luna_immunizations, name='temp_fix_luna_immunizations'),

    # Core apps
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('school.urls')),
    path('students/', include('students.urls')),
    path('rooms/', include('rooms.urls')),
    path('staff/', include('staff.urls')),
    path('messages/', include('notifications.urls')),
    path('attendance/', include('attendance.urls')),
    path('time_tracker/', include('time_tracker.urls')),
]




# Customize admin site
admin.site.site_header = f"{settings.SITE_NAME} - Administration"
admin.site.site_title = f"{settings.SITE_NAME} Admin"
admin.site.index_title = "Dashboard"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)