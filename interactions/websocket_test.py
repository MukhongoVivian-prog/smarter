"""
WebSocket Testing Utility for SmartHunt Real-time Notifications

This module provides testing utilities for WebSocket connections,
real-time notifications, and chat functionality.
"""

import asyncio
import websockets
import json
import jwt
from django.conf import settings
from django.test import TestCase
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import path
from .consumers import NotificationConsumer
from .models import Notification, BookingRequest, Message
from properties.models import Property

User = get_user_model()

class WebSocketTestClient:
    """Test client for WebSocket connections"""
    
    def __init__(self, user_id, access_token):
        self.user_id = user_id
        self.access_token = access_token
        self.websocket = None
        
    async def connect(self, host="localhost", port=8000):
        """Connect to WebSocket with JWT authentication"""
        uri = f"ws://{host}:{port}/ws/notifications/?token={self.access_token}"
        
        try:
            self.websocket = await websockets.connect(uri)
            print(f"✅ Connected to WebSocket for user {self.user_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {str(e)}")
            return False
    
    async def send_message(self, message_data):
        """Send message to WebSocket"""
        if not self.websocket:
            raise Exception("WebSocket not connected")
            
        await self.websocket.send(json.dumps(message_data))
        print(f"📤 Sent: {message_data}")
    
    async def receive_message(self, timeout=5):
        """Receive message from WebSocket"""
        if not self.websocket:
            raise Exception("WebSocket not connected")
            
        try:
            message = await asyncio.wait_for(
                self.websocket.recv(), 
                timeout=timeout
            )
            data = json.loads(message)
            print(f"📥 Received: {data}")
            return data
        except asyncio.TimeoutError:
            print("⏰ Timeout waiting for message")
            return None
    
    async def listen_for_notifications(self, duration=30):
        """Listen for notifications for a specified duration"""
        if not self.websocket:
            raise Exception("WebSocket not connected")
            
        print(f"👂 Listening for notifications for {duration} seconds...")
        
        try:
            while True:
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=duration
                )
                data = json.loads(message)
                
                if data.get('type') == 'notification':
                    print(f"🔔 Notification: {data.get('title')} - {data.get('body')}")
                elif data.get('type') == 'chat_message':
                    print(f"💬 Chat: {data.get('sender_name')}: {data.get('content')}")
                elif data.get('type') == 'booking_update':
                    print(f"🏠 Booking Update: {data.get('action')} - Status: {data.get('status')}")
                else:
                    print(f"📨 Message: {data}")
                    
        except asyncio.TimeoutError:
            print("⏰ Listening timeout reached")
        except websockets.exceptions.ConnectionClosed:
            print("🔌 WebSocket connection closed")
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            print(f"🔌 Disconnected from WebSocket")

