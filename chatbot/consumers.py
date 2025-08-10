# chatbot/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from properties.models import Property
from interactions.models import Message  # your model path

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        self.property_id = self.scope["url_route"]["kwargs"].get("property_id")
        self.user_group_name = f"user_{user.id}"
        # group for the property thread
        self.room_group_name = f"property_{self.property_id}"

        # join groups
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        user = self.scope["user"]
        data = json.loads(text_data)
        message_text = data.get("message")
        receiver_id = data.get("receiver_id")  # optional

        # save to DB
        message_obj = await self.create_message(user.id, receiver_id, self.property_id, message_text)

        # broadcast to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": message_obj["message"],
                "sender_id": message_obj["sender_id"],
                "receiver_id": message_obj["receiver_id"],
                "created_at": message_obj["created_at"],
            }
        )

    # handler for group message
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def create_message(self, sender_id, receiver_id, property_id, message):
        sender = User.objects.get(id=sender_id)
        receiver = None
        if receiver_id:
            try:
                receiver = User.objects.get(id=receiver_id)
            except User.DoesNotExist:
                receiver = None
        property_obj = None
        if property_id:
            try:
                property_obj = Property.objects.get(id=property_id)
            except Property.DoesNotExist:
                property_obj = None

        msg = Message.objects.create(
            sender=sender,
            receiver=receiver,
            content=message
        )
        # optionally attach property to message model if you have such field
        # trigger creation of Notification for receiver (sync)
        # returns simple dict to send
        return {
            "id": msg.id,
            "message": msg.content,
            "sender_id": sender.id,
            "receiver_id": receiver.id if receiver else None,
            "created_at": msg.timestamp.isoformat(),
        }
# chatbot/consumers.py (continued)
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return
        self.user_group_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

    # Receive broadcast
    async def notify(self, event):
        # event should contain 'title', 'body', 'type', 'created_at', etc
        await self.send(text_data=json.dumps(event))
