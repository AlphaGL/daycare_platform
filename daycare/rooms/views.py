from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Room, LessonPlan
from .forms import RoomForm, LessonPlanForm


def is_admin(user):
    return user.is_authenticated and user.is_admin


@login_required
def room_list(request):
    """List all rooms"""
    rooms = Room.objects.filter(is_active=True)
    return render(request, 'rooms/room_list.html', {'rooms': rooms})


@login_required
def room_detail(request, pk):
    """Room details"""
    room = get_object_or_404(Room, pk=pk)
    students = room.get_students()
    
    context = {
        'room': room,
        'students': students,
        'ratio': room.student_staff_ratio,
    }
    return render(request, 'rooms/room_detail.html', context)


@login_required
@user_passes_test(is_admin)
def room_create(request):
    """Create room"""
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.created_by = request.user
            room.save()
            form.save_m2m()
            messages.success(request, "Room created!")
            return redirect('rooms:detail', pk=room.pk)
    else:
        form = RoomForm()
    
    return render(request, 'rooms/room_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def room_update(request, pk):
    """Update room"""
    room = get_object_or_404(Room, pk=pk)
    
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, "Room updated!")
            return redirect('rooms:detail', pk=room.pk)
    else:
        form = RoomForm(instance=room)
    
    return render(request, 'rooms/room_form.html', {'form': form, 'room': room})