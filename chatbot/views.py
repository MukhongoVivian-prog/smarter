from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import ChatMessage
from .serializers import ChatMessageSerializer
from .utils import process_message

User = get_user_model()

class ChatMessageCreateView(generics.CreateAPIView):
    """
    POST /api/chatbot/send/
    Body: { "message": "text" }
    Auth: JWT (required)
    """
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        message_text = request.data.get('message', '').strip()
        if not message_text:
            return Response({"detail": "Message is required."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        role = getattr(user, 'role', None) or 'tenant'  # fallback to tenant

        # process (synchronous simple logic)
        bot_reply = process_message(role, message_text, user=user)

        # persist chat
        chat = ChatMessage.objects.create(
            user=user,
            role=role,
            message=message_text,
            response=bot_reply
        )

        serializer = self.get_serializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
