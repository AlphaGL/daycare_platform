from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from .models import Message, Announcement
from .forms import MessageForm


@login_required
def inbox(request):
    """User inbox"""
    messages = Message.objects.filter(recipient=request.user).order_by('-created_at')
    unread_count = messages.filter(is_read=False).count()
    
    return render(request, 'messages/inbox.html', {
        'messages': messages,
        'unread_count': unread_count
    })


@login_required
def message_detail(request, pk):
    """View message"""
    message = get_object_or_404(Message, pk=pk)
    
    if message.recipient == request.user:
        message.mark_as_read()
    
    return render(request, 'messages/message_detail.html', {'message': message})


@login_required
def compose_message(request):
    """Compose new message"""
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            django_messages.success(request, "Message sent!")
            return redirect('messages:inbox')
    else:
        form = MessageForm()
    
    return render(request, 'messages/compose.html', {'form': form})


@login_required
def announcements(request):
    """View announcements"""
    all_announcements = Announcement.objects.filter(is_published=True).order_by('-publish_date')
    return render(request, 'messages/announcements.html', {'announcements': all_announcements})