"""
Authentication Views - WITH EMAIL NOTIFICATIONS
Login, Registration, Profile Management
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .forms import UserLoginForm, ParentRegistrationForm, UserProfileUpdateForm, CheckInCodeForm
from .models import UserActivity, User
from notifications_service.email_service import (
    send_parent_welcome_email,
    send_admin_new_parent_notification,
    send_profile_updated_email,
    send_checkin_code_updated_email,
)
import threading


def _send_async(fn, *args, **kwargs):
    """Run email sending in a background thread so it never blocks the request."""
    t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    t.start()


def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        if request.user.is_admin or request.user.is_staff_member:
            return redirect('school:dashboard')
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)

                try:
                    UserActivity.objects.create(
                        user=user,
                        action_type=UserActivity.ActionType.LOGIN,
                        description="User logged in",
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                except Exception as e:
                    print(f"Activity logging failed: {e}")

                messages.success(request, f"Welcome back, {user.get_full_name()}!")

                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)

                if user.is_admin or user.is_staff_member:
                    return redirect('school:dashboard')
                else:
                    return redirect('accounts:profile')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    """User logout view"""
    if request.user.is_authenticated:
        try:
            UserActivity.objects.create(
                user=request.user,
                action_type=UserActivity.ActionType.LOGOUT,
                description="User logged out",
                ip_address=get_client_ip(request)
            )
        except Exception as e:
            print(f"Activity logging failed: {e}")

    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')


def parent_register(request):
    """Parent registration view with email notifications"""
    if request.user.is_authenticated:
        if request.user.is_admin or request.user.is_staff_member:
            return redirect('school:dashboard')
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()

                try:
                    UserActivity.objects.create(
                        user=user,
                        action_type=UserActivity.ActionType.CREATE,
                        description="New parent account created",
                        ip_address=get_client_ip(request)
                    )
                except Exception as e:
                    print(f"Activity logging failed: {e}")

                # ── EMAIL: welcome the new parent ──────────────────────────
                _send_async(send_parent_welcome_email, user)

                # ── EMAIL: notify all admins ───────────────────────────────
                admins = User.objects.filter(role=User.Role.ADMIN, is_active=True)
                for admin in admins:
                    _send_async(send_admin_new_parent_notification, admin, user)

                login(request, user)
                messages.success(
                    request,
                    "Registration successful! Welcome to our daycare family. "
                    "A confirmation email has been sent to you."
                )
                return redirect('students:register')
            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ParentRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    """User profile view and update"""
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()

            try:
                UserActivity.objects.create(
                    user=request.user,
                    action_type=UserActivity.ActionType.UPDATE,
                    description="Profile updated",
                    ip_address=get_client_ip(request)
                )
            except Exception as e:
                print(f"Activity logging failed: {e}")

            # ── EMAIL: notify user that their profile was changed ──────────
            _send_async(send_profile_updated_email, request.user)

            messages.success(request, "Profile updated successfully!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileUpdateForm(instance=request.user)

    try:
        recent_activities = request.user.activities.all()[:10]
    except Exception:
        recent_activities = []

    context = {
        'form': form,
        'recent_activities': recent_activities,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def update_check_in_code(request):
    """Update check-in code"""
    if request.method == 'POST':
        form = CheckInCodeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()

            # ── EMAIL: notify user their check-in code changed ─────────────
            _send_async(send_checkin_code_updated_email, request.user)

            messages.success(request, "Check-in code updated successfully!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CheckInCodeForm(instance=request.user)

    return render(request, 'accounts/check_in_code.html', {'form': form})


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip