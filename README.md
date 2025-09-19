# Prime VPN Backend v2.0.0

A production-ready VPN backend API with comprehensive admin panel, mobile optimization, real-time analytics, and enterprise-grade security features.

## 🚀 Features

- 🔐 **JWT Authentication** with email verification & password reset
- 👤 **User Management** with readable IDs & premium subscriptions
- 💳 **Subscription System** with auto-renewal & payment tracking
- 🌐 **VPN Server Management** with premium/free tier separation
- 📊 **Real-time Analytics** with usage tracking & performance metrics
- 🛡️ **Advanced Security** with DDoS protection & rate limiting
- 📱 **Mobile Optimized APIs** with quick connect & real-time status
- 🔧 **Admin Dashboard** with comprehensive management tools
- 🔌 **WebSocket Support** for real-time updates
- 📈 **Health Monitoring** with system metrics & alerts

## 🗄️ Database Structure

### Core Tables & Relationships

```sql
-- User Management (Separate Systems)
users (UUID id, int user_id, email, is_premium, ...)
admin_users (UUID id, username, role, ...)

-- Subscription System (4-Table Structure)
subscription_plans (UUID id, int plan_id, name, price_usd, duration_days, features JSONB, status)
user_subscriptions (UUID id, user_id FK→users.id, plan_id FK→subscription_plans.id, status, auto_renew)
payments (UUID id, user_id FK→users.id, subscription_id FK→user_subscriptions.id, amount_usd, status)
vpn_usage_logs (UUID id, user_id FK→users.id, server_id FK→vpn_servers.id, data_used_mb)

-- VPN Infrastructure
vpn_servers (UUID id, hostname, location, endpoint, public_key, is_premium, status, current_load)
connections (UUID id, user_id FK→users.id, server_id FK→vpn_servers.id, client_ip, status, bytes_sent/received)
otp_verification (UUID id, email, otp_code, purpose, expires_at)
```

### Key Relationships
- **Users ↔ Subscriptions**: One-to-many (users.id ← user_subscriptions.user_id)
- **Plans ↔ Subscriptions**: One-to-many (subscription_plans.id ← user_subscriptions.plan_id)
- **Subscriptions ↔ Payments**: One-to-many (user_subscriptions.id ← payments.subscription_id)
- **Users ↔ Connections**: One-to-many (users.id ← connections.user_id)
- **Servers ↔ Connections**: One-to-many (vpn_servers.id ← connections.server_id)
- **Users ↔ Usage Logs**: One-to-many (users.id ← vpn_usage_logs.user_id)

## 🏗️ Architecture Overview

```
VPN-backend/
├── app/
│   ├── api/v1/              # Role-based API endpoints
│   │   ├── auth.py          # Mobile: Authentication & OTP
│   │   ├── admin_auth.py    # Admin: Separate admin authentication
│   │   ├── users.py         # Mobile: /profile | Admin: /list, /by-id, /status
│   │   ├── user_subscriptions.py # Mobile: /user/plans | Admin: /plans
│   │   ├── admin_subscriptions.py # Admin: Full subscription management
│   │   ├── payments.py      # Payment processing & webhooks
│   │   ├── vpn.py          # Mobile: /servers, /connect, /disconnect, /status
│   │   ├── admin.py        # Admin: Dashboard & server management
│   │   ├── analytics.py    # Admin/Premium: Usage analytics & metrics
│   │   ├── health.py       # Admin: System health monitoring
│   │   └── websocket.py    # Mobile: /connection | Admin: /admin-dashboard
│   ├── models/             # Database models (8 core tables)
│   ├── schemas/            # Pydantic request/response models
│   ├── services/           # Business logic & external services
│   ├── middleware/         # Security middleware (DDoS, rate limiting)
│   ├── utils/             # Security utilities & helpers
│   ├── core/              # Configuration & settings
│   └── main.py            # Application entry point with role-based routing
├── alembic/               # Database migrations
├── requirements.txt       # Python dependencies
└── API_DOCUMENTATION.md   # Complete API reference
```

## ⚠️ CRITICAL PRODUCTION UPDATES REQUIRED

### 🔑 Security Configuration

#### 1. JWT Security (`app/core/config.py`)
```python
# CHANGE THIS PLACEHOLDER:
JWT_SECRET: str = "your-secret-key-change-in-production"
# TO: Strong random secret
JWT_SECRET: str = "your-actual-256-bit-secret-key"  # Use: openssl rand -hex 32
```

#### 2. Database Configuration (`.env`)
```env
# CHANGE PLACEHOLDER:
DATABASE_URL="postgresql+asyncpg://username:password@localhost:5432/primevpn"
# TO: Production credentials
DATABASE_URL="postgresql+asyncpg://prod_user:secure_password@prod-db:5432/primevpn"
```

