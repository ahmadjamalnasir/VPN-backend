# Prime VPN API Documentation v2.0.0

## 🔌 Complete API Endpoints

### Authentication (`/api/v1/auth`) - No Token Required
```http
POST /signup              # Register user with name, email, password, phone, country
POST /verify-email        # Verify email with OTP code
POST /login              # Login and get JWT token
POST /forgot-password    # Send password reset OTP
POST /reset-password     # Reset password with OTP verification
```

### Users (`/api/v1/users`) - Requires JWT Token
```http
GET  /connections?user_id=123&limit=50     # Connection history (Premium only)
PUT  /update?user_id=123                   # Update name, phone, country, password
```

### Subscriptions (`/api/v1/subscriptions`) - Requires JWT Token
```http
POST /plans/create?name=Premium&plan_type=monthly&price=9.99&duration_days=30&is_premium=true  # Create plan (Admin)
GET  /plans                                # List all plans (Public)
GET  /users/{user_id}                      # User subscription history
POST /assign?user_id=123&plan_id=2&auto_renew=true&payment_method=stripe  # Assign plan to user
PUT  /cancel/{user_id}                     # Cancel subscription
```

### VPN (`/api/v1/vpn`) - Requires JWT Token
```http
GET  /servers?is_premium=true&location=us-east  # Get VPN servers (Public)
POST /connect?user_id=123                       # Connect with profile validation
POST /disconnect?connection_id=uuid&user_id=123&bytes_sent=1048576&bytes_received=2097152  # Disconnect with stats
```

### Admin (`/api/v1/admin`) - Requires Admin JWT Token
```http
GET  /dashboard                           # Admin dashboard statistics
GET  /users?skip=0&limit=100&search=john # All users with pagination/search
PUT  /users/{user_id}/status             # Update user status (active/premium/superuser)
POST /servers                            # Create VPN server
PUT  /servers/{server_id}                # Update server configuration
DELETE /servers/{server_id}              # Delete server (if no active connections)
```

### Mobile (`/api/v1/mobile`) - Requires JWT Token
```http
GET  /profile                            # Mobile-optimized user profile
GET  /servers/quick                      # Quick server list with flags & load
POST /connect/quick                      # Quick connect for mobile apps
POST /disconnect?connection_id=uuid      # Mobile disconnect
GET  /status                            # Current connection status
```

### Analytics (`/api/v1/analytics`) - Requires Premium/Admin JWT Token
```http
GET  /usage/personal?days=30             # Personal usage analytics
GET  /servers/performance                # Server performance statistics
GET  /system/overview                    # System-wide overview metrics
GET  /locations/usage?days=30            # Usage statistics by location
```

### Health (`/health`) - No Token Required
```http
GET  /status                            # Comprehensive health check with DB/Redis/System
GET  /metrics                           # System metrics and connection stats
GET  /ping                             # Simple ping for load balancers
GET  /ready                            # Readiness probe for Kubernetes
GET  /live                             # Liveness probe for Kubernetes
```

### WebSocket (`/ws`) - Requires JWT Token as Query Parameter
```http
WS   /connection-status?token=jwt_token  # Real-time connection status updates
WS   /system-alerts?token=jwt_token     # System alerts (Admin only)
```

## 🔑 Authentication System (v2.0.0)

### JWT Token Authentication
All endpoints except `/auth` and `/health` require JWT token in Authorization header:
```http
Authorization: Bearer <jwt_token>
```

### Token Generation
```bash
# Login to get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_id": 123,
  "is_premium": true
}
```

### Token Usage
```bash
# Use token in subsequent requests
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  http://localhost:8000/api/v1/users/connections?user_id=123
```

## 📊 API Response Examples

### User Registration Flow
```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com", 
    "password": "secure123",
    "phone": "+1234567890",
    "country": "US"
  }'

# Response:
{
  "id": "uuid",
  "user_id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "is_premium": false,
  "is_email_verified": false,
  "created_at": "2024-01-15T10:30:00Z"
}

# 2. Verify Email
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "otp_code": "123456"}'

# 3. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "secure123"}'
```

