from django.db import models
from django.contrib.auth.models import User

class Thread(models.Model):
    participants = models.ManyToManyField(User, related_name='chat_threads')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Thread ({self.pk}) with {self.participants.count()} participants"

class ChatMessage(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} in Thread ({self.thread.pk})"