#### 3. Payment Provider Integration (`app/services/payment.py`)
```python
# REPLACE ENTIRE FILE WITH PROVIDER INTEGRATION:
# Current: Placeholder functions
# Required: Real Stripe/PayPal/Razorpay SDK integration

# Environment Variables Required:
STRIPE_SECRET_KEY="sk_live_your_actual_key"  # Not placeholder
STRIPE_WEBHOOK_SECRET="whsec_your_actual_secret"  # Not placeholder

# Webhook URL to configure in provider dashboard:
# https://yourdomain.com/api/v1/payments/callback
```

#### 4. Email Service (`app/services/otp_service.py`)
```python
# REPLACE MOCK IMPLEMENTATION:
async def send_otp_email(email: str, otp_code: str, purpose: str):
    # TODO: Implement actual email service (SMTP/SendGrid/AWS SES)
    pass  # Currently just logs - NO EMAILS SENT
```

#### 5. WireGuard Integration (`app/services/wireguard_service.py`)
```python
# REPLACE PLACEHOLDER IMPLEMENTATION:
def generate_wireguard_keys():
    # TODO: Use actual WireGuard key generation library
    private_key = os.urandom(32).hex()  # PLACEHOLDER - NOT REAL KEYS
    public_key = os.urandom(32).hex()   # PLACEHOLDER - NOT REAL KEYS
    return private_key, public_key
```

#### 6. CORS Origins (`app/core/config.py`)
```python
# UPDATE FOR PRODUCTION:
ALLOWED_ORIGINS: List[str] = ["https://your-mobile-app.com", "https://admin.your-domain.com"]
ALLOWED_HOSTS: List[str] = ["your-domain.com", "api.your-domain.com"]
```

### 🛡️ Security Features (Already Implemented)
- ✅ **DDoS Protection**: Multi-layer with IP banning
- ✅ **Rate Limiting**: Endpoint-specific with burst allowance
- ✅ **Input Sanitization**: Log injection prevention
- ✅ **SQL Injection Protection**: Parameterized queries
- ✅ **Authentication Security**: JWT with bcrypt password hashing
- ✅ **Role-Based Access**: Admin/User separation with proper verification

## 🔧 Step-by-Step Setup Guide

### 1. Environment Setup
```bash
# Clone repository
git clone <https://github.com/ahmadjamalnasir/VPN-backend>
cd VPN-backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Configuration
```bash
# Install PostgreSQL
# Create database: primevpn

# Update database URL in .env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/primevpn
```

### 3. Redis Setup (Required for Security Features)
```bash
# Install Redis
# Start Redis server: redis-server

# Update Redis URL in .env
REDIS_URL=redis://localhost:6379
```

### 4. Environment Variables (.env file)
```env
# Application
APP_NAME="Prime VPN"
DEBUG=true

# JWT Authentication
JWT_SECRET="your-secret-key-change-in-production"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL="postgresql+asyncpg://username:password@localhost:5432/primevpn"

# Redis
REDIS_URL="redis://localhost:6379"

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
ALLOWED_HOSTS=["localhost","127.0.0.1","yourdomain.com"]

# Payment Provider (UPDATE WITH REAL KEYS)
STRIPE_SECRET_KEY="sk_live_your_stripe_secret_key"
STRIPE_PUBLISHABLE_KEY="pk_live_your_stripe_publishable_key"
STRIPE_WEBHOOK_SECRET="whsec_your_webhook_secret"

# Security
DDOS_PROTECTION_ENABLED=true
RATE_LIMIT_ENABLED=true
DDOS_WHITELIST_IPS=["127.0.0.1","::1"]
```

### 5. Database Migration
```bash
# Initialize Alembic (if not done)
alembic init alembic

# Run migrations
alembic upgrade head

