from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from .models import SchoolProfile, SchoolSettings, Reminder
from .forms import SchoolProfileForm, SchoolSettingsForm, ReminderForm
from students.models import Student
from rooms.models import Room
from notifications.models import Message


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
    """Admin Dashboard"""
    total_students = Student.objects.filter(status='ACTIVE').count()
    total_rooms = Room.objects.filter(is_active=True).count()
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()
    
    context = {
        'total_students': total_students,
        'total_rooms': total_rooms,
        'unread_messages': unread_messages,
    }
    return render(request, 'school/admin_dashboard.html', context)


@login_required
@user_passes_test(is_staff_or_admin)
def staff_dashboard(request):
    """Staff Dashboard"""
    assigned_rooms = request.user.assigned_rooms.filter(is_active=True)
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()
    
    context = {
        'assigned_rooms': assigned_rooms,
        'unread_messages': unread_messages,
    }
    return render(request, 'school/staff_dashboard.html', context)


@login_required
def parent_dashboard(request):
    """Parent Dashboard"""
    children = request.user.children.filter(status='ACTIVE')
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()
    
    context = {
        'children': children,
        'unread_messages': unread_messages,
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
    
    return render(request, 'school/profile.html', {'form': form})


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
    
    return render(request, 'school/settings.html', {'form': form})


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