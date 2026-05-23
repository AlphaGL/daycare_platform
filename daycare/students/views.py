"""
Enhanced Student Views - FIXED
- Added email notification to admin when a student registration is submitted
- Added email to parent confirming their registration submission
- FIXED: Added admin views for listing, reviewing, approving, rejecting registrations
- All other logic preserved from original
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.utils import timezone
from datetime import date
import threading

from .models import  *

from .forms import  *

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
        immunization_record, created = Immunization.objects.get_or_create(student=student)
        if created:
            initialize_vaccine_doses(immunization_record)
        overdue_vaccines = immunization_record.get_overdue_vaccines()
        due_soon_vaccines = immunization_record.get_due_soon_vaccines()
        completion_percentage = immunization_record.get_completion_percentage()

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
            registration.status = StudentRegistration.Status.PENDING
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


# ========== ADMIN REGISTRATION REVIEW VIEWS ==========

@login_required
@user_passes_test(is_admin_or_staff)
def registration_list(request):
    """
    List all pending (and optionally all) student registrations.
    This is what the admin dashboard 'Pending Reviews' links to.
    """
    status_filter = request.GET.get('status', 'PENDING')

    registrations = StudentRegistration.objects.select_related(
        'parent', 'student', 'reviewed_by'
    ).order_by('-created_at')

    if status_filter and status_filter != 'ALL':
        registrations = registrations.filter(status=status_filter)

    # Counts for the filter tabs
    counts = {
        'PENDING': StudentRegistration.objects.filter(status='PENDING').count(),
        'APPROVED': StudentRegistration.objects.filter(status='APPROVED').count(),
        'REJECTED': StudentRegistration.objects.filter(status='REJECTED').count(),
        'PAYMENT_PENDING': StudentRegistration.objects.filter(status='PAYMENT_PENDING').count(),
    }

    context = {
        'registrations': registrations,
        'status_filter': status_filter,
        'counts': counts,
    }
    return render(request, 'students/registration_list.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def registration_detail(request, pk):
    """
    View a single registration request in full detail.
    Admins can approve or reject from here.
    """
    registration = get_object_or_404(
        StudentRegistration.objects.select_related('parent', 'student', 'reviewed_by'),
        pk=pk
    )
    context = {
        'registration': registration,
    }
    return render(request, 'students/registration_detail.html', context)


@login_required
@user_passes_test(is_admin)
def registration_approve(request, pk):
    """
    Approve a student registration and create the actual Student record.
    POST only — triggered by a button on the registration_detail page.
    """
    registration = get_object_or_404(StudentRegistration, pk=pk)

    if request.method != 'POST':
        return redirect('students:registration_detail', pk=pk)

    if registration.status == StudentRegistration.Status.APPROVED:
        messages.warning(request, "This registration has already been approved.")
        return redirect('students:registration_detail', pk=pk)

    # Create the Student object from registration data
    student = Student.objects.create(
        first_name=registration.child_first_name,
        last_name=registration.child_last_name,
        date_of_birth=registration.child_dob,
        gender=registration.child_gender,
        parent=registration.parent,
        status='ACTIVE',
    )

    # Initialize immunization record
    immunization = Immunization.objects.create(student=student)
    initialize_vaccine_doses(immunization)

    # Update the registration
    registration.status = StudentRegistration.Status.APPROVED
    registration.student = student
    registration.reviewed_by = request.user
    registration.reviewed_at = timezone.now()
    admin_notes = request.POST.get('admin_notes', '').strip()
    if admin_notes:
        registration.admin_notes = admin_notes
    registration.save()

    # Log activity
    try:
        UserActivity.objects.create(
            user=request.user,
            action_type=UserActivity.ActionType.UPDATE,
            description=f"Approved registration for {student.get_full_name()} "
                        f"(Registration ID: {registration.registration_id})"
        )
    except Exception:
        pass

    # Email parent with approval
    try:
        _send_async(_email_registration_approved, registration)
    except Exception:
        pass

    messages.success(
        request,
        f"✅ Registration approved! Student '{student.get_full_name()}' has been enrolled."
    )
    return redirect('students:registration_list')


@login_required
@user_passes_test(is_admin)
def registration_reject(request, pk):
    """
    Reject a student registration.
    POST only — triggered by a button on the registration_detail page.
    """
    registration = get_object_or_404(StudentRegistration, pk=pk)

    if request.method != 'POST':
        return redirect('students:registration_detail', pk=pk)

    if registration.status == StudentRegistration.Status.REJECTED:
        messages.warning(request, "This registration has already been rejected.")
        return redirect('students:registration_detail', pk=pk)

    registration.status = StudentRegistration.Status.REJECTED
    registration.reviewed_by = request.user
    registration.reviewed_at = timezone.now()
    admin_notes = request.POST.get('admin_notes', '').strip()
    if admin_notes:
        registration.admin_notes = admin_notes
    registration.save()

    # Log activity
    try:
        UserActivity.objects.create(
            user=request.user,
            action_type=UserActivity.ActionType.UPDATE,
            description=f"Rejected registration for {registration.child_first_name} "
                        f"{registration.child_last_name} "
                        f"(Registration ID: {registration.registration_id})"
        )
    except Exception:
        pass

    # Email parent with rejection
    try:
        _send_async(_email_registration_rejected, registration)
    except Exception:
        pass

    messages.success(request, "Registration has been rejected and the parent has been notified.")
    return redirect('students:registration_list')


# ========== EMAIL HELPERS ==========

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
        f"Review it here: {settings.SITE_URL}/students/registrations/\n\n"
        f"Regards,\n{settings.SITE_NAME} System"
    )
    send_notification_email(admin.email, subject, text_body)


def _email_registration_approved(registration):
    """Email the parent that their child's registration has been approved."""
    from notifications_service.email_service import send_notification_email
    from django.conf import settings

    parent = registration.parent
    subject = f"🎉 Registration Approved – {registration.child_first_name} {registration.child_last_name}"
    text_body = (
        f"Hi {parent.get_full_name()},\n\n"
        f"Great news! Your registration for "
        f"{registration.child_first_name} {registration.child_last_name} has been approved.\n\n"
        f"Registration ID: {registration.registration_id}\n\n"
        f"Your child is now enrolled. Please log in to the portal to view their profile "
        f"and complete any remaining steps.\n\n"
        f"Portal: {settings.SITE_URL}\n\n"
        f"Welcome to our daycare family! 🌟\n\n"
        f"Warm regards,\n{settings.SITE_NAME}"
    )
    send_notification_email(parent.email, subject, text_body)


