from django.contrib import admin
from .models import ChatMessage

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'message', 'created_at')
    search_fields = ('user__username', 'message', 'response')
    list_filter = ('role', 'created_at')
