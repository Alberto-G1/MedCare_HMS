from django.db import models
from django.contrib.auth.models import User

class Thread(models.Model):
    participants = models.ManyToManyField(User, related_name='chat_threads')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Thread ({self.pk}) with {self.participants.count()} participants"
    
    def get_unread_count_for_user(self, user):
        """Get count of unread messages for a specific user in this thread"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()

class ChatMessage(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # File/Image attachment support
    attachment = models.FileField(upload_to='chat_attachments/%Y/%m/%d/', null=True, blank=True)
    attachment_type = models.CharField(max_length=20, null=True, blank=True)  # 'image', 'document', 'other'
    
    # Optional link to appointment for context
    appointment = models.ForeignKey(
        'patients.Appointment', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='chat_messages'
    )

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender.username} in Thread ({self.thread.pk})"
    
    def mark_as_read(self):
        """Mark this message as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class UserPresence(models.Model):
    """Track online/offline status of users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='presence')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {'Online' if self.is_online else 'Offline'}"


class CannedResponse(models.Model):
    """Pre-defined quick reply templates for staff"""
    title = models.CharField(max_length=100)
    message = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['title']
    
    def __str__(self):
        return self.title