### Mobile Server List
```json
{
  "servers": [
    {
      "id": "uuid",
      "name": "US-EAST - Server 1",
      "location": "us-east",
      "ping": 15,
      "load_percentage": 25,
      "is_premium": false,
      "flag_emoji": "🇺🇸"
    },
    {
      "id": "uuid",
      "name": "EU-WEST - Server 2", 
      "location": "eu-west",
      "ping": 45,
      "load_percentage": 60,
      "is_premium": true,
      "flag_emoji": "🇪🇺"
    }
  ]
}
```

### VPN Connection Response
```json
{
  "connection_id": "uuid",
  "server": {
    "id": "uuid",
    "hostname": "vpn-us-east-1",
    "location": "us-east",
    "ip_address": "203.0.113.1",
    "is_premium": false
  },
  "client_ip": "10.0.123.45",
  "wg_config": "[Interface]\nPrivateKey = <client_private_key>\nAddress = 10.0.123.45/32\n...",
  "started_at": "2024-01-15T10:30:00Z",
  "status": "connected"
}
```

### Analytics Response
```json
{
  "period_days": 30,
  "total_connections": 150,
  "total_data_gb": 25.5,
  "total_duration_hours": 48.2,
  "daily_usage": [
    {
      "date": "2024-01-15",
      "connections": 5,
      "data_mb": 850.2,
      "duration_minutes": 120.5
    }
  ]
}
```

### Admin Dashboard Response
```json
{
  "total_users": 1250,
  "active_users": 1100,
  "premium_users": 450,
  "total_servers": 25,
  "active_servers": 23,
  "active_connections": 89,
  "daily_connections": 1450
}
```

### Health Status Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "database": {
    "status": "healthy",
    "response_time_ms": 12.5
  },
  "redis": {
    "status": "healthy", 
    "response_time_ms": 3.2
  },
  "servers": {
    "active_count": 23,
    "total_connections": 89
  },
  "system": {
    "cpu_usage_percent": 45.2,
    "memory_usage_percent": 67.8,
    "disk_usage_percent": 23.1
  }
}
```

### WebSocket Messages
```json
// Connection Status Update
{
  "type": "connection_status",
  "status": "connected",
  "data": {
    "connection_id": "uuid",
    "server_location": "us-east",
    "client_ip": "10.0.123.45",
    "duration_seconds": 3600,
    "connected_at": "2024-01-15T10:30:00Z"
  }
}

// System Alert (Admin)
{
  "type": "system_alert",
  "alert_type": "server_overload",
  "message": "Server us-east-1 is at 95% capacity",
  "severity": "warning",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔒 Security Features

### Input Validation
- Email format validation
- IP address validation  
- Suspicious pattern detection
- SQL injection prevention
- XSS protection

### Rate Limiting
```http
# Rate limit headers in responses
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1642248600
```

### Error Responses
```json
// Rate Limited
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded for auth_login",
  "retry_after": 60,
  "remaining": 0
}

// DDoS Protection
{
  "error": "IP_BANNED", 
  "message": "Your IP has been temporarily banned due to suspicious activity",
  "retry_after": 300
}

// Authentication Error
{
  "detail": "Invalid token"
}
```

## 🎯 Integration Ready Features

### Backoffice Integration
- Complete admin dashboard with real-time stats
- User management with search and pagination
- Server management (CRUD operations)
- System health monitoring
- Analytics and reporting

### Mobile App Integration  
- Optimized endpoints for mobile UI
- Quick connect functionality
- Real-time connection status via WebSocket
- Flag emojis for server locations
- Minimal data transfer for mobile networks

### Production Features
- Comprehensive health checks for load balancers
- DDoS protection with IP banning
- Advanced rate limiting per endpoint
- System metrics and monitoring
- Real-time WebSocket updates
- Async-first architecture for high performance

## 🔧 Development Notes

### API Versioning
- All endpoints prefixed with `/api/v1/`
- Future versions will use `/api/v2/`, etc.

### Database Relations
- Users ↔ UserSubscriptions ↔ SubscriptionPlans
- Users ↔ Connections ↔ VPNServers
- Proper foreign key constraints with CASCADE/SET NULL

### Authentication Flow
- JWT tokens contain `user_id` and `sub` (email)
- Tokens expire after 30 minutes (configurable)
- All protected routes verify token and extract user_id

### Error Handling
- Consistent error response format
- Proper HTTP status codes
- Security-conscious error messages (no information leakage)