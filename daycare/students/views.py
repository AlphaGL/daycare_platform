"""
Enhanced Student Views
Including Immunization Management and Mark Absent
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.utils import timezone
from datetime import date

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
    
    # Check permission
    if request.user.is_parent and student.parent != request.user:
        messages.error(request, "You don't have permission to view this student.")
        return redirect('students:list')
    
    # Get related data
    contacts = student.contacts.all().order_by('-can_pickup', 'full_name')
    custom_fields = student.custom_fields.all()
    incident_reports = student.incident_reports.all().order_by('-report_date')
    
    # Immunization data (NOT visible to parents)
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
            # Create immunization record if it doesn't exist
            immunization_record = Immunization.objects.create(student=student)
            # Initialize vaccine doses based on CDC schedule
            initialize_vaccine_doses(immunization_record)
    
    # Recent attendance
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
    """Register new student"""
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.parent = request.user
            registration.save()
            
            # Redirect to WhatsApp
            whatsapp_url = registration.get_whatsapp_url()
            messages.success(request, "Registration submitted! Please complete payment via WhatsApp.")
            return redirect(whatsapp_url)
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'students/register.html', {'form': form})


@login_required
@user_passes_test(is_admin_or_staff)
def student_create(request):
    """Create student (admin/staff)"""
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            
            # Create immunization record
            immunization = Immunization.objects.create(student=student)
            initialize_vaccine_doses(immunization)
            
            # Log activity
            try:
                UserActivity.objects.create(
                    user=request.user,
                    action_type=UserActivity.ActionType.CREATE,
                    description=f"Created student: {student.get_full_name()}"
                )
            except:
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
            
            # Log activity
            try:
                UserActivity.objects.create(
                    user=request.user,
                    action_type=UserActivity.ActionType.UPDATE,
                    description=f"Updated student: {student.get_full_name()}"
                )
            except:
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
    
    context = {'student': student}
    return render(request, 'students/student_confirm_delete.html', context)


# ========== CONTACT MANAGEMENT ==========

@login_required
@user_passes_test(is_admin_or_staff)
def contact_create(request, student_pk):
    """Add contact to student"""
    student = get_object_or_404(Student, pk=student_pk)
    
    if request.method == 'POST':
        form = StudentContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.student = student
            contact.save()
            
            # Generate access code if needed
            if contact.can_view_brightwheel and not contact.access_code:
                contact.generate_access_code()
            
            messages.success(request, f"Contact '{contact.full_name}' added successfully!")
            return redirect('students:detail', pk=student.pk)
    else:
        form = StudentContactForm()
    
    context = {'form': form, 'student': student}
    return render(request, 'students/contact_form.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def contact_update(request, pk):
    """Update contact"""
    contact = get_object_or_404(StudentContact, pk=pk)
    
    if request.method == 'POST':
        form = StudentContactForm(request.POST, instance=contact)
        if form.is_valid():
            contact = form.save()
            
            # Generate access code if needed
            if contact.can_view_brightwheel and not contact.access_code:
                contact.generate_access_code()
            
            messages.success(request, "Contact updated!")
            return redirect('students:detail', pk=contact.student.pk)
    else:
        form = StudentContactForm(instance=contact)
    
    context = {'form': form, 'contact': contact, 'student': contact.student}
    return render(request, 'students/contact_form.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def contact_delete(request, pk):
    """Delete contact"""
    contact = get_object_or_404(StudentContact, pk=pk)
    student = contact.student
    
    if request.method == 'POST':
        contact.delete()
        messages.success(request, "Contact deleted!")
        return redirect('students:detail', pk=student.pk)
    
    context = {'contact': contact, 'student': student}
    return render(request, 'students/contact_confirm_delete.html', context)


# ========== CUSTOM FIELDS ==========

@login_required
@user_passes_test(is_admin_or_staff)
def custom_field_create(request, student_pk):
    """Add custom field"""
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
    
    context = {'form': form, 'student': student}
    return render(request, 'students/custom_field_form.html', context)


# ========== INCIDENT REPORTS ==========

@login_required
@user_passes_test(is_admin_or_staff)
def incident_report_create(request, student_pk):
    """Create incident report"""
    student = get_object_or_404(Student, pk=student_pk)
    
    if request.method == 'POST':
        form = IncidentReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.student = student
            report.reported_by = request.user
            report.save()
            
            messages.success(request, f"Incident Report #{report.report_number} created!")
            return redirect('students:detail', pk=student.pk)
    else:
        # Auto-increment report number
        last_report = student.incident_reports.order_by('-report_number').first()
        next_number = (last_report.report_number + 1) if last_report else 1
        
        form = IncidentReportForm(initial={'report_number': next_number})
    
    context = {'form': form, 'student': student}
    return render(request, 'students/incident_report_form.html', context)


# ========== IMMUNIZATION VIEWS (Admin/Staff Only) ==========

@login_required
@user_passes_test(is_admin_or_staff)
def immunization_detail(request, student_pk):
    """View immunization details"""
    student = get_object_or_404(Student, pk=student_pk)
    
    # Get or create immunization record
    immunization, created = Immunization.objects.get_or_create(student=student)
    
    if created:
        # Initialize vaccine doses
        initialize_vaccine_doses(immunization)
    
    # Get all vaccine doses grouped by vaccine type
    vaccine_doses = immunization.vaccine_doses.select_related(
        'vaccine_type', 'dose_schedule'
    ).order_by('vaccine_type__display_order', 'dose_schedule__dose_number')
    
    # Group by vaccine type
    vaccines_by_type = {}
    for dose in vaccine_doses:
        vaccine_name = dose.vaccine_type.name
        if vaccine_name not in vaccines_by_type:
            vaccines_by_type[vaccine_name] = {
                'vaccine': dose.vaccine_type,
                'doses': []
            }
        vaccines_by_type[vaccine_name]['doses'].append(dose)
    
    # Get overdue and due soon
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
    """Update immunization settings"""
    student = get_object_or_404(Student, pk=student_pk)
    immunization, created = Immunization.objects.get_or_create(student=student)
    
    if request.method == 'POST':
        form = ImmunizationForm(request.POST, instance=immunization)
        if form.is_valid():
            immunization = form.save(commit=False)
            immunization.last_updated_by = request.user
            immunization.save()
            
            messages.success(request, "Immunization settings updated!")
            return redirect('students:immunization_detail', student_pk=student.pk)
    else:
        form = ImmunizationForm(instance=immunization)
    
    context = {
        'form': form,
        'student': student,
        'immunization': immunization
    }
    return render(request, 'students/immunization_settings.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def vaccine_dose_update(request, dose_pk):
    """Update individual vaccine dose"""
    dose = get_object_or_404(VaccineDose, pk=dose_pk)
    
    if request.method == 'POST':
        form = VaccineDoseForm(request.POST, instance=dose)
        if form.is_valid():
            vaccine_dose = form.save(commit=False)
            vaccine_dose.recorded_by = request.user
            vaccine_dose.save()
            
            messages.success(request, f"{dose.vaccine_type.name} dose updated!")
            return redirect('students:immunization_detail', student_pk=dose.immunization.student.pk)
    else:
        form = VaccineDoseForm(instance=dose)
    
    context = {
        'form': form,
        'dose': dose,
        'student': dose.immunization.student
    }
    return render(request, 'students/vaccine_dose_form.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def vaccine_dose_bulk_update(request, student_pk):
    """Bulk update vaccine doses"""
    student = get_object_or_404(Student, pk=student_pk)
    immunization = student.immunization_record
    
    if request.method == 'POST':
        form = BulkVaccineDoseUpdateForm(request.POST)
        dose_ids = request.POST.getlist('dose_ids')
        
        if form.is_valid() and dose_ids:
            date_administered = form.cleaned_data.get('date_administered')
            administered_by = form.cleaned_data.get('administered_by')
            location = form.cleaned_data.get('location')
            
            # Update selected doses
            doses = VaccineDose.objects.filter(
                id__in=dose_ids,
                immunization=immunization
            )
            
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
    
    # Get all doses
    doses = immunization.vaccine_doses.select_related('vaccine_type', 'dose_schedule')
    
    context = {
        'form': form,
        'student': student,
        'doses': doses
    }
    return render(request, 'students/vaccine_bulk_update.html', context)


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
                # Create or update attendance record
                attendance, created = Attendance.objects.get_or_create(
                    student=student,
                    date=absence_date,
                    defaults={
                        'status': reason,
                        'notes': notes,
                        'checked_in_by': request.user
                    }
                )
                
                if not created:
                    attendance.status = reason
                    attendance.notes = notes
                    attendance.save()
                
                count += 1
            
            # Log activity
            try:
                UserActivity.objects.create(
                    user=request.user,
                    action_type=UserActivity.ActionType.UPDATE,
                    description=f"Marked {count} student(s) as {reason.lower()} for {absence_date}"
                )
            except:
                pass
            
            messages.success(request, f"{count} student(s) marked as absent!")
            return redirect('attendance:attendance_list')
    else:
        form = MarkAbsentForm(initial={'date': date.today()})
    
    context = {'form': form}
    return render(request, 'students/mark_absent.html', context)


# ========== HELPER FUNCTIONS ==========

def initialize_vaccine_doses(immunization):
    """
    Initialize vaccine doses for a student based on CDC schedule
    """
    # Get all vaccine types
    vaccine_types = VaccineType.objects.filter(is_active=True).prefetch_related('dose_schedules')
    
    for vaccine_type in vaccine_types:
        for schedule in vaccine_type.dose_schedules.all():
            # Create dose record
            VaccineDose.objects.get_or_create(
                immunization=immunization,
                vaccine_type=vaccine_type,
                dose_schedule=schedule
            )