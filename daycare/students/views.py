"""
Enhanced Student Views - FIXED
- Added email notification to admin when a student registration is submitted
- Added email to parent confirming their registration submission
- All other logic preserved from original
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.utils import timezone
from datetime import date
import threading

from .models import (
    Student, StudentRegistration, StudentContact, CustomField,
    IncidentReport, Immunization, VaccineDose, VaccineType,
    VaccineDoseSchedule, Attendance
)
from .forms import (
    StudentForm, StudentRegistrationForm, AttendanceForm,
    StudentContactForm, CustomFieldForm, IncidentReportForm,
    ImmunizationForm, VaccineDoseForm, BulkVaccineDoseUpdateForm,
    MarkAbsentForm
)
from accounts.models import UserActivity


def _send_async(fn, *args):
    threading.Thread(target=fn, args=args, daemon=True).start()


def is_admin_or_staff(user):
    return user.is_authenticated and (user.is_admin or user.is_staff_member)


def is_admin(user):
    return user.is_authenticated and user.is_admin


# ========== STUDENT VIEWS ==========

@login_required
def student_list(request):
    """List all students"""
    if request.user.is_parent:
        students = request.user.children.filter(status='ACTIVE')
    else:
        students = Student.objects.filter(status='ACTIVE').select_related(
            'parent', 'room'
        ).order_by('last_name', 'first_name')

    context = {
        'students': students,
        'total_students': students.count()
    }
    return render(request, 'students/student_list.html', context)


@login_required
def student_detail(request, pk):
    """Enhanced student details with immunizations"""
    student = get_object_or_404(Student, pk=pk)

    if request.user.is_parent and student.parent != request.user:
        messages.error(request, "You don't have permission to view this student.")
        return redirect('students:list')

    contacts = student.contacts.all().order_by('-can_pickup', 'full_name')
    custom_fields = student.custom_fields.all()
    incident_reports = student.incident_reports.all().order_by('-report_date')

    show_immunizations = request.user.is_admin or request.user.is_staff_member
    immunization_record = None
    overdue_vaccines = []
    due_soon_vaccines = []
    completion_percentage = 0

    if show_immunizations:
        try:
            immunization_record = student.immunization_record
            overdue_vaccines = immunization_record.get_overdue_vaccines()
            due_soon_vaccines = immunization_record.get_due_soon_vaccines()
            completion_percentage = immunization_record.get_completion_percentage()
        except Immunization.DoesNotExist:
            immunization_record = Immunization.objects.create(student=student)
            initialize_vaccine_doses(immunization_record)

    recent_attendance = student.attendance_records.all()[:10]

    context = {
        'student': student,
        'contacts': contacts,
        'custom_fields': custom_fields,
        'incident_reports': incident_reports,
        'show_immunizations': show_immunizations,
        'immunization_record': immunization_record,
        'overdue_vaccines': overdue_vaccines,
        'due_soon_vaccines': due_soon_vaccines,
        'completion_percentage': completion_percentage,
        'recent_attendance': recent_attendance,
    }
    return render(request, 'students/student_detail.html', context)


@login_required
def student_register(request):
    """Register new student - with email notifications to parent + admins"""
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.parent = request.user
            registration.save()

            # ── EMAIL: confirm registration to parent ──────────────────────
            try:
                _send_async(_email_registration_submitted_parent, registration)
            except Exception:
                pass

            # ── EMAIL: notify all admins of new registration ───────────────
            try:
                from accounts.models import User
                admins = User.objects.filter(role=User.Role.ADMIN, is_active=True)
                for admin in admins:
                    _send_async(_email_registration_submitted_admin, admin, registration)
            except Exception:
                pass

            whatsapp_url = registration.get_whatsapp_url()
            messages.success(
                request,
                "Registration submitted! A confirmation email has been sent. "
                "Please complete payment via WhatsApp."
            )
            return redirect(whatsapp_url)
    else:
        form = StudentRegistrationForm()

    return render(request, 'students/register.html', {'form': form})


def _email_registration_submitted_parent(registration):
    """Email the parent confirming their child's registration was received."""
    from notifications_service.email_service import send_notification_email
    from django.conf import settings

    parent = registration.parent
    subject = f"Registration Received – {registration.child_first_name} {registration.child_last_name}"
    text_body = (
        f"Hi {parent.get_full_name()},\n\n"
        f"We've received your registration request for "
        f"{registration.child_first_name} {registration.child_last_name}.\n\n"
        f"Registration ID: {registration.registration_id}\n"
        f"Status: Pending Review\n\n"
        f"Our team will review your submission and get back to you shortly. "
        f"Please complete the registration fee payment via WhatsApp to finalize enrollment.\n\n"
        f"If you have any questions, don't hesitate to contact us.\n\n"
        f"Warm regards,\n{settings.SITE_NAME}"
    )
    send_notification_email(parent.email, subject, text_body)


