# smarthunt/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import chatbot.routing
import interactions.routing
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthunt.settings')
django_asgi_app = get_asgi_application()

# Import our custom JWTAuthMiddleware
from interactions.middleware import JWTAuthMiddleware

# Combine all WebSocket URL patterns
websocket_urlpatterns = (
    chatbot.routing.websocket_urlpatterns +
    interactions.routing.websocket_urlpatterns
)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
