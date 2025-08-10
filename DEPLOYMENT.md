# 🚀 SmartHunt Backend Deployment Guide

Your SmartHunt backend is production-ready! Follow this guide to deploy to your preferred platform.

## 📋 Pre-Deployment Checklist

✅ **Backend Status**: All systems operational  
✅ **Database**: Migrations applied successfully  
✅ **Dependencies**: All packages installed  
✅ **Configuration**: Production settings created  
✅ **Security**: JWT, OAuth, CORS configured  

## 🌟 Recommended: Railway Deployment (Easiest)

### Step 1: Install Railway CLI
```bash
npm install -g @railway/cli
```

### Step 2: Login and Initialize
```bash
railway login
cd /path/to/smarthunt-backend
railway init
```

### Step 3: Add Environment Variables
```bash
# Set production environment variables
railway variables set SECRET_KEY="your-django-secret-key"
railway variables set DJANGO_SETTINGS_MODULE="smarthunt.settings_production"
railway variables set GOOGLE_OAUTH2_CLIENT_ID="your-google-client-id"
railway variables set GOOGLE_OAUTH2_CLIENT_SECRET="your-google-client-secret"
railway variables set EMAIL_HOST_USER="your-email@gmail.com"
railway variables set EMAIL_HOST_PASSWORD="your-app-password"
```

### Step 4: Add Database and Redis
```bash
# Add PostgreSQL database
railway add postgresql

# Add Redis for WebSocket support
railway add redis
```

### Step 5: Deploy
```bash
railway up
```

**🎉 Your backend will be live at: `https://your-app-name.railway.app`**

## 🔧 Alternative: Render Deployment

### Step 1: Connect GitHub Repository
1. Push your code to GitHub
2. Go to [render.com](https://render.com)
3. Connect your GitHub repository

### Step 2: Configure Web Service
- **Build Command**: `pip install -r requirements-production.txt`
- **Start Command**: `python manage.py migrate && gunicorn smarthunt.wsgi:application`
- **Environment**: Python 3

### Step 3: Add Environment Variables
Add all variables from `.env.example` in Render dashboard

### Step 4: Add Database
- Add PostgreSQL database service
- Add Redis service for WebSocket support

## 🐳 Docker Deployment (Advanced)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements-production.txt .
RUN pip install -r requirements-production.txt

COPY . .

EXPOSE 8000
CMD ["gunicorn", "smarthunt.wsgi:application", "--bind", "0.0.0.0:8000"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/smarthunt
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: smarthunt
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
```

## 🔐 Environment Variables Setup

### Required Variables:
```bash
SECRET_KEY=your-django-secret-key
DJANGO_SETTINGS_MODULE=smarthunt.settings_production
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Optional Variables:
```bash
USE_HTTPS=True
SENTRY_DSN=your-sentry-dsn
ALLOWED_HOSTS=your-domain.com
FRONTEND_URL=https://your-frontend.com
```

## 🧪 Testing Your Deployment

### 1. Health Check
```bash
curl https://your-app.railway.app/api/users/auth/google-verify/
```

### 2. Test Authentication
```bash
curl -X POST https://your-app.railway.app/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'
```

### 3. Test WebSocket Connection
```javascript
const ws = new WebSocket('wss://your-app.railway.app/ws/notifications/?token=your-jwt-token');
```

## 📊 API Endpoints Available

### Authentication
- `POST /api/users/auth/google-token/` - Google OAuth login
- `POST /api/users/auth/logout/` - Enhanced logout
- `POST /api/users/auth/token/refresh/` - Token refresh
- `GET /api/users/profile/` - User profile

### Properties & Bookings
- `GET /api/properties/` - List properties
- `POST /api/interactions/bookings/` - Create booking
- `POST /api/interactions/bookings/{id}/approve/` - Approve booking
- `GET /api/interactions/bookings/stats/` - Booking statistics

### Real-time Features
- `WebSocket /ws/notifications/` - Live notifications
- `GET /api/interactions/notifications/` - Notification history
- `POST /api/interactions/messages/` - Send messages

## 🔧 Production Optimizations

### 1. Static Files
```python
# Already configured in settings_production.py
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

### 2. Database Connection Pooling
```python
# Add to production settings if needed
DATABASES['default']['CONN_MAX_AGE'] = 600
```

### 3. Caching
```python
# Redis caching already configured
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
    }
}
```

## 🚨 Security Checklist

✅ **DEBUG = False** in production  
✅ **HTTPS enabled** with SSL certificates  
✅ **Environment variables** for secrets  
✅ **CORS configured** for your frontend domain  
✅ **Database credentials** secured  
✅ **JWT tokens** with proper expiration  
✅ **Rate limiting** on authentication endpoints  

## 📈 Monitoring & Maintenance

### 1. Error Tracking
Add Sentry for error monitoring:
```bash
pip install sentry-sdk[django]
```

### 2. Database Backups
- Railway: Automatic backups included
- Render: Configure backup schedule
- Manual: `pg_dump` for PostgreSQL

### 3. Log Monitoring
```python
# Logging already configured in settings_production.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
}
```

## 🎯 Next Steps After Deployment

1. **Test all API endpoints** with your deployed URL
2. **Update frontend** to use production API URL
3. **Configure custom domain** (optional)
4. **Set up monitoring** and alerts
5. **Create admin user**: `python manage.py createsuperuser`

## 🆘 Troubleshooting

### Common Issues:
- **500 Error**: Check environment variables
- **Database Connection**: Verify DATABASE_URL
- **WebSocket Issues**: Ensure Redis is running
- **CORS Errors**: Update CORS_ALLOWED_ORIGINS

### Debug Commands:
```bash
# Check logs
railway logs

# Run migrations
railway run python manage.py migrate

# Create superuser
railway run python manage.py createsuperuser
```

## 🎉 Success!

Your SmartHunt backend is now deployed and ready for production use!

**Backend URL**: `https://your-app.railway.app`  
**Admin Panel**: `https://your-app.railway.app/admin/`  
**API Documentation**: Available via your endpoints  

Connect your frontend and start building amazing property rental experiences! 🏠✨
