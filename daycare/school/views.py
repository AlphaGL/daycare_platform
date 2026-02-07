"""
Enhanced School Dashboard Views
Separate dashboards for Admin, Staff, and Parents
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta, date
from .models import SchoolProfile, SchoolSettings, Reminder
from .forms import SchoolProfileForm, SchoolSettingsForm, ReminderForm
from students.models import Student, StudentRegistration, Attendance
from rooms.models import Room
from notifications.models import Message, Announcement
from accounts.models import User, UserActivity
from attendance.models import AttendanceCheckIn
from attendance.models import Schedule


def is_admin(user):
    return user.is_authenticated and user.is_admin


def is_staff_or_admin(user):
    return user.is_authenticated and (user.is_admin or user.is_staff_member)


@login_required
def dashboard(request):
    """Main dashboard - role-based redirect"""
    if request.user.is_admin:
        return admin_dashboard(request)
    elif request.user.is_staff_member:
        return staff_dashboard(request)
    elif request.user.is_parent:
        return parent_dashboard(request)
    return redirect('home')


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Enhanced Admin Dashboard
    Comprehensive view with room ratios, activities, and analytics
    """
    # Get school profile
    school = SchoolProfile.get_instance()
    
    # Get today's date (define early to avoid UnboundLocalError)
    today = date.today()
    
    # Basic Statistics
    total_students = Student.objects.filter(status='ACTIVE').count()
    total_rooms = Room.objects.filter(is_active=True).count()
    total_staff = User.objects.filter(role='STAFF', is_active=True).count()
    total_parents = User.objects.filter(role='PARENT', is_active=True).count()
    
    # Recent activity (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_students = Student.objects.filter(created_at__gte=week_ago).count()
    recent_registrations = StudentRegistration.objects.filter(created_at__gte=week_ago).count()
    
    # Pending items
    pending_registrations = StudentRegistration.objects.filter(status='PENDING').count()
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()
    
    # Current Room Ratios (like Brightwheel)
    rooms_with_ratios = []
    all_rooms = Room.objects.filter(is_active=True).select_related().prefetch_related('assigned_staff', 'students')
    
    total_students_in_rooms = 0
    total_staff_in_rooms = 0
    
    for room in all_rooms:
        students_count = room.students.filter(status='ACTIVE').count()
        
        # Get today's checked-in students
        checked_in_students = Attendance.objects.filter(
            student__room=room,
            date=today,
            status='PRESENT',
            check_out_time__isnull=True
        ).count()
        
        staff_count = room.assigned_staff.filter(
            is_active=True,
            staff_profile__is_active_staff=True
        ).count()
        
        total_students_in_rooms += checked_in_students
        total_staff_in_rooms += staff_count
        
        ratio = f"{checked_in_students}:{staff_count}" if staff_count > 0 else "N/A"
        
        rooms_with_ratios.append({
            'room': room,
            'students_enrolled': students_count,
            'students_in': checked_in_students,
            'staff_in': staff_count,
            'ratio': ratio,
            'capacity': room.capacity,
            'available_spots': room.capacity - students_count
        })
    
    # Today's logged activities
    today_activities = Attendance.objects.filter(
        date=today
    ).select_related('student', 'student__room').order_by('-check_in_time')[:10]
    
    # Recent messages
    recent_messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).select_related('sender', 'recipient').order_by('-created_at')[:5]
    
    # Active reminders
    active_reminders = Reminder.objects.filter(
        created_by=request.user,
        is_completed=False,
        remind_at__gte=timezone.now()
    ).order_by('remind_at')[:5]
    
    # Recent announcements
    recent_announcements = Announcement.objects.filter(
        is_published=True
    ).order_by('-publish_date')[:3]
    
    # System health checks
    rooms_at_capacity = sum(1 for r in rooms_with_ratios if r['available_spots'] == 0)
    rooms_understaffed = sum(1 for r in rooms_with_ratios if r['staff_in'] == 0 and r['students_in'] > 0)
    
    # Revenue data (if billing exists)
    try:
        from billing.models import Payment
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = Payment.objects.filter(
            payment_date__gte=month_start,
            status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total'] or 0
    except:
        monthly_revenue = None
    
    # Recent user activities
    recent_user_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:10]

    checked_in_today = AttendanceCheckIn.objects.filter(
        date=today,
        status='CHECKED_IN'
    ).count()
    
    total_today = AttendanceCheckIn.objects.filter(
        date=today
    ).count()
    
    context = {
        'school': school,
        'total_students': total_students,
        'total_rooms': total_rooms,
        'total_staff': total_staff,
        'total_parents': total_parents,
        'recent_students': recent_students,
        'recent_registrations': recent_registrations,
        'pending_registrations': pending_registrations,
        'unread_messages': unread_messages,
        'rooms_with_ratios': rooms_with_ratios,
        'total_students_in': total_students_in_rooms,
        'total_staff_in': total_staff_in_rooms,
        'today_activities': today_activities,
        'recent_messages': recent_messages,
        'active_reminders': active_reminders,
        'recent_announcements': recent_announcements,
        'rooms_at_capacity': rooms_at_capacity,
        'rooms_understaffed': rooms_understaffed,
        'monthly_revenue': monthly_revenue,
        'recent_user_activities': recent_user_activities,
        'current_time': timezone.now(),
        'checked_in_today': checked_in_today,
        'total_attendance_today': total_today,
    }   
    
    return render(request, 'school/admin_dashboard.html', context)


