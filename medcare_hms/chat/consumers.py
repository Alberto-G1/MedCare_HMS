import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Thread, ChatMessage
from django.contrib.auth.models import User

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
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.thread_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive_json(self, content):
        message = content['message']
        
        # Save message to database
        new_message = await self.save_message(message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.thread_group_name,
            {
                'type': 'chat_message',
                'message': new_message.message,
                'sender': new_message.sender.username
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send_json({
            'message': event['message'],
            'sender': event['sender']
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