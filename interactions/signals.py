# interactions/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import BookingRequest, Message, MaintenanceRequest, Review, Favorite, Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .utils import send_notification_to_user, send_chat_message_to_participants, broadcast_booking_update
from users.email_utils import (
    send_booking_notification_email, 
    send_maintenance_notification_email,
    send_welcome_email
)
from datetime import datetime

def create_notification(user, title, body, notification_type='general', data=None):
    """Helper function to create notification and send real-time update"""
    notification = Notification.objects.create(
        user=user,
        title=title,
        body=body,
        notification_type=notification_type,
        data=data or {}
    )
    
    # Send real-time notification with enhanced payload
    send_notification_to_user(
        user_id=user.id,
        title=title,
        body=body,
        notification_type=notification_type,
        data=data or {},
        notification_id=notification.id
    )
    
    return notification

@receiver(post_save, sender=BookingRequest)
def booking_request_notification(sender, instance, created, **kwargs):
    """Handle booking request creation and status updates"""
    from django.utils import timezone
    
    if created:
        # Notify landlord of new booking request
        create_notification(
            user=instance.property.owner,
            title="New Booking Request",
            body=f"{instance.tenant.username} requested to book {instance.property.title}",
            notification_type='booking',
            data={
                'booking_id': instance.id,
                'property_id': instance.property.id,
                'tenant_id': instance.tenant.id,
                'status': instance.status,
                'check_in_date': instance.check_in_date.isoformat() if instance.check_in_date else None,
                'check_out_date': instance.check_out_date.isoformat() if instance.check_out_date else None
            }
        )
        # Send email notification
        send_booking_notification_email(instance, 'created')
        
        # Broadcast booking update
        broadcast_booking_update(instance, 'created')
    else:
        # Handle status changes and update timestamps
        if instance.status == 'approved' and not instance.approved_at:
            instance.approved_at = timezone.now()
            instance.save(update_fields=['approved_at'])
        elif instance.status == 'checked_in' and not instance.checked_in_at:
            instance.checked_in_at = timezone.now()
            instance.save(update_fields=['checked_in_at'])
        elif instance.status == 'completed' and not instance.completed_at:
            instance.completed_at = timezone.now()
            instance.save(update_fields=['completed_at'])
        
        # Status change notifications
        status_messages = {
            'approved': f"Great news! Your booking request for {instance.property.title} has been approved!",
            'declined': f"Your booking request for {instance.property.title} was declined.",
            'checked_in': f"You have successfully checked in to {instance.property.title}. Enjoy your stay!",
            'completed': f"Your booking at {instance.property.title} has been completed. Thank you for choosing us!",
            'cancelled': f"Your booking for {instance.property.title} has been cancelled."
        }
        
        # Determine notification recipient based on status
        if instance.status in ['approved', 'declined']:
            # Notify tenant of landlord's decision
            recipient = instance.tenant
        elif instance.status in ['checked_in', 'completed', 'cancelled']:
            # Notify landlord of tenant's action
            recipient = instance.property.owner
        else:
            recipient = None
            
        if recipient and instance.status in status_messages:
            create_notification(
                user=recipient,
                title="Booking Update",
                body=status_messages[instance.status],
                notification_type='booking',
                data={
                    'booking_id': instance.id,
                    'property_id': instance.property.id,
                    'status': instance.status,
                    'tenant_id': instance.tenant.id,
                    'landlord_id': instance.property.owner.id
                }
            )
            
            # Send email notification for key status changes
            if instance.status in ['approved', 'declined', 'checked_in', 'completed']:
                send_booking_notification_email(instance, instance.status)
            
            # Broadcast booking status update
            broadcast_booking_update(instance, instance.status)

@receiver(post_save, sender=Message)
def message_notification(sender, instance, created, **kwargs):
    """Handle new message notifications and real-time chat"""
    if created:
        # Send real-time chat message to participants
        send_chat_message_to_participants(instance)
        
        # Create notification for recipient
        create_notification(
            user=instance.recipient,
            title="New Message",
            body=f"You have a new message from {instance.sender.username}",
            notification_type='message',
            data={
                'message_id': instance.id,
                'sender_id': instance.sender.id,
                'sender_name': instance.sender.username,
                'property_id': instance.property.id if instance.property else None,
                'content_preview': instance.content[:100] + '...' if len(instance.content) > 100 else instance.content
            }
        )

@receiver(post_save, sender=MaintenanceRequest)
def maintenance_request_notification(sender, instance, created, **kwargs):
    """Handle maintenance request notifications"""
    if created:
        # Notify landlord of new maintenance request
        create_notification(
            user=instance.property.owner,
            title="New Maintenance Request",
            body=f"Maintenance request for {instance.property.title}: {instance.description[:100]}{'...' if len(instance.description) > 100 else ''}",
            notification_type='maintenance',
            data={
                'maintenance_id': instance.id,
                'property_id': instance.property.id,
                'tenant_id': instance.tenant.id,
                'status': instance.status
            }
        )
        # Send email notification
        send_maintenance_notification_email(instance, 'created')
    else:
        # Status change - notify tenant
        status_messages = {
            'in_progress': f"Your maintenance request for {instance.property.title} is now in progress.",
            'resolved': f"Your maintenance request for {instance.property.title} has been resolved.",
            'open': f"Your maintenance request for {instance.property.title} is open."
        }
        
        if instance.status in status_messages:
            create_notification(
                user=instance.tenant,
                title="Maintenance Update",
                body=status_messages[instance.status],
                notification_type='maintenance',
                data={
                    'maintenance_id': instance.id,
                    'property_id': instance.property.id,
                    'status': instance.status
                }
            )
            # Send email notification for status changes
            if instance.status in ['in_progress', 'resolved']:
                send_maintenance_notification_email(instance, instance.status)

@receiver(post_save, sender=Review)
def review_notification(sender, instance, created, **kwargs):
    """Handle new review notifications"""
    if created:
        # Notify landlord of new review
        create_notification(
            user=instance.property.owner,
            title="New Property Review",
            body=f"{instance.tenant.username} left a {instance.rating}-star review for {instance.property.title}",
            notification_type='review',
            data={
                'review_id': instance.id,
                'property_id': instance.property.id,
                'tenant_id': instance.tenant.id,
                'rating': instance.rating
            }
        )

@receiver(post_save, sender=Favorite)
def favorite_notification(sender, instance, created, **kwargs):
    """Handle property favorite notifications"""
    if created:
        # Notify landlord when someone favorites their property
        create_notification(
            user=instance.property.owner,
            title="Property Favorited",
            body=f"{instance.tenant.username} added {instance.property.title} to their favorites",
            notification_type='property',
            data={
                'property_id': instance.property.id,
                'tenant_id': instance.tenant.id
            }
        )
