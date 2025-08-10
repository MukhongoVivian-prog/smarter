# WebSocket Integration Guide for SmartHunt Frontend

## Overview
SmartHunt backend provides real-time notifications and chat functionality via WebSocket connections using Django Channels. This guide explains how to integrate with the frontend.

## WebSocket Endpoints

### Notifications WebSocket
- **URL**: `ws://localhost:8000/ws/notifications/?token={jwt_access_token}`
- **Purpose**: Real-time notifications, unread counts, and system events
- **Authentication**: JWT token in query parameter

### Chat WebSocket (Future)
- **URL**: `ws://localhost:8000/ws/chat/?token={jwt_access_token}`
- **Purpose**: Real-time messaging between users
- **Authentication**: JWT token in query parameter

## Frontend Implementation

### 1. WebSocket Connection Setup

```javascript
class SmartHuntWebSocket {
    constructor(accessToken) {
        this.accessToken = accessToken;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.eventHandlers = {};
    }

    connect() {
        const wsUrl = `ws://localhost:8000/ws/notifications/?token=${this.accessToken}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = (event) => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.onConnectionEstablished(event);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onclose = (event) => {
            console.log('WebSocket disconnected');
            this.handleReconnection();
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    handleMessage(data) {
        const { type } = data;
        
        switch (type) {
            case 'connection_established':
                this.emit('connected', data);
                break;
            case 'notification':
                this.emit('notification', data);
                break;
            case 'chat_message':
                this.emit('chatMessage', data);
                break;
            case 'booking_update':
                this.emit('bookingUpdate', data);
                break;
            case 'unread_count':
                this.emit('unreadCount', data);
                break;
            case 'pong':
                this.emit('pong', data);
                break;
            default:
                console.log('Unknown message type:', type, data);
        }
    }

    // Event handling
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }

    emit(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => handler(data));
        }
    }

    // WebSocket actions
    markNotificationRead(notificationId) {
        this.send({
            type: 'mark_read',
            notification_id: notificationId
        });
    }

    markAllNotificationsRead() {
        this.send({
            type: 'mark_all_read'
        });
    }

    getUnreadCount() {
        this.send({
            type: 'get_unread_count'
        });
    }

    ping() {
        this.send({
            type: 'ping'
        });
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected');
        }
    }

    handleReconnection() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error('Max reconnection attempts reached');
            this.emit('connectionFailed');
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}
```

### 2. React Hook Implementation

```javascript
import { useState, useEffect, useCallback } from 'react';

export const useWebSocket = (accessToken) => {
    const [ws, setWs] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [unreadCount, setUnreadCount] = useState(0);
    const [notifications, setNotifications] = useState([]);

    useEffect(() => {
        if (!accessToken) return;

        const websocket = new SmartHuntWebSocket(accessToken);
        
        // Event handlers
        websocket.on('connected', (data) => {
            setIsConnected(true);
            console.log('WebSocket connected:', data);
        });

        websocket.on('notification', (data) => {
            setNotifications(prev => [data, ...prev]);
            // Show toast notification
            showToast(data.title, data.body, data.notification_type);
        });

        websocket.on('unreadCount', (data) => {
            setUnreadCount(data.count);
        });

        websocket.on('bookingUpdate', (data) => {
            // Handle booking updates
            console.log('Booking update:', data);
            // Refresh booking data if on bookings page
        });

        websocket.on('chatMessage', (data) => {
            // Handle real-time chat messages
            console.log('New chat message:', data);
            // Update chat UI if on messages page
        });

        websocket.on('connectionFailed', () => {
            setIsConnected(false);
            console.error('WebSocket connection failed');
        });

        websocket.connect();
        setWs(websocket);

        return () => {
            websocket.disconnect();
        };
    }, [accessToken]);

    const markNotificationRead = useCallback((notificationId) => {
        if (ws) {
            ws.markNotificationRead(notificationId);
        }
    }, [ws]);

    const markAllNotificationsRead = useCallback(() => {
        if (ws) {
            ws.markAllNotificationsRead();
            setNotifications([]);
        }
    }, [ws]);

    return {
        isConnected,
        unreadCount,
        notifications,
        markNotificationRead,
        markAllNotificationsRead,
        ws
    };
};
```

### 3. Notification Toast Component

```javascript
import { toast } from 'react-toastify';

