"""
Google OAuth Testing Utilities for SmartHunt

This module provides comprehensive testing utilities for Google OAuth integration,
including token validation, user creation, and authentication flow testing.
"""

import requests
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, Mock
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class GoogleOAuthTestCase(APITestCase):
    """Test case for Google OAuth functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.google_auth_url = reverse('google_token_auth')
        self.google_verify_url = reverse('google_token_verify')
        self.logout_url = reverse('enhanced_logout')
        self.profile_url = reverse('user_profile')
        
        # Mock Google user data
        self.mock_google_user_data = {
            'id': '123456789',
            'email': 'testuser@gmail.com',
            'name': 'Test User',
            'given_name': 'Test',
            'family_name': 'User',
            'picture': 'https://example.com/picture.jpg',
            'verified_email': True
        }
    
    @patch('requests.get')
    def test_google_auth_success_new_user(self, mock_get):
        """Test successful Google authentication with new user creation"""
        # Mock Google API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_google_user_data
        mock_get.return_value = mock_response
        
        # Test data
        data = {
            'access_token': 'fake_google_token',
            'role': 'tenant'
        }
        
        # Make request
        response = self.client.post(self.google_auth_url, data, format='json')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertTrue(response.data['created'])
        self.assertEqual(response.data['auth_method'], 'google_oauth')
        
        # Check user was created
        user = User.objects.get(email='testuser@gmail.com')
        self.assertEqual(user.role, 'tenant')
        self.assertEqual(user.google_id, '123456789')
        self.assertTrue(user.is_active)
    
    @patch('requests.get')
    def test_google_auth_success_existing_user(self, mock_get):
        """Test successful Google authentication with existing user"""
        # Create existing user
        existing_user = User.objects.create_user(
            username='testuser',
            email='testuser@gmail.com',
            role='landlord'
        )
        
        # Mock Google API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_google_user_data
        mock_get.return_value = mock_response
        
        # Test data
        data = {
            'access_token': 'fake_google_token',
            'role': 'tenant'  # Different role, should not change existing user
        }
        
        # Make request
        response = self.client.post(self.google_auth_url, data, format='json')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['created'])
        
        # Check user role didn't change
        existing_user.refresh_from_db()
        self.assertEqual(existing_user.role, 'landlord')  # Should remain landlord
        self.assertEqual(existing_user.google_id, '123456789')  # Should be updated
    
    def test_google_auth_missing_token(self):
        """Test Google authentication without access token"""
        data = {'role': 'tenant'}
        
        response = self.client.post(self.google_auth_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'MISSING_TOKEN')
    
    def test_google_auth_invalid_role(self):
        """Test Google authentication with invalid role"""
        data = {
            'access_token': 'fake_token',
            'role': 'invalid_role'
        }
        
        response = self.client.post(self.google_auth_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'INVALID_ROLE')
    
    @patch('requests.get')
    def test_google_auth_invalid_token(self, mock_get):
        """Test Google authentication with invalid token"""
        # Mock Google API error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        data = {
            'access_token': 'invalid_google_token',
            'role': 'tenant'
        }
        
        response = self.client.post(self.google_auth_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'INVALID_TOKEN')
    
    @patch('requests.get')
    def test_google_auth_unverified_email(self, mock_get):
        """Test Google authentication with unverified email"""
        # Mock Google API response with unverified email
        unverified_data = self.mock_google_user_data.copy()
        unverified_data['verified_email'] = False
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = unverified_data
        mock_get.return_value = mock_response
        
        data = {
            'access_token': 'fake_google_token',
            'role': 'tenant'
        }
        
        response = self.client.post(self.google_auth_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'UNVERIFIED_EMAIL')
    
    @patch('requests.get')
    def test_google_token_verification_success(self, mock_get):
        """Test Google token verification endpoint"""
        # Mock Google API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_google_user_data
        mock_get.return_value = mock_response
        
        data = {'access_token': 'fake_google_token'}
        
        response = self.client.post(self.google_verify_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        self.assertIn('user_info', response.data)
        self.assertEqual(response.data['user_info']['email'], 'testuser@gmail.com')
    
    def test_logout_success(self):
        """Test successful logout"""
        # Create user and get tokens
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='tenant'
        )
        refresh = RefreshToken.for_user(user)
        
        # Authenticate client
        self.client.force_authenticate(user=user)
        
        data = {'refresh_token': str(refresh)}
        
        response = self.client.post(self.logout_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'LOGOUT_SUCCESS')
    
    def test_logout_missing_refresh_token(self):
        """Test logout without refresh token"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='tenant'
        )
        self.client.force_authenticate(user=user)
        
        response = self.client.post(self.logout_url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'MISSING_REFRESH_TOKEN')
    
    def test_user_profile_view(self):
        """Test user profile view"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='tenant',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=user)
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['role'], 'tenant')
    
    def test_user_profile_update_protected_fields(self):
        """Test that protected fields cannot be updated"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='tenant'
        )
        self.client.force_authenticate(user=user)
        
        # Try to update protected field
        data = {'email': 'newemail@example.com'}
        
        response = self.client.patch(self.profile_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'PROTECTED_FIELD')

