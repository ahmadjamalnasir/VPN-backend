# Prime VPN API Documentation v2.0.0

## 🎯 Role-Based API Architecture

The API is designed with clear separation between **Mobile App** and **Admin Backoffice** endpoints, each with appropriate role-based access control.

## 🔐 ADMIN AUTHENTICATION

### Admin Login (`/api/v1/admin-auth`) - No Token Required
```http
POST /api/v1/admin-auth/login      # Admin login with username/password
```

## 📱 MOBILE APP ENDPOINTS

### Authentication (`/api/v1/auth`) - No Token Required
```http
POST /api/v1/auth/signup              # Register new user
POST /api/v1/auth/verify-email        # Verify email with OTP
POST /api/v1/auth/login              # Login and get JWT token
POST /api/v1/auth/forgot-password    # Send password reset OTP
POST /api/v1/auth/reset-password     # Reset password with OTP
```

### User Profile (`/api/v1/users/profile`) - JWT Required
```http
GET /api/v1/users/profile            # Get mobile-optimized user profile
```

### VPN Management (`/api/v1/vpn`) - JWT Required
```http
GET  /api/v1/vpn/servers?location=us-east&max_load=0.7&max_ping=50  # Get all servers (premium check at connection)
POST /api/v1/vpn/connect?user_id=123                                # Connect to VPN server (premium check enforced)
POST /api/v1/vpn/disconnect?connection_id=uuid&user_id=123&bytes_sent=1048576&bytes_received=2097152  # Disconnect with stats
GET  /api/v1/vpn/status?connection_id=uuid&user_id=123              # Get connection status with metrics
```

### User Subscriptions (`/api/v1/subscriptions`) - JWT Required
```http
# Public Plans
GET  /api/v1/subscriptions/plans                     # Get active subscription plans (Public)

# User Subscription Management
GET  /api/v1/subscriptions/users/{user_id}           # Get user's active subscription
POST /api/v1/subscriptions/users/{user_id}           # Assign subscription (self-purchase)
PATCH /api/v1/subscriptions/users/{user_id}/cancel   # Cancel subscription auto-renew
GET  /api/v1/subscriptions/users/{user_id}/history   # Get subscription history
```

### Real-time Updates (`/api/v1/websocket/connection`) - JWT Required
```http
WS /api/v1/websocket/connection?token=jwt_token        # Real-time connection status updates
```

## 🔧 ADMIN BACKOFFICE ENDPOINTS

### Admin - Dashboard (`/api/v1/admin`) - Role-Based Access
```http
# View Access (Admin + Super Admin)
GET  /api/v1/admin/dashboard                          # Admin dashboard stats
GET  /api/v1/admin/rate-limits/config                # Rate limiting config
```

### Admin - User Management (`/api/v1/admin`) - Role-Based Access

#### VPN User Management
```http
# View Access (Admin + Super Admin)
GET /api/v1/admin/vpn-users?skip=0&limit=100&search=john  # List all VPN users with pagination/search

# Modification Access (Super Admin Only)
PUT /api/v1/admin/vpn-user/{user_id}/status?is_active=true&is_premium=false  # Update VPN user status
```

#### Admin User Management
```http
# View Access (Admin + Super Admin)
GET  /api/v1/admin/admin-users?skip=0&limit=100       # List all admin users

# Modification Access (Super Admin Only)
POST /api/v1/admin/create-admin-user                  # Create new admin user
PUT  /api/v1/admin/admin-user/{admin_id}?password=string&full_name=string&role=admin  # Update admin user
DEL  /api/v1/admin/users/{admin_id}                   # Delete admin user
```

### Admin - Server Management (`/api/v1/admin`) - Role-Based Access
```http
# View Access (Admin + Super Admin)
GET  /api/v1/admin/servers                           # List all VPN servers

# Modification Access (Super Admin Only)
POST /api/v1/admin/add_server                        # Add new VPN server
PUT  /api/v1/admin/servers/{server_id}               # Update VPN server
DEL  /api/v1/admin/servers/{server_id}               # Delete VPN server
```

