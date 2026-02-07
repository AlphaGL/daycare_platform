"""
Authentication Views - FIXED VERSION
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
    """User login view - FIXED"""
    # If already authenticated, redirect based on role
    if request.user.is_authenticated:
        if request.user.is_admin or request.user.is_staff_member:
            return redirect('school:dashboard')  # Assuming school app has dashboard
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Try to log activity (non-critical)
                try:
                    UserActivity.objects.create(
                        user=user,
                        action_type=UserActivity.ActionType.LOGIN,
                        description=f"User logged in",
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                except Exception as e:
                    # Log error but don't fail the login
                    print(f"Activity logging failed: {e}")
                
                messages.success(request, f"Welcome back, {user.get_full_name()}!")
                
                # Handle 'next' parameter for redirect after login
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                # Default redirect based on role
                if user.is_admin or user.is_staff_member:
                    # Admin/Staff go to dashboard
                    return redirect('school:dashboard')
                else:
                    # Parents go to profile
                    return redirect('accounts:profile')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            # Form has validation errors
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    """User logout view"""
    if request.user.is_authenticated:
        # Try to log activity (non-critical)
        try:
            UserActivity.objects.create(
                user=request.user,
                action_type=UserActivity.ActionType.LOGOUT,
                description=f"User logged out",
                ip_address=get_client_ip(request)
            )
        except Exception as e:
            print(f"Activity logging failed: {e}")
    
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')


def parent_register(request):
    """Parent registration view - FIXED"""
    # If already authenticated, redirect based on role
    if request.user.is_authenticated:
        if request.user.is_admin or request.user.is_staff_member:
            return redirect('school:dashboard')
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                
                # Try to log activity (non-critical)
                try:
                    UserActivity.objects.create(
                        user=user,
                        action_type=UserActivity.ActionType.CREATE,
                        description=f"New parent account created",
                        ip_address=get_client_ip(request)
                    )
                except Exception as e:
                    print(f"Activity logging failed: {e}")
                
                # Log them in
                login(request, user)
                
                messages.success(
                    request,
                    "Registration successful! Welcome to our daycare family."
                )
                
                # Redirect to student registration
                return redirect('students:register')
            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}")
        else:
            # Form has validation errors
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
            
            # Try to log activity (non-critical)
            try:
                UserActivity.objects.create(
                    user=request.user,
                    action_type=UserActivity.ActionType.UPDATE,
                    description="Profile updated",
                    ip_address=get_client_ip(request)
                )
            except Exception as e:
                print(f"Activity logging failed: {e}")
            
            messages.success(request, "Profile updated successfully!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileUpdateForm(instance=request.user)
    
    # Get recent activities (handle errors)
    try:
        recent_activities = request.user.activities.all()[:10]
    except:
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