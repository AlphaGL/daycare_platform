"""
Messaging System Models
Parent-Staff and Staff-Staff communication
"""
from django.db import models
from accounts.models import User


class Message(models.Model):
    """
    Message model for communication
    Thread-based, refresh mode (not real-time)
    """
    
    # Sender
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    
    # Recipient
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    
    # Content
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    
    # Thread (for replies)
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Flagging
    is_flagged = models.BooleanField(
        default=False,
        help_text="Flag for admin review"
    )
    is_archived = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username} - {self.subject or 'No Subject'}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def get_thread(self):
        """Get full message thread"""
        if self.parent_message:
            # This is a reply, get the root message
            root = self.parent_message
            while root.parent_message:
                root = root.parent_message
            return Message.objects.filter(
                models.Q(id=root.id) | models.Q(parent_message=root)
            ).order_by('created_at')
        else:
            # This is the root message
            return Message.objects.filter(
                models.Q(id=self.id) | models.Q(parent_message=self)
            ).order_by('created_at')


class Announcement(models.Model):
    """
    School-wide announcements
    """
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'
    
    class TargetAudience(models.TextChoices):
        ALL = 'ALL', 'Everyone'
        PARENTS = 'PARENTS', 'Parents Only'
        STAFF = 'STAFF', 'Staff Only'
        ROOM_SPECIFIC = 'ROOM_SPECIFIC', 'Specific Room'
    
    # Author
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='announcements_created',
        limit_choices_to={'role__in': [User.Role.ADMIN, User.Role.STAFF]}
    )
    
    # Content
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    
    # Targeting
    target_audience = models.CharField(
        max_length=20,
        choices=TargetAudience.choices,
        default=TargetAudience.ALL
    )
    target_room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='announcements'
    )
    
    # Publishing
    is_published = models.BooleanField(default=True)
    publish_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    # Email notification
    send_email = models.BooleanField(
        default=False,
        help_text="Send email notification to target audience"
    )
    email_sent = models.BooleanField(default=False)
    
    # Pinned
    is_pinned = models.BooleanField(
        default=False,
        help_text="Pin to top of announcements"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-publish_date']
    
    def __str__(self):
        return f"{self.title} ({self.get_target_audience_display()})"
    
    @property
    def is_active(self):
        """Check if announcement is still active"""
        from django.utils import timezone
        if not self.is_published:
            return False
        if self.expiry_date and timezone.now() > self.expiry_date:
            return False
        return True


class MessageTemplate(models.Model):
    """
    Reusable message templates for staff
    """
    
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    
    # For specific scenarios
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='message_templates'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name