### Admin - Subscription Management (`/api/v1/admin/subscriptions`) - Admin JWT Required
```http
# Plan Management
GET  /api/v1/admin/subscriptions/plans               # Get all subscription plans
POST /api/v1/admin/subscriptions/plans               # Create new subscription plan
PUT  /api/v1/admin/subscriptions/plans/{plan_id}     # Update subscription plan
DEL  /api/v1/admin/subscriptions/plans/{plan_id}     # Deactivate subscription plan

# User Subscription Management
GET  /api/v1/admin/subscriptions/users/{user_id}           # Get user's active subscription
POST /api/v1/admin/subscriptions/users/{user_id}           # Assign subscription to user
PATCH /api/v1/admin/subscriptions/users/{user_id}/cancel   # Cancel user subscription
GET  /api/v1/admin/subscriptions/users/{user_id}/history   # Get subscription history
```

### Analytics (`/api/v1/analytics`) - Admin/Premium JWT Required
```http
GET /api/v1/analytics/usage/personal?days=30           # Personal usage analytics
GET /api/v1/analytics/servers/performance             # Server performance statistics
GET /api/v1/analytics/system/overview                 # System-wide overview metrics
GET /api/v1/analytics/locations/usage?days=30         # Usage statistics by location
```

### Health Monitoring (`/api/v1/health`) - No Token Required
```http
GET /api/v1/health/status                             # Comprehensive system health
GET /api/v1/health/metrics                            # System metrics and stats
GET /api/v1/health/ping                              # Simple health check
GET /api/v1/health/ready                             # Kubernetes readiness probe
GET /api/v1/health/live                              # Kubernetes liveness probe
```

### Admin Dashboard (`/api/v1/websocket/admin-dashboard`) - Admin JWT Required
```http
WS /api/v1/websocket/admin-dashboard?token=jwt_token  # Real-time dashboard updates
```

## 🔑 Authentication & Authorization

### JWT Token Authentication
All protected endpoints require JWT token in Authorization header:
```http
Authorization: Bearer <jwt_token>
```

### Role-Based Access Control
- **Mobile Users**: Access to own profile, connections, and subscriptions only
- **Premium Users**: Additional access to personal analytics
- **Admin Users**: Role-based access with different permission levels
  - **Super Admin**: Full system access (create/modify/delete users, servers, settings)
  - **Admin**: View-only access (read users, analytics, dashboard)
  - **Moderator**: Limited view access (basic analytics and user lists)
- **Rate Limiting**: Admin users are exempt from rate limiting

### Admin Authentication Flow
```bash
# Admin Login (Separate from Mobile Users)
curl -X POST http://localhost:8000/api/v1/admin-auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "admin_id": 1,
  "role": "super_admin",
  "full_name": "System Administrator"
}
```

### Mobile User Authentication Flow
```bash
# 1. Mobile User Registration
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "secure123",
    "phone": "+1234567890",
    "country": "US"
  }'

# 2. Email Verification
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "otp_code": "123456"}'

# 3. Login to Get JWT Token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "secure123"}'

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_id": 123,
  "is_premium": false
}
```

## 📊 API Response Examples

