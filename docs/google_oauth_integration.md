# Google OAuth Integration Guide for SmartHunt

## Overview
SmartHunt backend provides comprehensive Google OAuth integration for seamless user authentication. Users can sign up and log in using their Google accounts, with automatic JWT token generation for API access.

## Features
- ✅ Google OAuth 2.0 authentication
- ✅ Automatic user creation with role selection
- ✅ JWT token generation (access + refresh)
- ✅ Email verification validation
- ✅ Profile picture integration
- ✅ Comprehensive error handling
- ✅ Token validation endpoints
- ✅ Enhanced logout with token blacklisting

## API Endpoints

### 1. Google Token Authentication
**POST** `/api/users/auth/google-token/`

Authenticate user with Google access token and return JWT tokens.

**Request Body:**
```json
{
  "access_token": "google_access_token_here",
  "role": "tenant" // or "landlord"
}
```

**Success Response (200):**
```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "user@gmail.com",
    "first_name": "Test",
    "last_name": "User",
    "role": "tenant",
    "profile_picture_url": "https://lh3.googleusercontent.com/...",
    "google_id": "123456789"
  },
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "created": true,
  "message": "Successfully authenticated with Google",
  "auth_method": "google_oauth"
}
```

**Error Responses:**
- `400` - Missing token, invalid role, unverified email
- `503` - Network error contacting Google
- `500` - Internal server error

### 2. Google Token Verification
**POST** `/api/users/auth/google-verify/`

Verify Google token without authentication (useful for frontend validation).

**Request Body:**
```json
{
  "access_token": "google_access_token_here"
}
```

**Success Response (200):**
```json
{
  "valid": true,
  "user_info": {
    "email": "user@gmail.com",
    "name": "Test User",
    "picture": "https://lh3.googleusercontent.com/...",
    "verified_email": true
  },
  "message": "Google token is valid"
}
```

### 3. Enhanced Logout
**POST** `/api/users/auth/logout/`

Logout user and blacklist refresh token.

**Headers:**
```
Authorization: Bearer jwt_access_token
```

**Request Body:**
```json
{
  "refresh_token": "jwt_refresh_token"
}
```

**Success Response (200):**
```json
{
  "message": "Successfully logged out",
  "code": "LOGOUT_SUCCESS"
}
```

### 4. Enhanced Token Refresh
**POST** `/api/users/auth/token/refresh/`

Refresh JWT access token with validation.

**Request Body:**
```json
{
  "refresh": "jwt_refresh_token"
}
```

**Success Response (200):**
```json
{
  "access": "new_jwt_access_token",
  "message": "Token refreshed successfully"
}
```

### 5. User Profile
**GET/PATCH** `/api/users/profile/`

Get or update user profile (protected fields cannot be modified).

**Headers:**
```
Authorization: Bearer jwt_access_token
```

## Frontend Integration

### React Implementation

```javascript
// Google OAuth Hook
import { useGoogleLogin } from '@react-oauth/google';

const useSmartHuntAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setLoading(true);
      try {
        const response = await fetch('/api/users/auth/google-token/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            access_token: tokenResponse.access_token,
            role: 'tenant' // or 'landlord'
          }),
        });

        const data = await response.json();

        if (response.ok) {
          // Store tokens
          localStorage.setItem('access_token', data.access);
          localStorage.setItem('refresh_token', data.refresh);
          
          setUser(data.user);
          
          // Show success message
          if (data.created) {
            toast.success('Welcome to SmartHunt! Your account has been created.');
          } else {
            toast.success('Welcome back!');
          }
        } else {
          toast.error(data.error || 'Authentication failed');
        }
      } catch (error) {
        toast.error('Network error during authentication');
      } finally {
        setLoading(false);
      }
    },
    onError: (error) => {
      console.error('Google OAuth error:', error);
      toast.error('Google authentication failed');
    },
  });

  const logout = async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    const accessToken = localStorage.getItem('access_token');

    if (refreshToken && accessToken) {
      try {
        await fetch('/api/users/auth/logout/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            refresh_token: refreshToken,
          }),
        });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }

    // Clear local storage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  return {
    user,
    loading,
    googleLogin,
    logout,
  };
};

// Usage in component
const LoginPage = () => {
  const { googleLogin, loading } = useSmartHuntAuth();

  return (
    <div className="login-page">
      <h1>Sign in to SmartHunt</h1>
      
      <div className="role-selection">
        <button
          onClick={() => googleLogin()}
          disabled={loading}
          className="google-login-btn"
        >
          {loading ? 'Signing in...' : 'Continue with Google'}
        </button>
      </div>
    </div>
  );
};
```