def _email_registration_submitted_admin(admin, registration):
    """Email admin about a new student registration."""
    from notifications_service.email_service import send_notification_email
    from django.conf import settings

    subject = (
        f"New Student Registration – "
        f"{registration.child_first_name} {registration.child_last_name}"
    )
    text_body = (
        f"Hi {admin.get_full_name()},\n\n"
        f"A new student registration has been submitted.\n\n"
        f"Child: {registration.child_first_name} {registration.child_last_name}\n"
        f"Date of Birth: {registration.child_dob}\n"
        f"Gender: {registration.child_gender}\n"
        f"Parent: {registration.parent.get_full_name()} ({registration.parent.email})\n"
        f"Registration ID: {registration.registration_id}\n"
        f"Submitted: {registration.created_at.strftime('%d %b %Y, %I:%M %p')}\n\n"
        f"Review in admin panel: {settings.SITE_URL}/custom-admin/students/studentregistration/\n\n"
        f"Regards,\n{settings.SITE_NAME} System"
    )
    send_notification_email(admin.email, subject, text_body)


@login_required
@user_passes_test(is_admin_or_staff)
def student_create(request):
    """Create student (admin/staff)"""
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()

            immunization = Immunization.objects.create(student=student)
            initialize_vaccine_doses(immunization)

            try:
                UserActivity.objects.create(
                    user=request.user,
                    action_type=UserActivity.ActionType.CREATE,
                    description=f"Created student: {student.get_full_name()}"
                )
            except Exception:
                pass

            messages.success(request, "Student created successfully!")
            return redirect('students:detail', pk=student.pk)
    else:
        form = StudentForm()

    return render(request, 'students/student_form.html', {'form': form})


@login_required
@user_passes_test(is_admin_or_staff)
def student_update(request, pk):
    """Update student"""
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()

            try:
                UserActivity.objects.create(
                    user=request.user,
                    action_type=UserActivity.ActionType.UPDATE,
                    description=f"Updated student: {student.get_full_name()}"
                )
            except Exception:
                pass

            messages.success(request, "Student updated!")
            return redirect('students:detail', pk=student.pk)
    else:
        form = StudentForm(instance=student)

    return render(request, 'students/student_form.html', {'form': form, 'student': student})


@login_required
@user_passes_test(is_admin)
def student_delete(request, pk):
    """Delete student"""
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        student_name = student.get_full_name()
        student.delete()
        messages.success(request, f"Student '{student_name}' deleted successfully!")
        return redirect('students:list')

    return render(request, 'students/student_confirm_delete.html', {'student': student})


# ========== CONTACT MANAGEMENT ==========

@login_required
@user_passes_test(is_admin_or_staff)
def contact_create(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)

    if request.method == 'POST':
        form = StudentContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.student = student
            contact.save()

            if contact.can_view_brightwheel and not contact.access_code:
                contact.generate_access_code()

            messages.success(request, f"Contact '{contact.full_name}' added successfully!")
            return redirect('students:detail', pk=student.pk)
    else:
        form = StudentContactForm()

    return render(request, 'students/contact_form.html', {'form': form, 'student': student})


@login_required
@user_passes_test(is_admin_or_staff)
def contact_update(request, pk):
    contact = get_object_or_404(StudentContact, pk=pk)

    if request.method == 'POST':
        form = StudentContactForm(request.POST, instance=contact)
        if form.is_valid():
            contact = form.save()
            if contact.can_view_brightwheel and not contact.access_code:
                contact.generate_access_code()
            messages.success(request, "Contact updated!")
            return redirect('students:detail', pk=contact.student.pk)
    else:
        form = StudentContactForm(instance=contact)

    return render(request, 'students/contact_form.html', {
        'form': form, 'contact': contact, 'student': contact.student
    })