class WebSocketTestSuite:
    """Comprehensive WebSocket test suite"""
    
    @staticmethod
    def generate_jwt_token(user):
        """Generate JWT token for testing"""
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken.for_user(user)
        return str(token)
    
    @staticmethod
    async def test_notification_flow(tenant_user, landlord_user, property_obj):
        """Test complete notification flow for booking request"""
        print("\n🧪 Testing Notification Flow...")
        
        # Generate tokens
        tenant_token = WebSocketTestSuite.generate_jwt_token(tenant_user)
        landlord_token = WebSocketTestSuite.generate_jwt_token(landlord_user)
        
        # Create WebSocket clients
        tenant_client = WebSocketTestClient(tenant_user.id, tenant_token)
        landlord_client = WebSocketTestClient(landlord_user.id, landlord_token)
        
        try:
            # Connect both clients
            await tenant_client.connect()
            await landlord_client.connect()
            
            # Test ping/pong
            await tenant_client.send_message({"type": "ping"})
            response = await tenant_client.receive_message()
            assert response.get('type') == 'pong', "Ping/pong test failed"
            print("✅ Ping/pong test passed")
            
            # Create booking request (this should trigger notifications)
            booking = BookingRequest.objects.create(
                tenant=tenant_user,
                property=property_obj,
                message="Test booking request",
                check_in_date="2024-01-15",
                check_out_date="2024-01-20"
            )
            
            # Landlord should receive notification
            landlord_notification = await landlord_client.receive_message(timeout=3)
            assert landlord_notification.get('type') == 'notification', "Landlord didn't receive booking notification"
            print("✅ Landlord received booking request notification")
            
            # Test booking approval
            booking.status = 'approved'
            booking.save()
            
            # Tenant should receive approval notification
            tenant_notification = await tenant_client.receive_message(timeout=3)
            assert tenant_notification.get('type') == 'notification', "Tenant didn't receive approval notification"
            print("✅ Tenant received booking approval notification")
            
            # Test unread count
            await tenant_client.send_message({"type": "get_unread_count"})
            unread_response = await tenant_client.receive_message()
            assert unread_response.get('type') == 'unread_count', "Unread count test failed"
            print(f"✅ Unread count: {unread_response.get('count')}")
            
            print("🎉 All notification tests passed!")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
        finally:
            await tenant_client.disconnect()
            await landlord_client.disconnect()
    
    @staticmethod
    async def test_chat_flow(user1, user2, property_obj):
        """Test real-time chat functionality"""
        print("\n💬 Testing Chat Flow...")
        
        # Generate tokens
        user1_token = WebSocketTestSuite.generate_jwt_token(user1)
        user2_token = WebSocketTestSuite.generate_jwt_token(user2)
        
        # Create WebSocket clients
        client1 = WebSocketTestClient(user1.id, user1_token)
        client2 = WebSocketTestClient(user2.id, user2_token)
        
        try:
            # Connect both clients
            await client1.connect()
            await client2.connect()
            
            # Create a message (this should trigger real-time chat)
            message = Message.objects.create(
                sender=user1,
                recipient=user2,
                content="Hello! I'm interested in your property.",
                property=property_obj
            )
            
            # Both users should receive the chat message
            chat_msg1 = await client1.receive_message(timeout=3)
            chat_msg2 = await client2.receive_message(timeout=3)
            
            assert chat_msg1.get('type') == 'chat_message', "User1 didn't receive chat message"
            assert chat_msg2.get('type') == 'chat_message', "User2 didn't receive chat message"
            
            print("✅ Real-time chat messages delivered to both participants")
            print("🎉 Chat flow test passed!")
            
        except Exception as e:
            print(f"❌ Chat test failed: {str(e)}")
        finally:
            await client1.disconnect()
            await client2.disconnect()

def run_websocket_tests():
    """
    Run comprehensive WebSocket tests
    
    Usage:
        python manage.py shell
        >>> from interactions.websocket_test import run_websocket_tests
        >>> run_websocket_tests()
    """
    print("🚀 Starting WebSocket Test Suite...")
    
    # Create test users
    tenant = User.objects.create_user(
        username='test_tenant',
        email='tenant@test.com',
        role='tenant'
    )
    
    landlord = User.objects.create_user(
        username='test_landlord', 
        email='landlord@test.com',
        role='landlord'
    )
    
    # Create test property
    property_obj = Property.objects.create(
        title="Test Property",
        description="A test property for WebSocket testing",
        location="Test City",
        price=1000.00,
        owner=landlord,
        status='available'
    )
    
    async def run_tests():
        await WebSocketTestSuite.test_notification_flow(tenant, landlord, property_obj)
        await WebSocketTestSuite.test_chat_flow(tenant, landlord, property_obj)
    
    # Run the async tests
    asyncio.run(run_tests())
    
    # Cleanup
    tenant.delete()
    landlord.delete()
    property_obj.delete()
    
    print("🧹 Test cleanup completed")
    print("✨ WebSocket test suite finished!")

if __name__ == "__main__":
    run_websocket_tests()
