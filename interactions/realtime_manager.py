"""
Real-time Notification Manager for SmartHunt

This module provides centralized management for real-time notifications,
WebSocket connections, and event broadcasting across the platform.
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.contrib.auth import get_user_model
import json
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class RealtimeNotificationManager:
    """Centralized manager for real-time notifications and WebSocket events"""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
        
    def is_available(self):
        """Check if real-time notifications are available"""
        return self.channel_layer is not None
    
    def send_to_user(self, user_id, event_type, payload):
        """Send event to specific user"""
        if not self.is_available():
            logger.warning("Channel layer not configured - real-time disabled")
            return False
            
        try:
            async_to_sync(self.channel_layer.group_send)(
                f"user_{user_id}",
                {
                    "type": event_type,
                    **payload
                }
            )
            logger.info(f"Sent {event_type} to user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send {event_type} to user {user_id}: {str(e)}")
            return False
    
    def send_to_multiple_users(self, user_ids, event_type, payload):
        """Send event to multiple users"""
        success_count = 0
        for user_id in user_ids:
            if self.send_to_user(user_id, event_type, payload):
                success_count += 1
        return success_count
    
    def broadcast_notification(self, user_id, title, body, notification_type='general', data=None, notification_id=None):
        """Broadcast notification to user"""
        payload = {
            "title": title,
            "body": body,
            "notification_type": notification_type,
            "data": data or {},
            "notification_id": notification_id,
            "timestamp": timezone.now().isoformat()
        }
        return self.send_to_user(user_id, "notify", payload)
    
    def broadcast_chat_message(self, participants, message_data):
        """Broadcast chat message to participants"""
        payload = {
            "message_id": message_data.get('id'),
            "sender_id": message_data.get('sender_id'),
            "sender_name": message_data.get('sender_name'),
            "recipient_id": message_data.get('recipient_id'),
            "content": message_data.get('content'),
            "timestamp": message_data.get('timestamp'),
            "property_id": message_data.get('property_id')
        }
        return self.send_to_multiple_users(participants, "chat_message", payload)
    
    def broadcast_booking_update(self, participants, booking_data):
        """Broadcast booking update to participants"""
        payload = {
            "booking_id": booking_data.get('id'),
            "action": booking_data.get('action'),
            "status": booking_data.get('status'),
            "property_id": booking_data.get('property_id'),
            "property_title": booking_data.get('property_title'),
            "tenant_id": booking_data.get('tenant_id'),
            "landlord_id": booking_data.get('landlord_id'),
            "timestamp": timezone.now().isoformat()
        }
        return self.send_to_multiple_users(participants, "booking_update", payload)
    
    def broadcast_maintenance_update(self, participants, maintenance_data):
        """Broadcast maintenance update to participants"""
        payload = {
            "maintenance_id": maintenance_data.get('id'),
            "action": maintenance_data.get('action'),
            "status": maintenance_data.get('status'),
            "property_id": maintenance_data.get('property_id'),
            "tenant_id": maintenance_data.get('tenant_id'),
            "landlord_id": maintenance_data.get('landlord_id'),
            "timestamp": timezone.now().isoformat()
        }
        return self.send_to_multiple_users(participants, "maintenance_update", payload)
    
    def get_active_connections_count(self):
        """Get count of active WebSocket connections (requires Redis inspection)"""
        # This would require Redis inspection - placeholder for monitoring
        return "Not implemented - requires Redis monitoring"

# Global instance
realtime_manager = RealtimeNotificationManager()

class WebSocketHealthChecker:
    """Health checker for WebSocket functionality"""
    
    @staticmethod
    def check_channel_layer():
        """Check if channel layer is properly configured"""
        channel_layer = get_channel_layer()
        if not channel_layer:
            return {
                "status": "error",
                "message": "Channel layer not configured"
            }
        
        try:
            # Test basic channel layer functionality
            async_to_sync(channel_layer.group_send)(
                "test_group",
                {"type": "test_message", "data": "health_check"}
            )
            return {
                "status": "ok",
                "message": "Channel layer working"
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Channel layer error: {str(e)}"
            }
    
    @staticmethod
    def check_redis_connection():
        """Check Redis connection for Channels"""
        try:
            import redis
            from django.conf import settings
            
            # Get Redis config from Channels
            channel_layers = getattr(settings, 'CHANNEL_LAYERS', {})
            default_config = channel_layers.get('default', {})
            
            if default_config.get('BACKEND') == 'channels_redis.core.RedisChannelLayer':
                redis_config = default_config.get('CONFIG', {})
                hosts = redis_config.get('hosts', [('127.0.0.1', 6379)])
                
                # Test connection to first host
                if hosts:
                    host, port = hosts[0] if isinstance(hosts[0], tuple) else (hosts[0], 6379)
                    r = redis.Redis(host=host, port=port, decode_responses=True)
                    r.ping()
                    
                    return {
                        "status": "ok",
                        "message": f"Redis connected at {host}:{port}"
                    }
            
            return {
                "status": "warning",
                "message": "Redis not configured for Channels"
            }
            
        except ImportError:
            return {
                "status": "error",
                "message": "Redis package not installed"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Redis connection failed: {str(e)}"
            }
    
    @staticmethod
    def run_health_check():
        """Run comprehensive health check"""
        print("🏥 Running WebSocket Health Check...")
        
        # Check channel layer
        channel_result = WebSocketHealthChecker.check_channel_layer()
        print(f"📡 Channel Layer: {channel_result['status']} - {channel_result['message']}")
        
        # Check Redis
        redis_result = WebSocketHealthChecker.check_redis_connection()
        print(f"🔴 Redis: {redis_result['status']} - {redis_result['message']}")
        
        # Overall status
        overall_status = "ok" if all(
            result['status'] == 'ok' 
            for result in [channel_result, redis_result]
        ) else "error"
        
        print(f"🎯 Overall WebSocket Status: {overall_status}")
        
        return {
            "overall": overall_status,
            "channel_layer": channel_result,
            "redis": redis_result
        }

def test_realtime_system():
    """
    Quick test function for real-time system
    
    Usage:
        python manage.py shell
        >>> from interactions.realtime_manager import test_realtime_system
        >>> test_realtime_system()
    """
    print("🔧 Testing Real-time System...")
    
    # Run health check
    health_status = WebSocketHealthChecker.run_health_check()
    
    if health_status['overall'] != 'ok':
        print("❌ Real-time system not ready. Please check configuration.")
        return False
    
    # Test notification manager
    manager = RealtimeNotificationManager()
    
    if not manager.is_available():
        print("❌ Notification manager not available")
        return False
    
    print("✅ Real-time system is ready!")
    print("💡 To test WebSocket connections, use the WebSocketTestSuite class")
    return True