@login_required
@user_passes_test(is_admin_or_staff)
def contact_delete(request, pk):
    contact = get_object_or_404(StudentContact, pk=pk)
    student = contact.student

    if request.method == 'POST':
        contact.delete()
        messages.success(request, "Contact deleted!")
        return redirect('students:detail', pk=student.pk)

    return render(request, 'students/contact_confirm_delete.html', {
        'contact': contact, 'student': student
    })


# ========== CUSTOM FIELDS ==========

@login_required
@user_passes_test(is_admin_or_staff)
def custom_field_create(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)

    if request.method == 'POST':
        form = CustomFieldForm(request.POST)
        if form.is_valid():
            field = form.save(commit=False)
            field.student = student
            field.save()
            messages.success(request, "Custom field added!")
            return redirect('students:detail', pk=student.pk)
    else:
        form = CustomFieldForm()

    return render(request, 'students/custom_field_form.html', {'form': form, 'student': student})


# ========== INCIDENT REPORTS ==========

@login_required
@user_passes_test(is_admin_or_staff)
def incident_report_create(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)

    if request.method == 'POST':
        form = IncidentReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.student = student
            report.reported_by = request.user
            report.save()

            # ── EMAIL: notify parent of incident report ────────────────────
            try:
                _send_async(_email_incident_report, report)
            except Exception:
                pass

            messages.success(request, f"Incident Report #{report.report_number} created!")
            return redirect('students:detail', pk=student.pk)
    else:
        last_report = student.incident_reports.order_by('-report_number').first()
        next_number = (last_report.report_number + 1) if last_report else 1
        form = IncidentReportForm(initial={'report_number': next_number})

    return render(request, 'students/incident_report_form.html', {'form': form, 'student': student})


def _email_incident_report(report):
    """Notify the student's parent of an incident report."""
    from notifications_service.email_service import send_notification_email
    from django.conf import settings

    parent = report.student.parent
    subject = (
        f"⚠️ Incident Report #{report.report_number} – "
        f"{report.student.get_full_name()}"
    )
    text_body = (
        f"Hi {parent.get_full_name()},\n\n"
        f"An incident report has been filed for your child, "
        f"{report.student.get_full_name()}.\n\n"
        f"Report #: {report.report_number}\n"
        f"Date: {report.report_date}\n"
        f"Reported by: {report.reported_by.get_full_name() if report.reported_by else 'Staff'}\n\n"
        f"Details:\n{report.description}\n\n"
        f"{'Follow-up required: ' + report.follow_up_notes if report.follow_up_required and report.follow_up_notes else ''}\n\n"
        f"Please log in for more details or contact us if you have questions.\n\n"
        f"Regards,\n{settings.SITE_NAME}"
    )
    send_notification_email(parent.email, subject, text_body)


# ========== IMMUNIZATION VIEWS ==========

