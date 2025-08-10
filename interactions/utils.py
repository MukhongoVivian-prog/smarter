from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging

logger = logging.getLogger(__name__)

def send_notification_to_user(user_id, title, body, notification_type='general', data=None, notification_id=None):
    """
    Send real-time notification to a specific user via WebSocket
    
    Args:
        user_id: ID of the user to notify
        title: Notification title
        body: Notification body/message
        notification_type: Type of notification (booking, message, maintenance, etc.)
        data: Additional data payload
        notification_id: Database notification ID if applicable
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("Channel layer not configured - real-time notifications disabled")
            return
            
        payload = {
            "type": "notify",
            "title": title,
            "body": body,
            "notification_type": notification_type,
            "timestamp": json.dumps({"timestamp": "now"}, cls=DjangoJSONEncoder),
            "data": data or {}
        }
        
        if notification_id:
            payload["notification_id"] = notification_id
        
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            payload
        )
        
        logger.info(f"Sent notification to user {user_id}: {title}")
        
    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {str(e)}")

def send_chat_message_to_participants(message_instance):
    """
    Send real-time chat message to all participants
    
    Args:
        message_instance: Message model instance
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("Channel layer not configured - real-time chat disabled")
            return
            
        # Determine participants
        participants = [message_instance.sender.id, message_instance.recipient.id]
        
        payload = {
            "type": "chat_message",
            "message_id": message_instance.id,
            "sender_id": message_instance.sender.id,
            "sender_name": message_instance.sender.username,
            "recipient_id": message_instance.recipient.id,
            "content": message_instance.content,
            "timestamp": json.dumps({"timestamp": message_instance.created_at}, cls=DjangoJSONEncoder),
            "property_id": message_instance.property.id if message_instance.property else None
        }
        
        # Send to both participants
        for participant_id in participants:
            async_to_sync(channel_layer.group_send)(
                f"user_{participant_id}",
                payload
            )
            
        logger.info(f"Sent chat message {message_instance.id} to participants: {participants}")
        
    except Exception as e:
        logger.error(f"Failed to send chat message {message_instance.id}: {str(e)}")

def broadcast_booking_update(booking_instance, action):
    """
    Broadcast booking updates to relevant users
    
    Args:
        booking_instance: BookingRequest model instance
        action: The action performed (created, approved, declined, etc.)
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
            
        payload = {
            "type": "booking_update",
            "booking_id": booking_instance.id,
            "action": action,
            "status": booking_instance.status,
            "property_id": booking_instance.property.id,
            "property_title": booking_instance.property.title,
            "tenant_id": booking_instance.tenant.id,
            "landlord_id": booking_instance.property.owner.id,
            "timestamp": json.dumps({"timestamp": "now"}, cls=DjangoJSONEncoder)
        }
        
        # Send to tenant and landlord
        participants = [booking_instance.tenant.id, booking_instance.property.owner.id]
        for participant_id in participants:
            async_to_sync(channel_layer.group_send)(
                f"user_{participant_id}",
                payload
            )
            
        logger.info(f"Broadcast booking update {booking_instance.id} action '{action}' to participants: {participants}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast booking update {booking_instance.id}: {str(e)}")

def get_user_unread_count(user_id):
    """Get unread notification count for a user"""
    from .models import Notification
    try:
        return Notification.objects.filter(user_id=user_id, is_read=False).count()
    except Exception as e:
        logger.error(f"Failed to get unread count for user {user_id}: {str(e)}")
        return 0
