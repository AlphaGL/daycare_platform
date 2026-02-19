"""
Notifications / Messaging Views - FIXED & ENHANCED
- Added: unread_count API endpoint (used by base.html JS)
- Added: announcement creation view
- Added: reply to message
- Fixed: import clash between django.messages and notifications.models.Message
- Added: email notifications when a message is sent
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Message, Announcement
from .forms import MessageForm, AnnouncementForm
import threading


def _send_async(fn, *args):
    threading.Thread(target=fn, args=args, daemon=True).start()


def is_staff_or_admin(user):
    return user.is_authenticated and (user.is_admin or user.is_staff_member)


# ── INBOX ────────────────────────────────────────────────────────────────────

@login_required
def inbox(request):
    """User inbox"""
    inbox_messages = Message.objects.filter(
        recipient=request.user,
        is_archived=False,
        parent_message__isnull=True   # Only show root messages, not replies
    ).select_related('sender').order_by('-created_at')

    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()

    return render(request, 'notifications/inbox.html', {
        'messages': inbox_messages,
        'unread_count': unread_count,
    })


# ── MESSAGE DETAIL ────────────────────────────────────────────────────────────

@login_required
def message_detail(request, pk):
    """View message thread and allow reply"""
    message = get_object_or_404(Message, pk=pk)

    # Only sender or recipient may view
    if message.sender != request.user and message.recipient != request.user:
        django_messages.error(request, "You don't have permission to view this message.")
        return redirect('messages:inbox')

    # Mark as read for the recipient
    if message.recipient == request.user:
        message.mark_as_read()

    # Get the full thread
    thread = message.get_thread()

    # Reply form
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            reply = Message.objects.create(
                sender=request.user,
                recipient=message.sender if request.user == message.recipient else message.recipient,
                subject=f"Re: {message.subject}" if message.subject else '',
                body=body,
                parent_message=message,
            )
            # Email notification for new reply
            try:
                from notifications_service.email_service import send_notification_email
                from django.conf import settings
                recipient = reply.recipient
                _send_async(
                    send_notification_email,
                    recipient.email,
                    f"New reply from {request.user.get_full_name()} – {settings.SITE_NAME}",
                    f"Hi {recipient.get_full_name()},\n\n"
                    f"{request.user.get_full_name()} replied to your message:\n\n"
                    f"\"{body[:200]}{'...' if len(body) > 200 else ''}\"\n\n"
                    f"Log in to view the full conversation: {settings.SITE_URL}/messages/{message.pk}/\n\n"
                    f"Regards,\n{settings.SITE_NAME}",
                )
            except Exception:
                pass

            django_messages.success(request, "Reply sent!")
            return redirect('messages:detail', pk=pk)

    return render(request, 'notifications/message_detail.html', {
        'message': message,
        'thread': thread,
    })


# ── COMPOSE ───────────────────────────────────────────────────────────────────

@login_required
def compose_message(request):
    """Compose and send a new message"""
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.save()

            # Email notification to recipient
            try:
                from notifications_service.email_service import send_notification_email
                from django.conf import settings
                recipient = msg.recipient
                _send_async(
                    send_notification_email,
                    recipient.email,
                    f"New message from {request.user.get_full_name()} – {settings.SITE_NAME}",
                    f"Hi {recipient.get_full_name()},\n\n"
                    f"You have a new message from {request.user.get_full_name()}.\n\n"
                    f"Subject: {msg.subject or '(No subject)'}\n\n"
                    f"Log in to read it: {settings.SITE_URL}/messages/{msg.pk}/\n\n"
                    f"Regards,\n{settings.SITE_NAME}",
                )
            except Exception:
                pass

            django_messages.success(request, "✅ Message sent successfully!")
            return redirect('messages:inbox')
    else:
        # Pre-fill recipient if passed via query string
        initial = {}
        recipient_id = request.GET.get('to')
        if recipient_id:
            initial['recipient'] = recipient_id
        form = MessageForm(initial=initial)

    return render(request, 'notifications/compose.html', {'form': form})


# ── ANNOUNCEMENTS ─────────────────────────────────────────────────────────────

@login_required
def announcements(request):
    """View announcements relevant to the current user"""
    if request.user.is_admin or request.user.is_staff_member:
        audience_filter = ['ALL', 'STAFF', 'PARENTS', 'ROOM_SPECIFIC']
    else:
        audience_filter = ['ALL', 'PARENTS']

    all_announcements = Announcement.objects.filter(
        is_published=True,
        target_audience__in=audience_filter
    ).select_related('created_by').order_by('-is_pinned', '-publish_date')

    return render(request, 'notifications/announcements.html', {
        'announcements': all_announcements,
    })


@login_required
@user_passes_test(is_staff_or_admin)
def announcement_create(request):
    """Create a new announcement (staff/admin only)"""
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()

            # Send email if requested
            if announcement.send_email and not announcement.email_sent:
                try:
                    _send_async(_email_announcement, announcement)
                    announcement.email_sent = True
                    announcement.save(update_fields=['email_sent'])
                except Exception:
                    pass

            django_messages.success(request, f"📢 Announcement '{announcement.title}' published!")
            return redirect('messages:announcements')
    else:
        form = AnnouncementForm()

    return render(request, 'notifications/announcement_form.html', {'form': form})


def _email_announcement(announcement):
    """Send announcement email to the target audience."""
    from accounts.models import User
    from notifications_service.email_service import send_notification_email
    from django.conf import settings

    if announcement.target_audience == 'ALL':
        recipients = User.objects.filter(is_active=True).exclude(email='')
    elif announcement.target_audience == 'PARENTS':
        recipients = User.objects.filter(role=User.Role.PARENT, is_active=True).exclude(email='')
    elif announcement.target_audience == 'STAFF':
        recipients = User.objects.filter(
            role__in=[User.Role.STAFF, User.Role.ADMIN], is_active=True
        ).exclude(email='')
    else:
        return

    priority_label = {
        'LOW': '📋',
        'NORMAL': '📣',
        'HIGH': '⚠️',
        'URGENT': '🚨',
    }.get(announcement.priority, '📣')

    subject = f"{priority_label} {announcement.title} – {settings.SITE_NAME}"
    for user in recipients:
        text_body = (
            f"Hi {user.get_full_name()},\n\n"
            f"{announcement.content}\n\n"
            f"View on the portal: {settings.SITE_URL}/messages/announcements/\n\n"
            f"Regards,\n{settings.SITE_NAME}"
        )
        try:
            send_notification_email(user.email, subject, text_body)
        except Exception:
            pass


# ── UNREAD COUNT API (used by base.html JS) ───────────────────────────────────

@login_required
def unread_count(request):
    """Returns JSON unread message count – called by base.html every 30s"""
    count = Message.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


# ── MARK ALL READ ──────────────────────────────────────────────────────────────

@login_required
def mark_all_read(request):
    """Mark all messages as read"""
    if request.method == 'POST':
        Message.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
        django_messages.success(request, "All messages marked as read.")
    return redirect('messages:inbox')