@login_required
@user_passes_test(is_admin_or_staff)
def immunization_detail(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    immunization, created = Immunization.objects.get_or_create(student=student)

    if created:
        initialize_vaccine_doses(immunization)

    vaccine_doses = immunization.vaccine_doses.select_related(
        'vaccine_type', 'dose_schedule'
    ).order_by('vaccine_type__display_order', 'dose_schedule__dose_number')

    vaccines_by_type = {}
    for dose in vaccine_doses:
        vaccine_name = dose.vaccine_type.name
        if vaccine_name not in vaccines_by_type:
            vaccines_by_type[vaccine_name] = {'vaccine': dose.vaccine_type, 'doses': []}
        vaccines_by_type[vaccine_name]['doses'].append(dose)

    overdue = immunization.get_overdue_vaccines()
    due_soon = immunization.get_due_soon_vaccines()
    completion = immunization.get_completion_percentage()

    context = {
        'student': student,
        'immunization': immunization,
        'vaccines_by_type': vaccines_by_type,
        'overdue_vaccines': overdue,
        'due_soon_vaccines': due_soon,
        'completion_percentage': completion,
    }
    return render(request, 'students/immunization_detail.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def immunization_settings(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    immunization, _ = Immunization.objects.get_or_create(student=student)

    if request.method == 'POST':
        form = ImmunizationForm(request.POST, instance=immunization)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.last_updated_by = request.user
            obj.save()
            messages.success(request, "Immunization settings updated!")
            return redirect('students:immunization_detail', student_pk=student.pk)
    else:
        form = ImmunizationForm(instance=immunization)

    return render(request, 'students/immunization_settings.html', {
        'form': form, 'student': student, 'immunization': immunization
    })


@login_required
@user_passes_test(is_admin_or_staff)
def vaccine_dose_update(request, dose_pk):
    dose = get_object_or_404(VaccineDose, pk=dose_pk)

    if request.method == 'POST':
        form = VaccineDoseForm(request.POST, instance=dose)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.recorded_by = request.user
            obj.save()
            messages.success(request, f"{dose.vaccine_type.name} dose updated!")
            return redirect('students:immunization_detail', student_pk=dose.immunization.student.pk)
    else:
        form = VaccineDoseForm(instance=dose)

    return render(request, 'students/vaccine_dose_form.html', {
        'form': form, 'dose': dose, 'student': dose.immunization.student
    })


@login_required
@user_passes_test(is_admin_or_staff)
def vaccine_dose_bulk_update(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    immunization = student.immunization_record

    if request.method == 'POST':
        form = BulkVaccineDoseUpdateForm(request.POST)
        dose_ids = request.POST.getlist('dose_ids')

        if form.is_valid() and dose_ids:
            date_administered = form.cleaned_data.get('date_administered')
            administered_by = form.cleaned_data.get('administered_by')
            location = form.cleaned_data.get('location')

            doses = VaccineDose.objects.filter(id__in=dose_ids, immunization=immunization)
            for dose in doses:
                if date_administered:
                    dose.date_administered = date_administered
                if administered_by:
                    dose.administered_by = administered_by
                if location:
                    dose.location = location
                dose.recorded_by = request.user
                dose.save()

            messages.success(request, f"{len(dose_ids)} vaccine doses updated!")
            return redirect('students:immunization_detail', student_pk=student.pk)
    else:
        form = BulkVaccineDoseUpdateForm()

    doses = immunization.vaccine_doses.select_related('vaccine_type', 'dose_schedule')
    return render(request, 'students/vaccine_bulk_update.html', {
        'form': form, 'student': student, 'doses': doses
    })


# ========== ATTENDANCE VIEWS ==========

@login_required
@user_passes_test(is_admin_or_staff)
def mark_absent(request):
    """Mark students as absent"""
    if request.method == 'POST':
        form = MarkAbsentForm(request.POST)
        if form.is_valid():
            students = form.cleaned_data['students']
            absence_date = form.cleaned_data['date']
            reason = form.cleaned_data['reason']
            notes = form.cleaned_data.get('notes', '')

            count = 0
            for student in students:
                attendance, created = Attendance.objects.get_or_create(
                    student=student,
                    date=absence_date,
                    defaults={
                        'status': reason,
                        'notes': notes,
                        'checked_in_by': request.user,
                    }
                )
                if not created:
                    attendance.status = reason
                    attendance.notes = notes
                    attendance.save()
                count += 1

            try:
                UserActivity.objects.create(
                    user=request.user,
                    action_type=UserActivity.ActionType.UPDATE,
                    description=f"Marked {count} student(s) as {reason.lower()} for {absence_date}"
                )
            except Exception:
                pass

            messages.success(request, f"{count} student(s) marked as absent!")
            return redirect('attendance:attendance_list')
    else:
        form = MarkAbsentForm(initial={'date': date.today()})

    return render(request, 'students/mark_absent.html', {'form': form})


# ========== HELPER FUNCTIONS ==========

def initialize_vaccine_doses(immunization):
    """Initialize vaccine doses for a student based on CDC schedule"""
    vaccine_types = VaccineType.objects.filter(is_active=True).prefetch_related('dose_schedules')

    for vaccine_type in vaccine_types:
        for schedule in vaccine_type.dose_schedules.all():
            VaccineDose.objects.get_or_create(
                immunization=immunization,
                vaccine_type=vaccine_type,
                dose_schedule=schedule
            )