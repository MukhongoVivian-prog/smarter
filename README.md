# SmartHunt Backend

A comprehensive, multi-role property rental platform backend built with Django and Django REST Framework, featuring real-time notifications, role-based access control, and modern API design.

## 🏗️ Architecture Overview

SmartHunt is designed as a secure, scalable backend that supports three distinct user roles with strict data isolation:

- **Tenants**: Browse properties, save favorites, submit booking requests, write reviews, manage maintenance requests
- **Landlords**: Manage properties, handle booking requests, respond to maintenance issues, communicate with tenants
- **Admins**: Full platform oversight and moderation capabilities

## 🚀 Key Features

### ✅ **Authentication & Security**
- JWT-based authentication with access/refresh tokens
- Google OAuth integration for seamless login
- Role-based permissions with object-level access control
- Strict data isolation between users
- CORS support for frontend integration

### ✅ **Real-Time Communication**
- WebSocket notifications via Django Channels
- Real-time updates for bookings, messages, maintenance requests
- Redis-backed channel layer for scalability
- Fallback REST endpoints for notification history

### ✅ **Comprehensive API**
- RESTful endpoints with filtering, search, and pagination
- Advanced property search with location, price, type filters
- Nested serializers for efficient data loading
- Role-aware response data

### ✅ **Email Integration**
- SMTP email notifications for key events
- Welcome emails, booking updates, maintenance alerts
- Customizable email templates
- Automatic email triggers via Django signals

### ✅ **Business Logic**
- Complete booking lifecycle management
- Property management with image support
- Review and rating system
- Maintenance request tracking
- Favorite properties functionality

## 📁 Project Structure

```
smarthunt-backend/
├── smarthunt/           # Main Django project
│   ├── settings.py      # Configuration with OAuth, SMTP, Channels
│   ├── asgi.py         # WebSocket routing configuration
│   └── urls.py         # Main URL configuration
├── users/              # User management and authentication
│   ├── models.py       # Custom User model with roles
│   ├── permissions.py  # Role-based and object-level permissions
│   ├── auth_views.py   # Google OAuth and JWT authentication
│   ├── email_utils.py  # Email notification utilities
│   └── serializers.py  # User data serialization
├── properties/         # Property management
│   ├── models.py       # Property, Amenity, PropertyImage models
│   ├── filters.py      # Advanced property filtering
│   ├── serializers.py  # Property data serialization
│   └── views.py        # Property CRUD operations
├── interactions/       # User interactions and communications
│   ├── models.py       # Messages, Bookings, Reviews, Notifications
│   ├── consumers.py    # WebSocket consumers for real-time updates
│   ├── signals.py      # Automatic notifications and email triggers
│   ├── filters.py      # Interaction filtering capabilities
│   └── views.py        # Interaction API endpoints
├── dashboards/         # User-specific analytics and stats
├── chatbot/           # AI assistant integration
└── requirements.txt   # Python dependencies
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.9+
- Redis server (for WebSocket support)
- PostgreSQL (recommended for production)

### Installation

1. **Clone and setup virtual environment:**
```bash
cd smarthunt-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment variables:**
Create a `.env` file with:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3  # or PostgreSQL URL
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
```

3. **Run migrations and start services:**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

4. **Start Redis server:**
```bash
redis-server  # Required for WebSocket functionality
```

## 🔧 API Endpoints

### Authentication
- `POST /auth/register/` - User registration
- `POST /auth/login/` - JWT login
- `POST /auth/google/` - Google OAuth login
- `POST /auth/logout/` - Logout with token blacklisting

### Properties
- `GET /api/properties/` - List properties (with filtering)
- `GET /api/properties/{id}/` - Property details
- `POST /api/properties/` - Create property (landlords only)
- `PUT /api/properties/{id}/` - Update property (owner only)

### Interactions
- `GET /api/interactions/messages/` - User messages
- `POST /api/interactions/bookings/` - Create booking request
- `GET /api/interactions/notifications/` - User notifications
- `POST /api/interactions/reviews/` - Submit property review
- `GET /api/interactions/favorites/` - User favorites

### WebSocket Endpoints
- `ws://localhost:8000/ws/notifications/?token=<jwt_token>` - Real-time notifications

## 🔐 Permission System

### Role-Based Access
- **Tenants**: Can create bookings, reviews, favorites, maintenance requests
- **Landlords**: Can manage their properties, respond to requests for their properties
- **Admins**: Full access to all resources

### Object-Level Permissions
- Users can only access their own data (messages, notifications, bookings)
- Landlords can only manage their own properties and related interactions
- Strict data isolation prevents unauthorized access

## 📧 Email Notifications

Automatic email notifications are sent for:
- Welcome emails for new users
- New booking requests (to landlords)
- Booking status updates (to tenants)
- New maintenance requests (to landlords)
- Maintenance status updates (to tenants)

## 🔄 Real-Time Features

WebSocket connections provide instant updates for:
- New message notifications
- Booking request status changes
- Maintenance request updates
- Property interaction alerts

## 🚀 Deployment

### Production Checklist
1. Set `DEBUG=False` in settings
2. Configure PostgreSQL database
3. Set up Redis for production
4. Configure email SMTP settings
5. Set proper CORS origins
6. Use environment variables for secrets
7. Configure static file serving
8. Set up monitoring and logging

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "smarthunt.wsgi:application"]
```

## 🧪 Testing

Run the test suite:
```bash
python manage.py test
pytest  # If using pytest
```

## 📊 API Features

### Filtering & Search
- Properties: Filter by location, type, price range, availability
- Bookings: Filter by status, property, date range
- Notifications: Filter by type, read status
- Full-text search on relevant fields

### Pagination
- Default 20 items per page
- Configurable page size
- Efficient database queries

### Ordering
- Sort by creation date, price, rating
- Ascending/descending options
- Multiple field sorting

## 🔧 Configuration

Key settings in `settings.py`:
- JWT token lifetimes
- Email SMTP configuration
- CORS origins for frontend
- Channel layer configuration
- Google OAuth settings

## 🤝 Contributing

1. Follow Django best practices
2. Maintain role-based security
3. Add tests for new features
4. Update documentation
5. Ensure proper error handling

## 📝 License

This project is proprietary software for SmartHunt platform.

---

**SmartHunt Backend** - Secure, scalable, real-time property rental platform API
