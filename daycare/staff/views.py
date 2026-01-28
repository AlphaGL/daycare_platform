from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from accounts.models import User
from .models import StaffSchedule, Timecard


def is_admin(user):
    return user.is_authenticated and user.is_admin


@login_required
@user_passes_test(is_admin)
def staff_list(request):
    """List all staff"""
    staff_members = User.objects.filter(role='STAFF', is_active=True)
    return render(request, 'staff/staff_list.html', {'staff_members': staff_members})


@login_required
def staff_schedule(request):
    """View staff schedules"""
    if request.user.is_admin:
        schedules = StaffSchedule.objects.filter(is_active=True)
    else:
        schedules = request.user.schedules.filter(is_active=True)
    
    return render(request, 'staff/schedule_list.html', {'schedules': schedules})


@login_required
def timecard_list(request):
    """View timecards"""
    if request.user.is_admin:
        timecards = Timecard.objects.all()
    else:
        timecards = request.user.timecards.all()
    
    return render(request, 'staff/timecard_list.html', {'timecards': timecards})