def _email_registration_rejected(registration):
    """Email the parent that their child's registration has been rejected."""
    from notifications_service.email_service import send_notification_email
    from django.conf import settings

    parent = registration.parent
    subject = f"Registration Update – {registration.child_first_name} {registration.child_last_name}"
    text_body = (
        f"Hi {parent.get_full_name()},\n\n"
        f"We regret to inform you that the registration for "
        f"{registration.child_first_name} {registration.child_last_name} "
        f"could not be approved at this time.\n\n"
        f"Registration ID: {registration.registration_id}\n"
        + (f"Notes: {registration.admin_notes}\n\n" if registration.admin_notes else "\n")
        + f"Please contact us if you have any questions or would like to discuss next steps.\n\n"
        f"Regards,\n{settings.SITE_NAME}"
    )
    send_notification_email(parent.email, subject, text_body)


# ========== STUDENT CRUD (Admin/Staff) ==========

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
def immunization_list(request):
    """
    Dashboard-style list of every student's immunization status.
    Supports search by student name and filter by completion / overdue.
    URL: /students/immunizations/
    """
    students = Student.objects.filter(status='ACTIVE').select_related('parent', 'room').order_by('last_name', 'first_name')
 
    search = request.GET.get('search', '').strip()
    if search:
        students = students.filter(
            first_name__icontains=search
        ) | students.filter(
            last_name__icontains=search
        )
        students = students.distinct()
 
    filter_by = request.GET.get('filter', '')  # 'overdue' | 'incomplete' | ''
 
    rows = []
    for student in students:
        immunization, created = Immunization.objects.get_or_create(student=student)
        if created:
            initialize_vaccine_doses(immunization)
 
        overdue_count    = len(immunization.get_overdue_vaccines())
        completion       = immunization.get_completion_percentage()
        due_soon_count   = len(immunization.get_due_soon_vaccines())
 
        if filter_by == 'overdue' and overdue_count == 0:
            continue
        if filter_by == 'incomplete' and completion == 100:
            continue
 
        rows.append({
            'student':      student,
            'immunization': immunization,
            'completion':   completion,
            'overdue':      overdue_count,
            'due_soon':     due_soon_count,
        })
 
    context = {
        'rows':      rows,
        'search':    search,
        'filter_by': filter_by,
    }
    return render(request, 'students/immunization_list.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def immunization_detail(request, student_pk):
    """
    Full immunization record for a single student.
    Shows all vaccine types grouped, with per-dose status.
    URL: /students/<student_pk>/immunizations/
    """
    student = get_object_or_404(Student, pk=student_pk)
    immunization, created = Immunization.objects.get_or_create(student=student)
    if created:
        initialize_vaccine_doses(immunization)
    else:
        # Sync in case new VaccineTypes were added after initial creation
        initialize_vaccine_doses(immunization)
 
    vaccine_doses = immunization.vaccine_doses.select_related(
        'vaccine_type', 'dose_schedule'
    ).order_by('vaccine_type__display_order', 'vaccine_type__name', 'dose_schedule__dose_number')
 
    # Group doses by vaccine type
    vaccines_by_type = {}
    for dose in vaccine_doses:
        key = dose.vaccine_type.name
        if key not in vaccines_by_type:
            vaccines_by_type[key] = {'vaccine': dose.vaccine_type, 'doses': []}
        vaccines_by_type[key]['doses'].append(dose)
 
    context = {
        'student':          student,
        'immunization':     immunization,
        'vaccines_by_type': vaccines_by_type,
        'overdue_vaccines': immunization.get_overdue_vaccines(),
        'due_soon_vaccines':immunization.get_due_soon_vaccines(),
        'completion':       immunization.get_completion_percentage(),
        'add_form':         AddVaccineDoseForm(),   # quick-add panel
    }
    return render(request, 'students/immunization_detail.html', context)
 

@login_required
@user_passes_test(is_admin_or_staff)
def immunization_add_dose(request, student_pk):
    """
    Add a vaccine dose for a student.
    - If the vaccine type doesn't exist yet, create it on the fly.
    - If the dose_schedule slot doesn't exist, create it on the fly.
    - If the VaccineDose row already exists (pre-seeded), update it.
    - If it doesn't exist yet (custom type), create it.
    URL: /students/<student_pk>/immunizations/add-dose/
    """
    student      = get_object_or_404(Student, pk=student_pk)
    immunization, _ = Immunization.objects.get_or_create(student=student)
 
    if request.method == 'POST':
        form = AddVaccineDoseForm(request.POST)
        if form.is_valid():
            cd          = form.cleaned_data
            custom_name = (cd.get('vaccine_name_custom') or '').strip()
            dose_num    = cd['dose_number']
 
            with transaction.atomic():
                # 1. Resolve vaccine type
                if cd.get('vaccine_type'):
                    vaccine_type = cd['vaccine_type']
                else:
                    vaccine_type, _ = VaccineType.objects.get_or_create(
                        name=custom_name,
                        defaults={
                            'full_name':     custom_name,
                            'total_doses':   dose_num,
                            'is_active':     True,
                            'display_order': 999,
                        }
                    )
 
                # 2. Resolve dose schedule slot
                schedule, _ = VaccineDoseSchedule.objects.get_or_create(
                    vaccine_type=vaccine_type,
                    dose_number=dose_num,
                    defaults={
                        'cdc_recommendation_text': f'Dose {dose_num}',
                        'recommended_age_months':  0,
                    }
                )
 
                # 3. Get or create the VaccineDose row
                dose, created = VaccineDose.objects.get_or_create(
                    immunization=immunization,
                    vaccine_type=vaccine_type,
                    dose_schedule=schedule,
                )
 
                # 4. Fill in administration details
                dose.date_administered = cd['date_administered']
                dose.administered_by   = cd.get('administered_by', '')
                dose.location          = cd.get('location', '')
                dose.lot_number        = cd.get('lot_number', '')
                dose.notes             = cd.get('notes', '')
                dose.recorded_by       = request.user
                dose.save()
 
            action = 'recorded' if created else 'updated'
            messages.success(
                request,
                f"{vaccine_type.name} dose {dose_num} {action} for {student.get_full_name()}."
            )
            return redirect('students:immunization_detail', student_pk=student.pk)
    else:
        form = AddVaccineDoseForm()
 
    return render(request, 'students/immunization_add_dose.html', {
        'form':    form,
        'student': student,
    })
 

@login_required
@user_passes_test(is_admin_or_staff)
def immunization_settings(request, student_pk):
    """
    Edit exemption status, catch-up notes, general notes.
    URL: /students/<student_pk>/immunizations/settings/
    """
    student      = get_object_or_404(Student, pk=student_pk)
    immunization, _ = Immunization.objects.get_or_create(student=student)
 
    if request.method == 'POST':
        form = ImmunizationSettingsForm(request.POST, instance=immunization)
        if form.is_valid():
            obj                 = form.save(commit=False)
            obj.last_updated_by = request.user
            obj.save()
            messages.success(request, "Immunization settings updated.")
            return redirect('students:immunization_detail', student_pk=student.pk)
    else:
        form = ImmunizationSettingsForm(instance=immunization)
 
    return render(request, 'students/immunization_settings.html', {
        'form':        form,
        'student':     student,
        'immunization': immunization,
    })

@login_required
@user_passes_test(is_admin_or_staff)
def vaccine_dose_update(request, dose_pk):
    """
    Edit administration details of one dose.
    URL: /students/vaccine-dose/<dose_pk>/update/
    """
    dose    = get_object_or_404(VaccineDose, pk=dose_pk)
    student = dose.immunization.student
 
    if request.method == 'POST':
        form = VaccineDoseForm(request.POST, instance=dose)
        if form.is_valid():
            obj             = form.save(commit=False)
            obj.recorded_by = request.user
            obj.save()
            messages.success(request, f"{dose.vaccine_type.name} dose updated.")
            return redirect('students:immunization_detail', student_pk=student.pk)
    else:
        form = VaccineDoseForm(instance=dose)
 
    return render(request, 'students/vaccine_dose_form.html', {
        'form':    form,
        'dose':    dose,
        'student': student,
    })


@login_required
@user_passes_test(is_admin_or_staff)
def vaccine_dose_delete(request, dose_pk):
    """
    Clear the administration details from a dose (sets date_administered to None).
    For doses seeded from the standard schedule this keeps the row alive but marks
    it as un-administered. For custom (non-scheduled) doses, removes the row entirely.
    URL: /students/vaccine-dose/<dose_pk>/delete/
    """
    dose    = get_object_or_404(VaccineDose, pk=dose_pk)
    student = dose.immunization.student
 
    if request.method == 'POST':
        vaccine_name = dose.vaccine_type.name
        dose_num     = dose.dose_schedule.dose_number
 
        # If the schedule was auto-seeded from VaccineDoseSchedule, just clear it
        if VaccineDoseSchedule.objects.filter(pk=dose.dose_schedule.pk).exists():
            dose.date_administered = None
            dose.administered_by   = ''
            dose.location          = ''
            dose.lot_number        = ''
            dose.notes             = ''
            dose.recorded_by       = request.user
            dose.save()
            messages.warning(
                request,
                f"{vaccine_name} dose {dose_num} administration record cleared."
            )
        else:
            # Fully custom dose — delete the row
            dose.delete()
            messages.warning(
                request,
                f"{vaccine_name} dose {dose_num} deleted."
            )
        return redirect('students:immunization_detail', student_pk=student.pk)
 
    return render(request, 'students/vaccine_dose_confirm_delete.html', {
        'dose':    dose,
        'student': student,
    })

@login_required
@user_passes_test(is_admin_or_staff)
def vaccine_dose_bulk_update(request, student_pk):
    """
    Apply the same administration details to multiple selected dose rows.
    URL: /students/<student_pk>/immunizations/bulk-update/
    """
    student      = get_object_or_404(Student, pk=student_pk)
    immunization, _ = Immunization.objects.get_or_create(student=student)
 
    if request.method == 'POST':
        form     = BulkVaccineDoseUpdateForm(request.POST)
        dose_ids = request.POST.getlist('dose_ids')
 
        if form.is_valid() and dose_ids:
            cd     = form.cleaned_data
            doses  = VaccineDose.objects.filter(id__in=dose_ids, immunization=immunization)
            count  = 0
            for dose in doses:
                if cd.get('date_administered'):
                    dose.date_administered = cd['date_administered']
                if cd.get('administered_by'):
                    dose.administered_by = cd['administered_by']
                if cd.get('location'):
                    dose.location = cd['location']
                if cd.get('lot_number'):
                    dose.lot_number = cd['lot_number']
                if cd.get('notes'):
                    dose.notes = cd['notes']
                dose.recorded_by = request.user
                dose.save()
                count += 1
 
            messages.success(request, f"{count} dose(s) updated.")
            return redirect('students:immunization_detail', student_pk=student.pk)
        else:
            messages.error(request, "Please select at least one dose and fill the form.")
    else:
        form = BulkVaccineDoseUpdateForm()
 
    doses = immunization.vaccine_doses.select_related('vaccine_type', 'dose_schedule')
    return render(request, 'students/vaccine_bulk_update.html', {
        'form':    form,
        'student': student,
        'doses':   doses,
    })



@login_required
@user_passes_test(is_admin)
def vaccine_type_list(request):
    """
    List all VaccineTypes with edit / delete links.
    URL: /students/vaccine-types/
    """
    vaccine_types = VaccineType.objects.all().order_by('display_order', 'name')
    return render(request, 'students/vaccine_type_list.html', {
        'vaccine_types': vaccine_types,
    })



@login_required
@user_passes_test(is_admin)
def vaccine_type_create(request):
    """
    Create a new VaccineType.
    URL: /students/vaccine-types/create/
    """
    if request.method == 'POST':
        form = VaccineTypeForm(request.POST)
        if form.is_valid():
            vt = form.save()
            messages.success(request, f"Vaccine type '{vt.name}' created.")
            return redirect('students:vaccine_type_list')
    else:
        form = VaccineTypeForm()
 
    return render(request, 'students/vaccine_type_form.html', {
        'form':  form,
        'title': 'Add Vaccine Type',
    })


@login_required
@user_passes_test(is_admin)
def vaccine_type_update(request, pk):
    """
    Edit an existing VaccineType.
    URL: /students/vaccine-types/<pk>/update/
    """
    vt = get_object_or_404(VaccineType, pk=pk)
 
    if request.method == 'POST':
        form = VaccineTypeForm(request.POST, instance=vt)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{vt.name}' updated.")
            return redirect('students:vaccine_type_list')
    else:
        form = VaccineTypeForm(instance=vt)
 
    return render(request, 'students/vaccine_type_form.html', {
        'form':  form,
        'title': f'Edit — {vt.name}',
        'vt':    vt,
    })



@login_required
@user_passes_test(is_admin)
def vaccine_type_delete(request, pk):
    """
    Delete a VaccineType (and cascade its doses).
    URL: /students/vaccine-types/<pk>/delete/
    """
    vt = get_object_or_404(VaccineType, pk=pk)
 
    if request.method == 'POST':
        name = vt.name
        vt.delete()
        messages.warning(request, f"Vaccine type '{name}' deleted.")
        return redirect('students:vaccine_type_list')
 
    return render(request, 'students/vaccine_type_confirm_delete.html', {'vt': vt})

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