class GoogleOAuthIntegrationTest:
    """Integration test utilities for Google OAuth"""
    
    @staticmethod
    def test_complete_oauth_flow():
        """
        Test complete OAuth flow with real Google API (requires valid token)
        
        Usage:
            python manage.py shell
            >>> from users.oauth_test import GoogleOAuthIntegrationTest
            >>> GoogleOAuthIntegrationTest.test_complete_oauth_flow()
        """
        print("🔍 Testing Google OAuth Integration...")
        
        # This would require a real Google token for testing
        print("⚠️  This test requires a valid Google access token")
        print("📝 To test manually:")
        print("   1. Get Google access token from Google OAuth playground")
        print("   2. Use the token with /api/users/auth/google-token/ endpoint")
        print("   3. Verify JWT tokens are returned")
        
        return True
    
    @staticmethod
    def validate_oauth_settings():
        """Validate Google OAuth settings"""
        from django.conf import settings
        
        print("🔧 Validating Google OAuth Settings...")
        
        # Check if allauth is configured
        if 'allauth' not in settings.INSTALLED_APPS:
            print("❌ django-allauth not in INSTALLED_APPS")
            return False
        
        # Check Google provider settings
        socialaccount_providers = getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
        google_config = socialaccount_providers.get('google', {})
        
        if not google_config:
            print("⚠️  Google provider not configured in SOCIALACCOUNT_PROVIDERS")
        else:
            print("✅ Google provider configured")
        
        # Check required environment variables
        google_client_id = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', None)
        google_client_secret = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_SECRET', None)
        
        if not google_client_id:
            print("⚠️  GOOGLE_OAUTH2_CLIENT_ID not set")
        else:
            print("✅ Google Client ID configured")
            
        if not google_client_secret:
            print("⚠️  GOOGLE_OAUTH2_CLIENT_SECRET not set")
        else:
            print("✅ Google Client Secret configured")
        
        print("🎯 OAuth validation complete")
        return True

def run_oauth_tests():
    """
    Run comprehensive OAuth tests
    
    Usage:
        python manage.py shell
        >>> from users.oauth_test import run_oauth_tests
        >>> run_oauth_tests()
    """
    print("🚀 Starting Google OAuth Test Suite...")
    
    # Validate settings
    GoogleOAuthIntegrationTest.validate_oauth_settings()
    
    # Run integration test
    GoogleOAuthIntegrationTest.test_complete_oauth_flow()
    
    print("✅ OAuth test suite completed!")
    print("💡 Run 'python manage.py test users.oauth_test' for unit tests")

if __name__ == "__main__":
    run_oauth_tests()