# Insert sample data
python insert_subscription_plans.py
python insert_sample_data.py
```

### 6. Start Server
```bash
python start_server.py
# Server runs on http://localhost:8000
# API docs: http://localhost:8000/docs
```

## 📚 Understanding the Application

### Role-Based API Architecture (v2.0.0):
1. **Mobile-First Design** → Optimized endpoints for mobile app integration
2. **Admin Role Separation** → Secure admin-only endpoints with proper verification
3. **Separate User Systems** → VPN users and admin users in separate tables with dedicated creation endpoints
4. **Role-Based Permissions** → Super Admin (full access) vs Admin (view-only access)
5. **JWT-Based Security** → Token validation with role checking on all protected routes
6. **Real-time Features** → Separate WebSocket channels for mobile and admin

### Core Flow:
1. **Mobile User Registration** → Email verification → Login (JWT token)
2. **Admin User Management** → Create/update users, assign subscriptions
3. **VPN Connection Flow** → Mobile connects → Real-time status → Admin monitoring
4. **Analytics & Monitoring** → Usage tracking → Admin dashboard → System alerts

### Key Components:

#### Role-Based Authentication:
- `auth.py` → Mobile authentication (signup, login, verify)
- `admin_auth.py` → Admin authentication (separate login system)
- `users.py` → Mobile profile + VPN user management
- `user_management.py` → Separate VPN user and admin user creation
- JWT tokens with role verification on all protected endpoints

#### Mobile-Optimized APIs:
- **Server Visibility**: All users can view all servers (premium check at connection time)
- **Minimal Payloads**: Optimized response sizes for mobile networks
- **Real-time Updates**: WebSocket connection status and metrics
- **Premium Enforcement**: Clear upgrade prompts for premium server access

#### Admin Management APIs:
- Comprehensive user management with search/pagination
- System analytics and performance monitoring
- Real-time dashboard updates via WebSocket
- Role-based permissions (Super Admin vs Admin)

#### Role-Based Permissions:
- **Super Admin** (`SUPER_ADMIN`): Full system access
  - Create/modify/delete VPN users and admin users
  - Manage VPN servers (create/update/delete)
  - Update user status and permissions
  - All view permissions
- **Admin** (`ADMIN`): View-only access
  - View VPN users and admin users
  - View dashboard and analytics
  - View system health and metrics
  - Cannot create or modify anything
- **Moderator** (`MODERATOR`): Limited view access
  - Basic user lists and analytics
  - Limited dashboard access

## 📋 Production Deployment Checklist
- [ ] Update JWT secret key (256-bit random)
- [ ] Configure production database with SSL
- [ ] Set up Redis cluster for rate limiting
- [ ] Integrate real payment provider (Stripe/PayPal)
- [ ] Implement email service (SMTP/SendGrid/AWS SES)
- [ ] Replace WireGuard key generation with real library
- [ ] Update CORS origins for mobile app and admin panel
- [ ] Set up SSL certificates and HTTPS
- [ ] Create admin user: `python create_admin_user.py`
- [ ] Configure monitoring and alerts
- [ ] Set up automated backups
- [ ] Test mobile app integration
- [ ] Test admin panel integration
- [ ] Configure payment provider webhooks

## 📖 API Documentation

Complete API reference with mobile and admin endpoints: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 🔧 WireGuard Server Configuration

### Minimum WireGuard Server Details Required

The client needs these essential details for VPN connection:

- **`public_key`** → The server's WireGuard public key (must be a real base64-like key, not "usa.org")
- **`endpoint`** → The server's reachable IP and port (e.g., 23.123.12.12:51820)
- **`allowed_ips`** → What traffic should go through this peer (usually 0.0.0.0/0 for all traffic)
- **`tunnel_ip`** → The IP inside the tunnel with CIDR notation (e.g., 10.221.12.11/32)

### Database Structure

**VPN Servers Table Fields:**
- `hostname` - Server hostname
- `location` - Server location
- `endpoint` - External server endpoint (IP:port)
- `public_key` - WireGuard public key
- `tunnel_ip` - Internal tunnel IP with CIDR
- `allowed_ip` - Allowed IPs for routing (default: 0.0.0.0/0)
- `ip_address` - Extracted IP from tunnel_ip (auto-populated)
- `is_premium` - Premium server flag
- `status` - Server status (active/inactive/maintenance)
- `current_load` - Current server load (0.0-1.0, read-only)
- `max_connections` - Maximum allowed connections

### Server Parameters

**Create Server** (`POST /api/v1/admin/add_server`):
- `hostname` - Server hostname (required)
- `location` - Server location (required)
- `endpoint` - Server endpoint IP:port (required)
- `public_key` - Server WireGuard public key (required)
- `tunnel_ip` - Tunnel IP with CIDR (required, e.g., 10.221.12.11/32)
- `allowed_ips` - Allowed IPs (optional, default: 0.0.0.0/0)
- `is_premium` - Premium flag (optional, default: false)
- `status` - Server status (optional, default: active)
- `max_connections` - Maximum connections (optional, default: 100)

**Update Server** (`PUT /api/v1/admin/servers/{server_id}`):
- All above parameters can be updated (all optional)
- `current_load` - Only shown in server listing (read-only, not editable)

## 🔒 Security Implementation

### ✅ Security Measures Active
- **Package Security**: All vulnerabilities fixed, updated to latest secure versions
- **Log Injection Prevention**: All user inputs sanitized before logging
- **Input Validation**: Email, IP address, and identifier validation across all endpoints
- **SQL Injection Protection**: Parameterized queries and type checking
- **Rate Limiting**: Multi-layer DDoS protection with IP whitelisting
- **Authentication**: JWT with secure algorithms and bcrypt password hashing
- **Role-Based Access**: Separate admin/user systems with proper verification

### 🛡️ Security Monitoring
Monitor these metrics via admin dashboard:
- Rate limit violations and banned IPs
- Failed authentication attempts
- Suspicious activity patterns
- System health and performance metrics

### 🔍 Security Testing
```bash
# Run security test suite
pytest tests/test_security_fixes.py -v
```

## 📝 License

MIT License