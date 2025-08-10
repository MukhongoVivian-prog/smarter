from django.urls import path
from .views import ChatMessageCreateView

urlpatterns = [
    path('send/', ChatMessageCreateView.as_view(), name='send-message'),
]
