# smarthunt/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT Authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # App endpoints
    path('api/users/', include('users.urls')),          # Authentication & roles
    path('api/properties/', include('properties.urls')), # Property listings
    path('api/interactions/', include('interactions.urls')), # Reviews, favorites, etc.
    path('api/dashboards/', include('dashboards.urls')),     # Landlord & Tenant dashboards
    path('api/chatbot/', include('chatbot.urls')),           # Chatbot integration
    path('ussd/', include('ussd.urls')),           # Chatbot integration

]