### Token Management

```javascript
// API client with automatic token refresh
class ApiClient {
  constructor() {
    this.baseURL = '/api';
  }

  async request(endpoint, options = {}) {
    const accessToken = localStorage.getItem('access_token');
    
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
        ...options.headers,
      },
    };

    let response = await fetch(`${this.baseURL}${endpoint}`, config);

    // Handle token refresh
    if (response.status === 401) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        // Retry request with new token
        config.headers.Authorization = `Bearer ${localStorage.getItem('access_token')}`;
        response = await fetch(`${this.baseURL}${endpoint}`, config);
      }
    }

    return response;
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;

    try {
      const response = await fetch('/api/users/auth/token/refresh/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh: refreshToken,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access);
        return true;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }

    // Refresh failed, redirect to login
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
    return false;
  }
}
```

## Configuration

### Environment Variables

Create `.env` file with Google OAuth credentials:

```bash
# Google OAuth Settings
GOOGLE_OAUTH2_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=your_google_client_secret

# JWT Settings
SECRET_KEY=your_django_secret_key
```

### Django Settings

Add to `settings.py`:

```python
# Google OAuth Configuration
GOOGLE_OAUTH2_CLIENT_ID = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
GOOGLE_OAUTH2_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET')

# Allauth Configuration (if using django-allauth)
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

## Testing

### Unit Tests

```bash
# Run OAuth-specific tests
python manage.py test users.oauth_test

# Run all user tests
python manage.py test users
```

### Manual Testing

```python
# In Django shell
from users.oauth_test import run_oauth_tests
run_oauth_tests()

# Validate OAuth settings
from users.oauth_test import GoogleOAuthIntegrationTest
GoogleOAuthIntegrationTest.validate_oauth_settings()
```

### API Testing with cURL

```bash
# Test Google token authentication
curl -X POST http://localhost:8000/api/users/auth/google-token/ \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "your_google_access_token",
    "role": "tenant"
  }'

# Test token verification
curl -X POST http://localhost:8000/api/users/auth/google-verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "your_google_access_token"
  }'
```

## Error Handling

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `MISSING_TOKEN` | Google access token not provided | Include `access_token` in request |
| `INVALID_TOKEN` | Google token is invalid/expired | Get new token from Google |
| `INVALID_ROLE` | Role is not 'tenant' or 'landlord' | Use valid role value |
| `UNVERIFIED_EMAIL` | Google email not verified | Verify email in Google account |
| `NETWORK_ERROR` | Cannot contact Google API | Check internet connection |
| `MISSING_REFRESH_TOKEN` | Refresh token not provided | Include refresh token in logout |
| `PROTECTED_FIELD` | Trying to update protected field | Remove protected fields from request |

### Error Response Format

```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": "Additional error details (optional)"
}
```

## Security Considerations

### Best Practices
1. **Token Storage**: Store JWT tokens securely (httpOnly cookies recommended for production)
2. **HTTPS**: Always use HTTPS in production
3. **Token Expiry**: Implement proper token refresh logic
4. **Validation**: Always validate Google tokens server-side
5. **Rate Limiting**: Implement rate limiting on auth endpoints
6. **Logging**: Log authentication events for security monitoring

### Production Checklist
- [ ] Google OAuth credentials configured
- [ ] HTTPS enabled
- [ ] Rate limiting implemented
- [ ] Error logging configured
- [ ] Token blacklisting enabled
- [ ] CORS properly configured
- [ ] Security headers implemented

## Troubleshooting

### Common Issues

1. **"Invalid Google token"**
   - Check token expiry
   - Verify Google API credentials
   - Ensure proper scopes requested

2. **"Network error"**
   - Check internet connectivity
   - Verify Google API endpoints accessible
   - Check firewall settings

3. **"User creation failed"**
   - Check database connectivity
   - Verify user model fields
   - Check for unique constraint violations

4. **"Token refresh failed"**
   - Verify refresh token not blacklisted
   - Check JWT configuration
   - Ensure user account is active

For additional support, check the Django logs and Google OAuth documentation.
