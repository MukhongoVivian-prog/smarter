# users/auth_views.py
from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from .serializers import UserSerializer
from .email_utils import send_welcome_email
import requests
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class GoogleLogin(SocialLoginView):
    """
    Google OAuth2 login view that returns JWT tokens
    """
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://localhost:3000/auth/callback/google"  # Frontend callback URL
    client_class = OAuth2Client

    def get_response(self):
        """Override to return JWT tokens instead of session auth"""
        serializer_class = self.get_response_serializer()
        
        if getattr(self, 'access_token', None):
            # User successfully authenticated
            user = self.user
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'message': 'Successfully authenticated with Google'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Authentication failed'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def google_auth(request):
    """
    Enhanced Google authentication endpoint
    Accepts Google access token and returns JWT tokens with comprehensive validation
    """
    google_access_token = request.data.get('access_token')
    user_role = request.data.get('role', 'tenant')  # Default to tenant
    
    if not google_access_token:
        return Response({
            'error': 'Google access token is required',
            'code': 'MISSING_TOKEN'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate role
    if user_role not in ['tenant', 'landlord']:
        return Response({
            'error': 'Invalid role. Must be either "tenant" or "landlord"',
            'code': 'INVALID_ROLE'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Verify Google token and get user info
        google_user_info_url = f'https://www.googleapis.com/oauth2/v2/userinfo?access_token={google_access_token}'
        response = requests.get(google_user_info_url, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"Google token verification failed: {response.status_code}")
            return Response({
                'error': 'Invalid or expired Google access token',
                'code': 'INVALID_TOKEN'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_data = response.json()
        email = user_data.get('email')
        name = user_data.get('name', '')
        picture = user_data.get('picture', '')
        google_id = user_data.get('id')
        
        if not email:
            return Response({
                'error': 'Email not provided by Google',
                'code': 'MISSING_EMAIL'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user_data.get('verified_email', False):
            return Response({
                'error': 'Google email not verified',
                'code': 'UNVERIFIED_EMAIL'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use database transaction for user creation
        with transaction.atomic():
            # Check if user exists
            try:
                user = User.objects.get(email=email)
                created = False
                
                # Update user info if needed
                if not user.google_id and google_id:
                    user.google_id = google_id
                    user.save(update_fields=['google_id'])
                    
            except User.DoesNotExist:
                # Create new user
                username = email.split('@')[0]
                
                # Ensure unique username
                counter = 1
                original_username = username
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=name.split(' ')[0] if name else '',
                    last_name=' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else '',
                    role=user_role,
                    is_active=True,
                    google_id=google_id,
                    profile_picture_url=picture
                )
                created = True
                
                # Send welcome email for new users
                try:
                    send_welcome_email(user)
                except Exception as e:
                    logger.error(f"Failed to send welcome email to {email}: {str(e)}")
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Log successful authentication
        logger.info(f"Google OAuth successful for user {user.id} ({email}) - {'created' if created else 'existing'}")
        
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'created': created,
            'message': 'Successfully authenticated with Google',
            'auth_method': 'google_oauth'
        }, status=status.HTTP_200_OK)
        
    except requests.RequestException as e:
        logger.error(f"Google API request failed: {str(e)}")
        return Response({
            'error': 'Failed to verify Google token - network error',
            'code': 'NETWORK_ERROR'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    except ValidationError as e:
        logger.error(f"User validation failed: {str(e)}")
        return Response({
            'error': 'User data validation failed',
            'code': 'VALIDATION_ERROR',
            'details': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Google OAuth authentication failed: {str(e)}")
        return Response({
            'error': 'Authentication failed - internal error',
            'code': 'INTERNAL_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Enhanced logout view that blacklists the refresh token
    """
    try:
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh token is required for logout',
                'code': 'MISSING_REFRESH_TOKEN'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Blacklist the refresh token
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        logger.info(f"User {request.user.id} logged out successfully")
        
        return Response({
            'message': 'Successfully logged out',
            'code': 'LOGOUT_SUCCESS'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Logout failed for user {request.user.id}: {str(e)}")
        return Response({
            'error': 'Logout failed - invalid or expired token',
            'code': 'LOGOUT_FAILED'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def token_refresh_view(request):
    """
    Enhanced token refresh endpoint with validation
    """
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response({
            'error': 'Refresh token is required',
            'code': 'MISSING_REFRESH_TOKEN'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Validate and refresh token
        token = RefreshToken(refresh_token)
        user = User.objects.get(id=token['user_id'])
        
        # Check if user is still active
        if not user.is_active:
            return Response({
                'error': 'User account is deactivated',
                'code': 'ACCOUNT_DEACTIVATED'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate new access token
        new_access_token = str(token.access_token)
        
        return Response({
            'access': new_access_token,
            'message': 'Token refreshed successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        return Response({
            'error': 'Invalid or expired refresh token',
            'code': 'INVALID_REFRESH_TOKEN'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_google_token(request):
    """
    Endpoint to verify Google token without authentication
    Useful for frontend validation
    """
    google_access_token = request.data.get('access_token')
    
    if not google_access_token:
        return Response({
            'error': 'Google access token is required',
            'code': 'MISSING_TOKEN'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Verify Google token
        google_user_info_url = f'https://www.googleapis.com/oauth2/v2/userinfo?access_token={google_access_token}'
        response = requests.get(google_user_info_url, timeout=10)
        
        if response.status_code != 200:
            return Response({
                'valid': False,
                'error': 'Invalid or expired Google token',
                'code': 'INVALID_TOKEN'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_data = response.json()
        
        return Response({
            'valid': True,
            'user_info': {
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'picture': user_data.get('picture'),
                'verified_email': user_data.get('verified_email', False)
            },
            'message': 'Google token is valid'
        }, status=status.HTTP_200_OK)
        
    except requests.RequestException as e:
        logger.error(f"Google token verification failed: {str(e)}")
        return Response({
            'valid': False,
            'error': 'Network error during token verification',
            'code': 'NETWORK_ERROR'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return Response({
            'valid': False,
            'error': 'Token verification failed',
            'code': 'VERIFICATION_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Enhanced user profile view with Google OAuth integration
    """
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        """Override to prevent certain fields from being updated"""
        # Fields that cannot be updated via this endpoint
        protected_fields = ['email', 'google_id', 'is_active', 'is_staff', 'is_superuser']
        
        for field in protected_fields:
            if field in request.data:
                return Response({
                    'error': f'Field "{field}" cannot be updated via this endpoint',
                    'code': 'PROTECTED_FIELD'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().update(request, *args, **kwargs)
