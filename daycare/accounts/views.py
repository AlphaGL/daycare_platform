"""
Authentication Views
Login, Registration, Profile Management
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .forms import UserLoginForm, ParentRegistrationForm, UserProfileUpdateForm, CheckInCodeForm
from .models import UserActivity


def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Log activity
                UserActivity.objects.create(
                    user=user,
                    action_type=UserActivity.ActionType.LOGIN,
                    description=f"User logged in",
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f"Welcome back, {user.get_full_name()}!")
                
                # Redirect based on role
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    """User logout view"""
    if request.user.is_authenticated:
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            action_type=UserActivity.ActionType.LOGOUT,
            description=f"User logged out",
            ip_address=get_client_ip(request)
        )
    
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')


def parent_register(request):
    """Parent registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Log activity
            UserActivity.objects.create(
                user=user,
                action_type=UserActivity.ActionType.CREATE,
                description=f"New parent account created",
                ip_address=get_client_ip(request)
            )
            
            # Log them in
            login(request, user)
            
            messages.success(
                request,
                "Registration successful! You can now register your child."
            )
            return redirect('students:register')
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
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action_type=UserActivity.ActionType.UPDATE,
                description="Profile updated",
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, "Profile updated successfully!")
            return redirect('accounts:profile')
    else:
        form = UserProfileUpdateForm(instance=request.user)
    
    # Get recent activities
    recent_activities = request.user.activities.all()[:10]
    
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
            messages.success(request, "Check-in code updated successfully!")
            return redirect('accounts:profile')
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