@login_required
@user_passes_test(is_staff_or_admin)
def staff_dashboard(request):
    """Staff Dashboard"""
    today = date.now
    school = SchoolProfile.get_instance()
    assigned_rooms = request.user.assigned_rooms.filter(is_active=True)
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()
    
    # Today's schedule
    from staff.models import StaffSchedule
    today_day = timezone.now().isoweekday()
    today_schedule = StaffSchedule.objects.filter(
        staff=request.user,
        day_of_week=today_day,
        is_active=True
    ).order_by('start_time')
    
    # Count students in assigned rooms
    total_students = Student.objects.filter(
        room__in=assigned_rooms,
        status='ACTIVE'
    ).count()
    
    # Recent announcements
    recent_announcements = Announcement.objects.filter(
        is_published=True,
        target_audience__in=['ALL', 'STAFF']
    ).order_by('-publish_date')[:3]

    today_schedules = Schedule.objects.filter(
        Q(end_date__gte=today) | Q(end_date__isnull=True),
                assigned_staff=request.user,
        start_date__lte=today,
        is_active=True
    ).order_by('start_time')
    
    context = {
        'school': school,
        'assigned_rooms': assigned_rooms,
        'unread_messages': unread_messages,
        'today_schedule': today_schedule,
        'total_students': total_students,
        'recent_announcements': recent_announcements,
        'today_schedules': today_schedules,
    }
    
    return render(request, 'school/staff_dashboard.html', context)


@login_required
def parent_dashboard(request):
    """Parent Dashboard"""
    school = SchoolProfile.get_instance()
    
    # Get children with prefetched today's attendance
    today = date.today()
    children = request.user.children.filter(status='ACTIVE').prefetch_related(
        'attendance_records'
    )
    
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()
    
    # Recent announcements for parents
    recent_announcements = Announcement.objects.filter(
        is_published=True,
        target_audience__in=['ALL', 'PARENTS']
    ).order_by('-publish_date')[:5]
    
    context = {
        'school': school,
        'children': children,
        'unread_messages': unread_messages,
        'recent_announcements': recent_announcements,
        'today_date': today,
    }
    
    return render(request, 'school/parent_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def school_profile_view(request):
    """View and update school profile"""
    school = SchoolProfile.get_instance()
    
    if request.method == 'POST':
        form = SchoolProfileForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, "School profile updated!")
            return redirect('school:profile')
    else:
        form = SchoolProfileForm(instance=school)
    
    return render(request, 'school/profile.html', {'form': form, 'school': school})


@login_required
@user_passes_test(is_admin)
def school_settings_view(request):
    """View and update school settings"""
    settings = SchoolSettings.get_instance()
    
    if request.method == 'POST':
        form = SchoolSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()
            messages.success(request, "Settings updated!")
            return redirect('school:settings')
    else:
        form = SchoolSettingsForm(instance=settings)
    
    return render(request, 'school/settings.html', {'form': form, 'settings': settings})


@login_required
@user_passes_test(is_admin)
def reminder_list(request):
    """List all reminders"""
    reminders = Reminder.objects.filter(created_by=request.user)
    return render(request, 'school/reminder_list.html', {'reminders': reminders})


@login_required
@user_passes_test(is_admin)
def reminder_create(request):
    """Create reminder"""
    if request.method == 'POST':
        form = ReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.created_by = request.user
            reminder.save()
            messages.success(request, "Reminder created!")
            return redirect('school:reminder_list')
    else:
        form = ReminderForm()
    
    return render(request, 'school/reminder_form.html', {'form': form})