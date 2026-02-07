"""
Attendance and Schedule Views
Check-In/Check-Out and Scheduling System
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import date, timedelta
from .models import AttendanceCheckIn, Schedule, StaffTimecard
from .forms import (
    CheckInForm, CheckOutForm, ScheduleForm, 
    QuickCheckInForm, StaffTimecardForm
)
from students.models import Student
from rooms.models import Room
from accounts.models import User, UserActivity


def is_staff_or_admin(user):
    return user.is_authenticated and (user.is_admin or user.is_staff_member)


# ==================== CHECK-IN/CHECK-OUT VIEWS ====================

@login_required
def student_checkin(request):
    """
    Student Check-In View
    Parents check in their own children using their check-in code
    """
    if request.method == 'POST':
        form = CheckInForm(request.POST, user=request.user)
        if form.is_valid():
            # Create check-in record
            checkin = form.save(commit=False)
            checkin.check_in_time = timezone.now()
            checkin.check_in_by = request.user
            checkin.check_in_code_verified = True
            checkin.status = AttendanceCheckIn.Status.CHECKED_IN
            checkin.save()
            
            # Log activity
            try:
                UserActivity.objects.create(
                    user=request.user,
                    action_type=UserActivity.ActionType.CREATE,
                    description=f"Checked in {checkin.student.get_full_name()}",
                )
            except:
                pass
            
            messages.success(
                request, 
                f"✅ {checkin.student.get_full_name()} has been checked in successfully!"
            )
            return redirect('attendance:checkin')
    else:
        form = CheckInForm(user=request.user)
    
    # Get today's check-ins
    today = date.today()
    
    # Filter check-ins based on user role
    if request.user.is_parent:
        # Parents see only their children's check-ins
        todays_checkins = AttendanceCheckIn.objects.filter(
            date=today,
            student__parent=request.user,
            status=AttendanceCheckIn.Status.CHECKED_IN
        ).select_related('student', 'room', 'check_in_by').order_by('-check_in_time')
    else:
        # Staff/Admin see all check-ins
        todays_checkins = AttendanceCheckIn.objects.filter(
            date=today,
            status=AttendanceCheckIn.Status.CHECKED_IN
        ).select_related('student', 'room', 'check_in_by').order_by('-check_in_time')[:10]
    
    context = {
        'form': form,
        'todays_checkins': todays_checkins,
        'total_checked_in': AttendanceCheckIn.objects.filter(
            date=today,
            status=AttendanceCheckIn.Status.CHECKED_IN
        ).count() if not request.user.is_parent else todays_checkins.count()
    }
    return render(request, 'attendance/checkin.html', context)


@login_required
def student_checkout(request, pk):
    """
    Student Check-Out View
    Parents check out their own children using their check-in code
    """
    checkin = get_object_or_404(
        AttendanceCheckIn, 
        pk=pk, 
        status=AttendanceCheckIn.Status.CHECKED_IN
    )
    
    # Parents can only check out their own children
    if request.user.is_parent and checkin.student.parent != request.user:
        messages.error(request, "You can only check out your own children.")
        return redirect('attendance:attendance_list')
    
    if request.method == 'POST':
        form = CheckOutForm(student=checkin.student, data=request.POST)
        if form.is_valid():
            # Perform checkout
            checkin.perform_checkout(
                user=request.user,
                code_verified=True
            )
            
            # Add notes if provided
            if form.cleaned_data.get('notes'):
                checkin.notes += f"\nCheck-out: {form.cleaned_data['notes']}"
                checkin.save()
            
            # Log activity
            try:
                UserActivity.objects.create(
                    user=request.user,
                    action_type=UserActivity.ActionType.UPDATE,
                    description=f"Checked out {checkin.student.get_full_name()}",
                )
            except:
                pass
            
            messages.success(
                request,
                f"✅ {checkin.student.get_full_name()} has been checked out successfully!"
            )
            return redirect('attendance:attendance_list')
    else:
        form = CheckOutForm(student=checkin.student)
    
    context = {
        'form': form,
        'checkin': checkin,
        'student': checkin.student
    }
    return render(request, 'attendance/checkout.html', context)


@login_required
def attendance_list(request):
    """
    Attendance List View
    View all attendance records (filtered by role)
    """
    today = date.today()
    
    # Filter by date
    selected_date = request.GET.get('date', today.isoformat())
    try:
        filter_date = date.fromisoformat(selected_date)
    except:
        filter_date = today
    
    # Get attendance records based on user role
    if request.user.is_parent:
        # Parents see only their children's attendance
        attendance_records = AttendanceCheckIn.objects.filter(
            date=filter_date,
            student__parent=request.user
        ).select_related('student', 'room', 'check_in_by', 'check_out_by').order_by('-check_in_time')
    else:
        # Staff/Admin see all attendance
        attendance_records = AttendanceCheckIn.objects.filter(
            date=filter_date
        ).select_related('student', 'room', 'check_in_by', 'check_out_by').order_by('-check_in_time')
    
    # Statistics
    total_checkins = attendance_records.count()
    currently_in = attendance_records.filter(status=AttendanceCheckIn.Status.CHECKED_IN).count()
    checked_out = attendance_records.filter(status=AttendanceCheckIn.Status.CHECKED_OUT).count()
    
    context = {
        'attendance_records': attendance_records,
        'selected_date': filter_date,
        'total_checkins': total_checkins,
        'currently_in': currently_in,
        'checked_out': checked_out,
    }
    return render(request, 'attendance/attendance_list.html', context)


@login_required
def attendance_detail(request, pk):
    """Attendance record detail"""
    record = get_object_or_404(AttendanceCheckIn, pk=pk)
    
    # Parents can only view their own children's records
    if request.user.is_parent and record.student.parent != request.user:
        messages.error(request, "You can only view your own children's attendance.")
        return redirect('attendance:attendance_list')
    
    context = {
        'record': record,
        'student': record.student
    }
    return render(request, 'attendance/attendance_detail.html', context)


# ==================== SCHEDULE VIEWS ====================

@login_required
def schedule_list(request):
    """
    Schedule List View
    View all schedules (filtered by user role)
    """
    today = date.today()
    
    # Base queryset
    schedules = Schedule.objects.filter(is_active=True)
    
    # Filter by user role
    if request.user.is_parent:
        # Parents see schedules for their children
        schedules = schedules.filter(
            Q(assigned_students__parent=request.user) |
            Q(assigned_students__isnull=True, schedule_type=Schedule.ScheduleType.ACTIVITY)
        ).distinct()
    elif request.user.is_staff_member:
        # Staff see their own schedules and room schedules
        schedules = schedules.filter(
            Q(assigned_staff=request.user) |
            Q(assigned_room__assigned_staff=request.user)
        ).distinct()
    
    # Filter by date range
    filter_type = request.GET.get('filter', 'today')
    if filter_type == 'today':
        schedules = schedules.filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True),
            start_date__lte=today
        )
    elif filter_type == 'week':
        week_end = today + timedelta(days=7)
        schedules = schedules.filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True),
            start_date__lte=week_end
        )
    elif filter_type == 'month':
        month_end = today + timedelta(days=30)
        schedules = schedules.filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True),
            start_date__lte=month_end
        )
    
    schedules = schedules.select_related('assigned_room', 'created_by').prefetch_related(
        'assigned_staff', 'assigned_students'
    ).order_by('start_date', 'start_time')
    
    context = {
        'schedules': schedules,
        'filter_type': filter_type,
        'today': today,
    }
    return render(request, 'attendance/schedule_list.html', context)


@login_required
@user_passes_test(is_staff_or_admin)
def schedule_create(request):
    """Create new schedule"""
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, f"✅ Schedule '{schedule.title}' created successfully!")
            return redirect('attendance:schedule_list')
    else:
        form = ScheduleForm()
    
    return render(request, 'attendance/schedule_form.html', {'form': form})


@login_required
@user_passes_test(is_staff_or_admin)
def schedule_update(request, pk):
    """Update schedule"""
    schedule = get_object_or_404(Schedule, pk=pk)
    
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Schedule '{schedule.title}' updated successfully!")
            return redirect('attendance:schedule_list')
    else:
        form = ScheduleForm(instance=schedule)
    
    context = {
        'form': form,
        'schedule': schedule
    }
    return render(request, 'attendance/schedule_form.html', context)


@login_required
def schedule_detail(request, pk):
    """Schedule detail view"""
    schedule = get_object_or_404(Schedule, pk=pk)
    
    # Check permission
    if request.user.is_parent:
        # Parents can only view schedules for their children
        if not schedule.assigned_students.filter(parent=request.user).exists():
            messages.error(request, "You don't have permission to view this schedule.")
            return redirect('attendance:schedule_list')
    
    context = {
        'schedule': schedule
    }
    return render(request, 'attendance/schedule_detail.html', context)


@login_required
@user_passes_test(is_staff_or_admin)
def schedule_delete(request, pk):
    """Delete schedule"""
    schedule = get_object_or_404(Schedule, pk=pk)
    
    if request.method == 'POST':
        title = schedule.title
        schedule.delete()
        messages.success(request, f"Schedule '{title}' deleted successfully!")
        return redirect('attendance:schedule_list')
    
    context = {'schedule': schedule}
    return render(request, 'attendance/schedule_confirm_delete.html', context)


# ==================== STAFF TIMECARD VIEWS ====================

@login_required
@user_passes_test(is_staff_or_admin)
def timecard_list(request):
    """Staff timecard list"""
    today = date.today()
    
    # Filter timecards
    if request.user.is_staff_member:
        timecards = StaffTimecard.objects.filter(staff=request.user)
    else:
        timecards = StaffTimecard.objects.all()
    
    timecards = timecards.select_related('staff', 'assigned_room').order_by('-date', '-clock_in_time')[:50]
    
    # Today's active timecards
    active_timecards = StaffTimecard.objects.filter(
        date=today,
        clock_out_time__isnull=True
    ).select_related('staff', 'assigned_room')
    
    context = {
        'timecards': timecards,
        'active_timecards': active_timecards,
    }
    return render(request, 'attendance/timecard_list.html', context)


@login_required
@user_passes_test(is_staff_or_admin)
def staff_clock_in(request):
    """Staff clock-in"""
    if request.method == 'POST':
        form = StaffTimecardForm(request.POST)
        if form.is_valid():
            timecard = form.save(commit=False)
            timecard.clock_in_time = timezone.now()
            timecard.date = date.today()
            timecard.save()
            
            messages.success(request, f"✅ {timecard.staff.get_full_name()} clocked in successfully!")
            return redirect('attendance:timecard_list')
    else:
        # Pre-fill with current user if staff
        initial = {}
        if request.user.is_staff_member:
            initial['staff'] = request.user
        form = StaffTimecardForm(initial=initial)
    
    return render(request, 'attendance/staff_clock_in.html', {'form': form})


@login_required
@user_passes_test(is_staff_or_admin)
def staff_clock_out(request, pk):
    """Staff clock-out"""
    timecard = get_object_or_404(StaffTimecard, pk=pk, clock_out_time__isnull=True)
    
    if request.method == 'POST':
        timecard.clock_out_time = timezone.now()
        notes = request.POST.get('notes', '')
        if notes:
            timecard.notes += f"\nClock-out: {notes}"
        timecard.save()
        
        messages.success(request, f"✅ {timecard.staff.get_full_name()} clocked out successfully!")
        return redirect('attendance:timecard_list')
    
    context = {'timecard': timecard}
    return render(request, 'attendance/staff_clock_out.html', context)