const showToast = (title, body, type) => {
    const toastOptions = {
        position: "top-right",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
    };

    switch (type) {
        case 'booking':
            toast.success(`${title}: ${body}`, toastOptions);
            break;
        case 'message':
            toast.info(`${title}: ${body}`, toastOptions);
            break;
        case 'maintenance':
            toast.warning(`${title}: ${body}`, toastOptions);
            break;
        default:
            toast(`${title}: ${body}`, toastOptions);
    }
};
```

## Message Types

### Outgoing (Frontend → Backend)

| Type | Purpose | Payload |
|------|---------|---------|
| `mark_read` | Mark notification as read | `{type: 'mark_read', notification_id: number}` |
| `mark_all_read` | Mark all notifications as read | `{type: 'mark_all_read'}` |
| `get_unread_count` | Get current unread count | `{type: 'get_unread_count'}` |
| `ping` | Test connection | `{type: 'ping'}` |

### Incoming (Backend → Frontend)

| Type | Purpose | Payload |
|------|---------|---------|
| `connection_established` | Connection confirmed | `{type: 'connection_established', user_id, username, timestamp}` |
| `notification` | New notification | `{type: 'notification', title, body, notification_type, data, notification_id, timestamp}` |
| `chat_message` | Real-time chat message | `{type: 'chat_message', message_id, sender_id, sender_name, recipient_id, content, timestamp, property_id}` |
| `booking_update` | Booking status update | `{type: 'booking_update', booking_id, action, status, property_id, property_title, tenant_id, landlord_id, timestamp}` |
| `unread_count` | Updated unread count | `{type: 'unread_count', count}` |
| `pong` | Response to ping | `{type: 'pong', timestamp}` |

## Testing WebSocket Connections

### Backend Testing
```python
# In Django shell
from interactions.websocket_test import run_websocket_tests
run_websocket_tests()

# Health check
from interactions.realtime_manager import WebSocketHealthChecker
WebSocketHealthChecker.run_health_check()
```

### Frontend Testing
```javascript
// Test connection
const ws = new SmartHuntWebSocket(accessToken);
ws.connect();

// Test ping
ws.ping();

// Listen for events
ws.on('notification', (data) => {
    console.log('Received notification:', data);
});
```

## Error Handling

### Connection Errors
- **Invalid JWT**: WebSocket will close immediately
- **Network issues**: Automatic reconnection with exponential backoff
- **Server errors**: Error messages sent via WebSocket

### Best Practices
1. Always check `isConnected` before sending messages
2. Implement reconnection logic with exponential backoff
3. Handle connection failures gracefully
4. Store notifications locally for offline viewing
5. Implement heartbeat/ping mechanism for connection monitoring

## Production Considerations

### Security
- JWT tokens should be refreshed before expiry
- Use WSS (secure WebSocket) in production
- Validate all incoming messages

### Performance
- Limit notification history in frontend state
- Implement message queuing for offline users
- Use connection pooling for high traffic

### Monitoring
- Track WebSocket connection counts
- Monitor message delivery rates
- Log connection failures and errors

## Environment Variables

```bash
# Redis for Channels (required)
REDIS_URL=redis://localhost:6379/0

# WebSocket settings
WEBSOCKET_TIMEOUT=30
WEBSOCKET_MAX_CONNECTIONS=1000
```

## Troubleshooting

### Common Issues
1. **WebSocket won't connect**: Check JWT token validity and Redis connection
2. **Messages not received**: Verify user is in correct channel group
3. **High memory usage**: Implement message cleanup and connection limits
4. **Slow performance**: Check Redis performance and network latency

### Debug Commands
```python
# Check active connections
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()

# Test notification sending
from interactions.utils import send_notification_to_user
send_notification_to_user(user_id=1, title="Test", body="Test notification")
```
