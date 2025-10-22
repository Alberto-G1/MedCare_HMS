from django.contrib import admin
from .models import Thread, ChatMessage, UserPresence, CannedResponse

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ['id', 'created', 'updated', 'participant_count']
    list_filter = ['created', 'updated']
    search_fields = ['participants__username', 'participants__email']
    
    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'thread', 'is_read', 'timestamp', 'has_attachment']
    list_filter = ['is_read', 'timestamp', 'attachment_type']
    search_fields = ['sender__username', 'message']
    readonly_fields = ['timestamp', 'read_at']
    
    def has_attachment(self, obj):
        return bool(obj.attachment)
    has_attachment.boolean = True
    has_attachment.short_description = 'Attachment'


@admin.register(UserPresence)
class UserPresenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_online', 'last_seen']
    list_filter = ['is_online', 'last_seen']
    search_fields = ['user__username', 'user__email']


@admin.register(CannedResponse)
class CannedResponseAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'message', 'created_by__username']
    readonly_fields = ['created_at']
