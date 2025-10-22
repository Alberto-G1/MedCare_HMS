import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Thread, ChatMessage, UserPresence
from django.contrib.auth.models import User
from notifications.utils import create_notification
from django.urls import reverse

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.thread_group_name = f'chat_{self.thread_id}'
        self.user = self.scope['user']

        # Security check: Ensure user is authenticated and part of the thread
        if not self.user.is_authenticated or not await self.is_user_in_thread():
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.thread_group_name,
            self.channel_name
        )
        
        # Set user as online
        await self.set_user_online(True)
        
        # Mark all unread messages as read when user enters the chat
        await self.mark_messages_as_read()
        
        await self.accept()
        
        # Notify other participants that user is online
        await self.channel_layer.group_send(
            self.thread_group_name,
            {
                'type': 'user_status',
                'user': self.user.username,
                'status': 'online'
            }
        )

    async def disconnect(self, close_code):
        # Set user as offline
        await self.set_user_online(False)
        
        # Notify other participants that user is offline
        await self.channel_layer.group_send(
            self.thread_group_name,
            {
                'type': 'user_status',
                'user': self.user.username,
                'status': 'offline'
            }
        )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.thread_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive_json(self, content):
        message_type = content.get('type', 'message')
        
        if message_type == 'typing':
            # Handle typing indicator
            await self.channel_layer.group_send(
                self.thread_group_name,
                {
                    'type': 'typing_indicator',
                    'user': self.user.username,
                    'is_typing': content.get('is_typing', False)
                }
            )
        
        elif message_type == 'read_receipt':
            # Handle read receipt
            message_id = content.get('message_id')
            await self.mark_message_read(message_id)
            
            await self.channel_layer.group_send(
                self.thread_group_name,
                {
                    'type': 'read_receipt_update',
                    'message_id': message_id,
                    'read_by': self.user.username
                }
            )
        
        elif message_type == 'message':
            message = content['message']
            
            # Save message to database
            new_message = await self.save_message(message)

            # Get sender's profile picture
            sender_avatar = await self.get_sender_avatar()

            # --- NOTIFICATION LOGIC ---
            await self.notify_other_participants(new_message)
            # --- END NOTIFICATION LOGIC ---
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.thread_group_name,
                {
                    'type': 'chat_message',
                    'message_id': new_message.id,
                    'message': new_message.message,
                    'sender': new_message.sender.username,
                    'sender_name': new_message.sender.get_full_name(),
                    'sender_avatar': sender_avatar,
                    'timestamp': new_message.timestamp.isoformat(),
                    'is_read': new_message.is_read
                }
            )

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send_json({
            'type': 'message',
            'message_id': event['message_id'],
            'message': event['message'],
            'sender': event['sender'],
            'sender_name': event['sender_name'],
            'sender_avatar': event['sender_avatar'],
            'timestamp': event['timestamp'],
            'is_read': event['is_read']
        })
    
    # Handle typing indicator
    async def typing_indicator(self, event):
        # Don't send typing indicator back to the person who is typing
        if event['user'] != self.user.username:
            await self.send_json({
                'type': 'typing',
                'user': event['user'],
                'is_typing': event['is_typing']
            })
    
    # Handle user status updates
    async def user_status(self, event):
        # Don't send status update to the user themselves
        if event['user'] != self.user.username:
            await self.send_json({
                'type': 'status',
                'user': event['user'],
                'status': event['status']
            })
    
    # Handle read receipt updates
    async def read_receipt_update(self, event):
        await self.send_json({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'read_by': event['read_by']
        })

    @database_sync_to_async
    def is_user_in_thread(self):
        try:
            thread = Thread.objects.get(pk=self.thread_id)
            return self.user in thread.participants.all()
        except Thread.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, message_text):
        thread = Thread.objects.get(pk=self.thread_id)
        return ChatMessage.objects.create(thread=thread, sender=self.user, message=message_text)
    
    @database_sync_to_async
    def set_user_online(self, is_online):
        """Set user's online/offline status"""
        presence, created = UserPresence.objects.get_or_create(user=self.user)
        presence.is_online = is_online
        presence.save()
    
    @database_sync_to_async
    def mark_messages_as_read(self):
        """Mark all unread messages in this thread as read for the current user"""
        thread = Thread.objects.get(pk=self.thread_id)
        unread_messages = thread.messages.filter(is_read=False).exclude(sender=self.user)
        
        from django.utils import timezone
        for message in unread_messages:
            message.is_read = True
            message.read_at = timezone.now()
        
        ChatMessage.objects.bulk_update(unread_messages, ['is_read', 'read_at'])
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark a specific message as read"""
        try:
            message = ChatMessage.objects.get(id=message_id)
            if message.sender != self.user:
                message.mark_as_read()
        except ChatMessage.DoesNotExist:
            pass
    
    @database_sync_to_async
    def get_sender_avatar(self):
        """Get the sender's profile picture URL"""
        user = self.user
        try:
            if hasattr(user, 'doctorprofile') and user.doctorprofile.profile_picture:
                return user.doctorprofile.profile_picture.url
            elif hasattr(user, 'patientprofile') and user.patientprofile.profile_picture:
                return user.patientprofile.profile_picture.url
            elif hasattr(user, 'receptionistprofile') and user.receptionistprofile.profile_picture:
                return user.receptionistprofile.profile_picture.url
        except:
            pass
        return '/media/profile_pictures/default.jpeg'
    
    # --- NEW ASYNC HELPER METHOD ---
    @database_sync_to_async
    def notify_other_participants(self, new_message):
        thread = new_message.thread
        sender = new_message.sender
        
        # Get all participants in the thread except the sender
        for participant in thread.participants.all():
            if participant != sender:
                message = f"You have a new message from {sender.get_full_name()}."
                link = reverse('chat:thread_detail', kwargs={'thread_id': thread.id})
                create_notification(recipient=participant, message=message, link=link)