### Mobile User Profile
```json
{
  "user_id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "country": "US",
  "is_premium": false,
  "is_email_verified": true,
  "subscription_status": "none",
  "subscription_expires": null,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Mobile VPN Server List (All Users See All Servers)
```json
[
  {
    "id": "uuid",
    "hostname": "vpn-us-east-1",
    "location": "us-east",
    "ip_address": "203.0.113.1",
    "status": "active",
    "current_load": 0.25,
    "ping": 15,
    "is_premium": false,
    "created_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": "uuid",
    "hostname": "vpn-premium-eu-1",
    "location": "eu-west",
    "ip_address": "203.0.113.2",
    "status": "active",
    "current_load": 0.15,
    "ping": 25,
    "is_premium": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Mobile VPN Connection Response
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
  "wg_config": "[Interface]\nPrivateKey = <client_private_key>\nAddress = 10.0.123.45/32\nDNS = 1.1.1.1, 1.0.0.1\n\n[Peer]\nPublicKey = <server_public_key>\nEndpoint = 203.0.113.1:51820\nAllowedIPs = 0.0.0.0/0\nPersistentKeepalive = 25",
  "started_at": "2024-01-15T10:30:00Z",
  "status": "connected"
}
```

### Mobile VPN Status Response
```json
{
  "connection_id": "uuid",
  "status": "connected",
  "server": {
    "id": "uuid",
    "hostname": "vpn-us-east-1",
    "location": "us-east",
    "ip_address": "203.0.113.1",
    "is_premium": false
  },
  "client_ip": "10.0.123.45",
  "started_at": "2024-01-15T10:30:00Z",
  "ended_at": null,
  "duration_seconds": 3600,
  "bytes_sent": 1048576,
  "bytes_received": 2097152,
  "total_bytes": 3145728,
  "connection_speed_mbps": 6.99,
  "server_load": 0.35,
  "ping_ms": 15,
  "is_active": true
}
```

### Admin Login Response
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "admin_id": 1,
  "role": "super_admin",
  "full_name": "System Administrator"
}
```

### Create VPN User Request
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "secure123",
  "phone": "+1234567890",
  "country": "US"
}
```

### Create Admin User Request
```json
{
  "username": "admin_john",
  "email": "john.admin@company.com",
  "password": "admin123",
  "full_name": "John Admin",
  "role": "admin"
}
```

### Add VPN Server Request (Required: hostname, location, endpoint, public_key, tunnel_ip)
```bash
POST /api/v1/admin/add_server?hostname=test-server-1&location=United+States&endpoint=23.123.12.12:51820&public_key=SERVER_PUBLIC_KEY_HERE&tunnel_ip=10.221.12.11/32&allowed_ips=0.0.0.0/0&is_premium=false&status=active&max_connections=10
```

### Update VPN Server Request (All parameters optional)
```bash
PUT /api/v1/admin/servers/{server_id}?hostname=updated-server&location=Canada&endpoint=new.endpoint.com:51820&public_key=NEW_PUBLIC_KEY&tunnel_ip=10.0.0.1/32&allowed_ips=0.0.0.0/0&is_premium=true&status=active&max_connections=50
```

### Server Parameters
- **Required for Creation**: `hostname`, `location`, `endpoint`, `public_key`, `tunnel_ip`
- **Optional**: `allowed_ips` (default: "0.0.0.0/0"), `is_premium` (default: false), `status` (default: "active"), `max_connections` (default: 100)
- **Read-only**: `current_load` (only in GET response)
- **Validation**: `endpoint` must include port, `tunnel_ip` must include CIDR notation

### Server List Response
```json
[
  {
    "id": "uuid",
    "hostname": "test-server-1",
    "location": "United States",
    "endpoint": "23.123.12.12:51820",
    "public_key": "SERVER_PUBLIC_KEY_HERE",
    "tunnel_ip": "10.221.12.11/32",
    "allowed_ips": "0.0.0.0/0",
    "is_premium": false,
    "status": "active",
    "current_load": 0.25,
    "max_connections": 10,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Server Management Validation Rules
```bash
# Required Parameters (POST /api/v1/admin/add_server)
hostname=test-server-1              # Required: Server hostname
location=United+States              # Required: Server location  
endpoint=23.123.12.12:51820        # Required: Must include port
public_key=SERVER_PUBLIC_KEY_HERE   # Required: WireGuard public key
tunnel_ip=10.221.12.11/32          # Required: Must include CIDR notation

# Optional Parameters (with defaults)
allowed_ips=0.0.0.0/0              # Optional: Default "0.0.0.0/0"
is_premium=false                    # Optional: Default false
status=active                       # Optional: Default "active"
max_connections=100                 # Optional: Default 100

# Validation Errors
400 Bad Request: "endpoint must include port (e.g., 192.168.1.1:51820)"
400 Bad Request: "tunnel_ip must include CIDR notation (e.g., 10.0.0.1/32)"
400 Bad Request: "Max connections must be greater than 0"
400 Bad Request: "Invalid status. Must be: Active, Inactive, Maintenance"
```

### Role-Based Permission Examples
```bash
# Admin (View-Only) - Can access these endpoints:
GET /api/v1/users/                    # ✅ View VPN users
GET /api/v1/admin/admin-users         # ✅ View admin users
GET /api/v1/admin/servers             # ✅ View servers
GET /api/v1/admin/dashboard           # ✅ View dashboard

# Admin (View-Only) - Cannot access these endpoints:
POST /api/v1/admin/add_server         # ❌ 403: Super admin access required
PUT /api/v1/admin/servers/{id}        # ❌ 403: Super admin access required
POST /api/v1/admin/create-vpn-user    # ❌ 403: Super admin access required

# Super Admin - Can access all endpoints
POST /api/v1/admin/add_server         # ✅ Full access
PUT /api/v1/admin/servers/{id}        # ✅ Full access
DEL /api/v1/admin/servers/{id}        # ✅ Full access
```

### VPN User List
```json
[
  {
    "id": "uuid",
    "user_id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "country": "US",
    "is_active": true,
    "is_premium": false,
    "is_email_verified": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Admin Analytics Response
```json
{
  "period_days": 30,
  "total_connections": 1250,
  "total_data_gb": 450.5,
  "total_duration_hours": 2840.2,
  "daily_usage": [
    {
      "date": "2024-01-15",
      "connections": 45,
      "data_mb": 15420.8,
      "duration_minutes": 3680.5
    }
  ]
}
```

### System Health Response
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

## 🔌 WebSocket Messages

### Mobile Connection Status
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

// Connection Change Notification
{
  "type": "connection_change",
  "status": "disconnected",
  "data": {
    "duration_seconds": 3600,
    "bytes_sent": 1048576,
    "bytes_received": 2097152
  },
  "timestamp": "2024-01-15T14:30:00Z"
}
```

### Admin Dashboard Updates
```json
// Dashboard Statistics Update
{
  "type": "dashboard_update",
  "data": {
    "total_users": 1250,
    "active_users": 1100,
    "premium_users": 450,
    "total_servers": 25,
    "active_servers": 23,
    "active_connections": 89,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}

// System Alert
{
  "type": "system_alert",
  "alert_type": "server_overload",
  "message": "Server us-east-1 is at 95% capacity",
  "severity": "warning",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔒 Security Features

### Input Validation & Role Checking
```python
# Example: Admin endpoint with role verification
@router.get("/users/")
async def get_all_users(
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    # Verify admin access
    admin_result = await db.execute(select(User).where(User.id == current_user_id))
    admin_user = admin_result.scalar_one_or_none()
    if not admin_user or not admin_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
```

### Rate Limiting Headers
```http
# Rate limit headers in responses
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1642248600
```

### Error Responses
```json
// Authentication Error
{
  "detail": "Invalid token"
}

// Authorization Error
{
  "detail": "Admin access required"
}

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
```

## 🎯 Integration Guidelines

### Mobile App Integration
1. **Authentication Flow**: Implement signup → verify email → login → store JWT token
2. **Profile Management**: Use `/users/profile` for user info with subscription status
3. **VPN Connection**: Use `/vpn/connect`, `/vpn/disconnect`, and `/vpn/status` with real-time status via WebSocket
4. **Server Selection**: All users see all servers, premium check happens at connection time
5. **Error Handling**: Handle 403 "Upgrade to Premium required" errors with upgrade prompts

### Admin Panel Integration
1. **Dashboard**: Use WebSocket `/websocket/admin-dashboard` for real-time updates
2. **User Management**: Implement search, pagination, and status updates
3. **Analytics**: Display usage patterns and system performance metrics
4. **Server Management**: Monitor server health and manage configurations
5. **Role Verification**: Always verify admin status before showing admin features

### Database Alignment
- All APIs use proper foreign key relationships (UUIDs for internal, integers for external)
- User subscriptions correctly link `user.id` (UUID) to `plan.id` (UUID)
- Connection tracking properly references `user.id` and `server.id` (UUIDs)
- Readable IDs (`user_id`, `plan_id`) used in API endpoints for external references

## 🔧 Development Notes

### API Versioning
- All endpoints prefixed with `/api/v1/` for version control
- Clear separation between mobile and admin functionality with role-based paths
- Future versions will use `/api/v2/` prefix for backward compatibility

### Database Relations
```sql
-- Verified Foreign Key Relationships:
users.id (UUID) ← user_subscriptions.user_id (UUID)
subscription_plans.id (UUID) ← user_subscriptions.plan_id (UUID)
users.id (UUID) ← connections.user_id (UUID)
vpn_servers.id (UUID) ← connections.server_id (UUID)

-- Readable ID Usage:
User.user_id (int) - Used in mobile/admin API endpoints
SubscriptionPlan.plan_id (int) - Used in admin API endpoints
```

### Performance Optimizations
- Mobile endpoints return minimal data payloads
- Admin endpoints support pagination and search
- WebSocket connections separated by role (mobile vs admin)
- Database queries optimized with proper indexing on foreign keys

The API is now fully aligned with database structure and ready for production mobile and admin integrations.