"""
Time Tracker Views
- Live dashboard (admin/staff)
- Personal session view (parents, staff)
- Analytics API endpoint (JSON) for the live counter
- Session management helpers

FIXED: All date.today() calls replaced with timezone.localdate() so dates
       are computed in America/Chicago (US Central), not the OS clock.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timezone import localdate
from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, DurationField, Q
from django.db.models.functions import TruncDate, TruncHour
from datetime import timedelta
from decimal import Decimal
import json

from .models import TimeSession, DailySummary
from accounts.models import User
from students.models import Student
from attendance.models import AttendanceCheckIn


# ─── Permission helpers ──────────────────────────────────────────────────────

def is_staff_or_admin(user):
    return user.is_authenticated and (user.is_admin or user.is_staff_member)

def is_admin(user):
    return user.is_authenticated and user.is_admin


# ─── Live Dashboard (Admin / Staff) ──────────────────────────────────────────

@login_required
@user_passes_test(is_staff_or_admin)
def live_dashboard(request):
    """
    Real-time overview of everyone currently on site.
    Rendered once; the JS polling updates counters every 30 s.
    """
    today = localdate()  # FIX: timezone-aware

    active_sessions = TimeSession.objects.filter(
        status=TimeSession.Status.ACTIVE,
        date=today,
    ).select_related(
        'student_checkin__student',
        'student_checkin__room',
        'staff',
        'parent',
    ).order_by('clock_in')

    students_on_site = active_sessions.filter(session_type=TimeSession.SessionType.STUDENT)
    staff_on_site    = active_sessions.filter(session_type=TimeSession.SessionType.STAFF)
    parents_on_site  = active_sessions.filter(session_type=TimeSession.SessionType.PARENT)

    all_today = TimeSession.objects.filter(date=today)
    total_students_today = all_today.filter(session_type=TimeSession.SessionType.STUDENT).count()
    total_staff_today    = all_today.filter(session_type=TimeSession.SessionType.STAFF).count()

    recent_departures = TimeSession.objects.filter(
        date=today,
        status=TimeSession.Status.CLOSED,
    ).select_related(
        'student_checkin__student',
        'staff',
        'parent',
    ).order_by('-clock_out')[:10]

    seven_days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        count = TimeSession.objects.filter(
            date=d,
            session_type=TimeSession.SessionType.STUDENT,
        ).count()
        seven_days.append({'label': d.strftime('%a'), 'count': count})

    context = {
        'today': today,
        'students_on_site': students_on_site,
        'staff_on_site': staff_on_site,
        'parents_on_site': parents_on_site,
        'students_on_site_count': students_on_site.count(),
        'staff_on_site_count': staff_on_site.count(),
        'parents_on_site_count': parents_on_site.count(),
        'total_students_today': total_students_today,
        'total_staff_today': total_staff_today,
        'recent_departures': recent_departures,
        'seven_days_json': json.dumps(seven_days),
    }
    return render(request, 'time_tracker/live_dashboard.html', context)


# ─── Analytics (Admin / Staff) ────────────────────────────────────────────────

@login_required
@user_passes_test(is_staff_or_admin)
def analytics_view(request):
    """
    Full analytics: average hours, peak arrival times, per-student breakdowns.
    """
    today = localdate()  # FIX: timezone-aware
    range_days = int(request.GET.get('days', 30))
    start_date = today - timedelta(days=range_days)

    sessions = TimeSession.objects.filter(
        date__gte=start_date,
        status=TimeSession.Status.CLOSED,
    )

    student_sessions = sessions.filter(session_type=TimeSession.SessionType.STUDENT)

    from collections import defaultdict
    student_stats = defaultdict(lambda: {'total_seconds': 0, 'sessions': 0, 'name': ''})

    for s in student_sessions.select_related('student_checkin__student'):
        if s.student_checkin:
            sid  = s.student_checkin.student_id
            name = s.student_checkin.student.get_full_name()
            student_stats[sid]['name']           = name
            student_stats[sid]['total_seconds'] += s.elapsed_seconds
            student_stats[sid]['sessions']      += 1

    student_rows = []
    for sid, data in student_stats.items():
        avg_h = round(data['total_seconds'] / 3600 / max(data['sessions'], 1), 2)
        tot_h = round(data['total_seconds'] / 3600, 2)
        student_rows.append({
            'student_id': sid,
            'name': data['name'],
            'avg_hours': avg_h,
            'total_hours': tot_h,
            'sessions': data['sessions'],
        })
    student_rows.sort(key=lambda x: x['total_hours'], reverse=True)

    hour_counts = [0] * 24
    for s in student_sessions:
        hour_counts[s.clock_in.astimezone().hour] += 1

    peak_hour_labels = [f"{h:02d}:00" for h in range(24)]

    staff_sessions = sessions.filter(session_type=TimeSession.SessionType.STAFF)
    staff_stats = defaultdict(lambda: {'total_seconds': 0, 'sessions': 0, 'name': ''})

    for s in staff_sessions.select_related('staff'):
        if s.staff:
            uid  = s.staff_id
            staff_stats[uid]['name']            = s.staff.get_full_name()
            staff_stats[uid]['total_seconds']  += s.elapsed_seconds
            staff_stats[uid]['sessions']       += 1

    staff_rows = []
    for uid, data in staff_stats.items():
        tot_h = round(data['total_seconds'] / 3600, 2)
        avg_h = round(data['total_seconds'] / 3600 / max(data['sessions'], 1), 2)
        staff_rows.append({
            'name': data['name'],
            'total_hours': tot_h,
            'avg_hours': avg_h,
            'sessions': data['sessions'],
        })
    staff_rows.sort(key=lambda x: x['total_hours'], reverse=True)

    daily_totals = []
    for i in range(range_days - 1, -1, -1):
        d = today - timedelta(days=i)
        cnt = TimeSession.objects.filter(
            date=d, session_type=TimeSession.SessionType.STUDENT
        ).count()
        daily_totals.append({'date': d.strftime('%b %d'), 'count': cnt})

    context = {
        'range_days': range_days,
        'start_date': start_date,
        'student_rows': student_rows,
        'staff_rows': staff_rows,
        'peak_hour_labels_json': json.dumps(peak_hour_labels),
        'peak_hour_data_json': json.dumps(hour_counts),
        'daily_totals_json': json.dumps(daily_totals),
        'total_student_sessions': student_sessions.count(),
        'total_staff_sessions': staff_sessions.count(),
    }
    return render(request, 'time_tracker/analytics.html', context)


# ─── Personal Session History (Parents & Staff) ───────────────────────────────

@login_required
def my_sessions(request):
    """
    Parents see their children's session history.
    Staff see their own clock-in history.
    Admins see everything (redirect to dashboard).
    """
    user  = request.user
    today = localdate()  # FIX: timezone-aware

    if user.is_admin:
        return redirect('time_tracker:live_dashboard')

    if user.is_parent:
        sessions = TimeSession.objects.filter(
            session_type=TimeSession.SessionType.STUDENT,
            student_checkin__student__parent=user,
        ).select_related(
            'student_checkin__student',
            'student_checkin__room',
        ).order_by('-clock_in')[:60]

        active = sessions.filter(status=TimeSession.Status.ACTIVE, date=today)

        week_ago = today - timedelta(days=7)
        children = Student.objects.filter(parent=user)
        child_stats = []
        for child in children:
            child_sessions = TimeSession.objects.filter(
                session_type=TimeSession.SessionType.STUDENT,
                student_checkin__student=child,
                date__gte=week_ago,
                status=TimeSession.Status.CLOSED,
            )
            total_s = sum(s.elapsed_seconds for s in child_sessions)
            child_stats.append({
                'child': child,
                'week_hours': round(total_s / 3600, 1),
                'week_days': child_sessions.values('date').distinct().count(),
            })

        context = {
            'sessions': sessions,
            'active_sessions': active,
            'child_stats': child_stats,
            'today': today,
        }
        return render(request, 'time_tracker/parent_sessions.html', context)

    else:  # staff
        sessions = TimeSession.objects.filter(
            session_type=TimeSession.SessionType.STAFF,
            staff=user,
        ).order_by('-clock_in')[:60]

        active = sessions.filter(status=TimeSession.Status.ACTIVE, date=today)

        week_ago = today - timedelta(days=7)
        week_sessions = sessions.filter(date__gte=week_ago, status=TimeSession.Status.CLOSED)
        week_total_s  = sum(s.elapsed_seconds for s in week_sessions)

        context = {
            'sessions': sessions,
            'active_sessions': active,
            'week_hours': round(week_total_s / 3600, 1),
            'week_days': week_sessions.values('date').distinct().count(),
            'today': today,
        }
        return render(request, 'time_tracker/staff_sessions.html', context)


# ─── JSON polling endpoint ────────────────────────────────────────────────────

@login_required
def session_status_api(request):
    """
    Returns JSON with live elapsed seconds for all active sessions today.
    Called every 30 s by the front-end JS.
    """
    today = localdate()  # FIX: timezone-aware
    active = TimeSession.objects.filter(
        status=TimeSession.Status.ACTIVE,
        date=today,
    ).select_related('student_checkin__student', 'staff', 'parent')

    if request.user.is_parent:
        active = active.filter(
            session_type=TimeSession.SessionType.STUDENT,
            student_checkin__student__parent=request.user,
        )
    elif request.user.is_staff_member:
        active = active

    data = {
        'sessions': [
            {
                'id': s.id,
                'elapsed_seconds': s.elapsed_seconds,
                'display_name': s.display_name,
                'session_type': s.session_type,
                'clock_in': s.clock_in.isoformat(),
            }
            for s in active
        ],
        'counts': {
            'students': active.filter(session_type=TimeSession.SessionType.STUDENT).count(),
            'staff':    active.filter(session_type=TimeSession.SessionType.STAFF).count(),
            'parents':  active.filter(session_type=TimeSession.SessionType.PARENT).count(),
        },
        'server_time': timezone.now().isoformat(),
    }
    return JsonResponse(data)


# ─── Admin: manual session close ──────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def force_close_session(request, session_id):
    """Admin can manually close a stuck session."""
    if request.method == 'POST':
        session = get_object_or_404(TimeSession, pk=session_id)
        notes   = request.POST.get('notes', 'Manually closed by admin.')
        session.close(notes=notes)
        from django.contrib import messages
        messages.success(request, f"Session for {session.display_name} closed.")
    return redirect('time_tracker:live_dashboard')