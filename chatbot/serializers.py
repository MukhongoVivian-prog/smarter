from rest_framework import serializers
from .models import ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'role', 'message', 'response', 'created_at']
        read_only_fields = ['id', 'user', 'role', 'response', 'created_at']
