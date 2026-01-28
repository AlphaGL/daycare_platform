from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Student, StudentRegistration
from .forms import StudentForm, StudentRegistrationForm


def is_admin_or_staff(user):
    return user.is_authenticated and (user.is_admin or user.is_staff_member)


@login_required
def student_list(request):
    """List all students"""
    if request.user.is_parent:
        students = request.user.children.all()
    else:
        students = Student.objects.all()
    
    return render(request, 'students/student_list.html', {'students': students})


@login_required
def student_detail(request, pk):
    """Student details"""
    student = get_object_or_404(Student, pk=pk)
    
    # Check permission
    if request.user.is_parent and student.parent != request.user:
        messages.error(request, "You don't have permission to view this student.")
        return redirect('students:list')
    
    return render(request, 'students/student_detail.html', {'student': student})


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
            messages.success(request, "Student updated!")
            return redirect('students:detail', pk=student.pk)
    else:
        form = StudentForm(instance=student)
    
    return render(request, 'students/student_form.html', {'form': form, 'student': student})
