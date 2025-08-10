# interactions/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
            
        # Join user-specific group
        self.user_group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation and current status
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'user_id': self.user.id,
            'username': self.user.username,
            'timestamp': timezone.now().isoformat()
        }, cls=DjangoJSONEncoder))
        
        # Send current unread count on connect
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))
        
        logger.info(f"User {self.user.id} connected to notifications WebSocket")

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        logger.info(f"User {self.user.id} disconnected from notifications WebSocket")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    success = await self.mark_notification_read(notification_id)
                    await self.send(text_data=json.dumps({
                        'type': 'mark_read_response',
                        'notification_id': notification_id,
                        'success': success
                    }))
                    
            elif message_type == 'mark_all_read':
                count = await self.mark_all_notifications_read()
                await self.send(text_data=json.dumps({
                    'type': 'mark_all_read_response',
                    'marked_count': count
                }))
                
            elif message_type == 'get_unread_count':
                unread_count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': unread_count
                }))
                
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }, cls=DjangoJSONEncoder))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error handling WebSocket message from user {self.user.id}: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))

    # Group message handlers
    async def notify(self, event):
        """Handle notification messages"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event['title'],
            'body': event['body'],
            'notification_type': event.get('notification_type', 'general'),
            'data': event.get('data', {}),
            'notification_id': event.get('notification_id'),
            'timestamp': timezone.now().isoformat()
        }, cls=DjangoJSONEncoder))
        
        # Send updated unread count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))

    async def chat_message(self, event):
        """Handle chat message broadcasts"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'recipient_id': event['recipient_id'],
            'content': event['content'],
            'timestamp': event['timestamp'],
            'property_id': event.get('property_id')
        }))

    async def booking_update(self, event):
        """Handle booking update broadcasts"""
        await self.send(text_data=json.dumps({
            'type': 'booking_update',
            'booking_id': event['booking_id'],
            'action': event['action'],
            'status': event['status'],
            'property_id': event['property_id'],
            'property_title': event['property_title'],
            'tenant_id': event['tenant_id'],
            'landlord_id': event['landlord_id'],
            'timestamp': timezone.now().isoformat()
        }, cls=DjangoJSONEncoder))

    @database_sync_to_async
    def get_unread_count(self):
        from .models import Notification
        return Notification.objects.filter(user=self.user, is_read=False).count()

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        from .models import Notification
        try:
            notification = Notification.objects.get(id=notification_id, user=self.user)
                id=notification_id,
                user_id=self.user_id
            )
            notification.is_read = True
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False

    @database_sync_to_async
    def get_user_notifications(self):
        notifications = Notification.objects.filter(
            user_id=self.user_id
        ).order_by('-created_at')[:20]  # Last 20 notifications
        
        return [
            {
                'id': notif.id,
                'title': notif.title,
                'body': notif.body,
                'is_read': notif.is_read,
                'notification_type': notif.notification_type,
                'created_at': notif.created_at.isoformat(),
                'data': notif.data
            }
            for notif in notifications
        ]
