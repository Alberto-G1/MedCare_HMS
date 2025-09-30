from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class SystemLog(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('STATUS', 'Status Change'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('READ', 'Read/View'),
        ('OTHER', 'Other'),
    )
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='system_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_model = models.CharField(max_length=100)
    target_id = models.CharField(max_length=100, blank=True, null=True)
    summary = models.CharField(max_length=255)
    details = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    correlation_id = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['target_model','target_id']),
            models.Index(fields=['action']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.action} {self.target_model} {self.target_id} by {self.actor}"