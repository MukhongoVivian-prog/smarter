# chatbot/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # user notifications
    re_path(r"ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
    # chat per property or thread (use property id in path)
    re_path(r"ws/chat/property/(?P<property_id>\d+)/$", consumers.ChatConsumer.as_asgi()),
    # optional: user-to-user chat
    re_path(r"ws/chat/user/(?P<user_id>\d+)/$", consumers.ChatConsumer.as_asgi()),
]
