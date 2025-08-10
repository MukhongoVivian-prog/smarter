from django.urls import path
from .views import RegisterView, LandlordOnlyView, TenantOnlyView
from .auth_views import (
    GoogleLogin, google_auth, logout_view, token_refresh_view, 
    verify_google_token, UserProfileView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # User registration and basic auth
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Google OAuth endpoints
    path('auth/google/', GoogleLogin.as_view(), name='google_oauth_login'),
    path('auth/google-token/', google_auth, name='google_token_auth'),
    path('auth/google-verify/', verify_google_token, name='google_token_verify'),
    path('auth/token/refresh/', token_refresh_view, name='enhanced_token_refresh'),
    path('auth/logout/', logout_view, name='enhanced_logout'),
    
    # User profile
    path('profile/', UserProfileView.as_view(), name='user_profile'),

    # Role-based test endpoints
    path('landlord-only/', LandlordOnlyView.as_view(), name='landlord-only'),
    path('tenant-only/', TenantOnlyView.as_view(), name='tenant-only'),
]
