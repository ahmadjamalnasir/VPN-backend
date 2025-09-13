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

## 🏗️ Architecture Overview

```
VPN-backend/
├── app/
│   ├── api/v1/              # Role-based API endpoints
│   │   ├── auth.py          # Mobile: Authentication & OTP
│   │   ├── admin_auth.py    # Admin: Separate admin authentication
│   │   ├── users.py         # Mobile: /profile | Admin: /list, /by-id, /status
│   │   ├── subscriptions.py # Mobile: /user/plans | Admin: /plans
│   │   ├── vpn.py          # Mobile: /connect, /disconnect | Admin: /servers
│   │   ├── admin.py        # Admin: Dashboard & server management
│   │   ├── mobile.py       # Legacy mobile endpoints
│   │   ├── analytics.py    # Admin/Premium: Usage analytics & metrics
│   │   ├── health.py       # Admin: System health monitoring
│   │   └── websocket.py    # Mobile: /connection | Admin: /admin-dashboard
│   ├── models/             # Database models
│   │   ├── user.py         # User with readable ID & premium status
│   │   ├── admin_user.py   # Separate admin users with role-based access
│   │   ├── subscription_plan.py    # Independent subscription plans
│   │   ├── user_subscription.py    # User-plan assignments
│   │   ├── vpn_server.py          # VPN servers with premium flag
│   │   ├── connection.py          # Connection tracking with stats
│   │   └── otp_verification.py    # Email verification & password reset
│   ├── schemas/            # Pydantic request/response models
│   ├── services/           # Business logic & external services (CLEANED)
│   │   ├── auth.py         # JWT & password services
│   │   ├── otp_service.py  # Email verification
│   │   ├── payment.py      # Stripe integration
│   │   ├── vpn_service.py  # VPN server management
│   │   ├── metrics_service.py # Real-time metrics
│   │   ├── rate_limit_service.py # Advanced rate limiting
│   │   ├── redis_service.py # Redis operations
│   │   └── wireguard_service.py # WireGuard integration
│   ├── middleware/         # Security middleware (DDoS, rate limiting)
│   ├── utils/             # Security utilities & helpers
│   ├── core/              # Configuration & settings
│   └── main.py            # Application entry point with role-based routing
├── alembic/               # Database migrations
├── requirements.txt       # Python dependencies
└── API_DOCUMENTATION.md   # Complete API reference
```


### **Impact of Removals:**
- ✅ **No Functionality Lost** - All features migrated to role-based system
- ✅ **Improved Security** - Proper role checking on all endpoints
- ✅ **Better Performance** - Single async system with optimized queries
- ✅ **Cleaner Architecture** - Clear separation between mobile and admin APIs

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

# Stripe Payment
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

## 🔑 Critical Production Placeholders

### ⚠️ MUST UPDATE BEFORE PRODUCTION:

#### 1. JWT Security (`app/core/config.py`)
```python
# CHANGE THIS:
JWT_SECRET: str = "your-secret-key-change-in-production"
# TO: Strong random secret (use: openssl rand -hex 32)
JWT_SECRET: str = "your-actual-256-bit-secret-key"
```

#### 2. Database Configuration (`.env`)
```env
# CHANGE THIS:
DATABASE_URL="postgresql+asyncpg://username:password@localhost:5432/primevpn"
# TO: Production database credentials
DATABASE_URL="postgresql+asyncpg://prod_user:secure_password@prod-db:5432/primevpn"
```

#### 3. Stripe Payment Keys (`.env`)
```env
# CHANGE THESE TEST KEYS:
STRIPE_SECRET_KEY="sk_test_your_stripe_secret_key"
STRIPE_PUBLISHABLE_KEY="pk_test_your_stripe_publishable_key"
# TO: Live Stripe keys
STRIPE_SECRET_KEY="sk_live_actual_secret_key"
STRIPE_PUBLISHABLE_KEY="pk_live_actual_publishable_key"
```

#### 4. CORS Origins (`app/core/config.py`)
```python
# CHANGE THIS:
ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://yourdomain.com"]
# TO: Your actual domains
ALLOWED_ORIGINS: List[str] = ["https://your-mobile-app.com", "https://admin.your-domain.com"]
```

#### 5. Email Service (`app/services/otp_service.py`)
```python
# IMPLEMENT ACTUAL EMAIL SERVICE:
# Replace mock email sending with real SMTP/SendGrid/AWS SES
async def send_otp_email(email: str, otp_code: str, purpose: str):
    # TODO: Implement actual email service
    pass
```

#### 6. WireGuard Keys (`app/services/wireguard_service.py`)
```python
# REPLACE PLACEHOLDER:
def generate_wireguard_keys():
    # TODO: Use actual WireGuard key generation
    private_key = os.urandom(32).hex()  # PLACEHOLDER
    public_key = os.urandom(32).hex()   # PLACEHOLDER
    return private_key, public_key
```

#### 7. Admin User Creation
```bash
# Create separate admin user (recommended approach):
python3 create_admin_user.py

# Default admin credentials:
# Username: admin
# Password: admin123
# Email: admin@primevpn.com
```

## 📚 Understanding the Application

### Role-Based API Architecture (v2.0.0):
1. **Mobile-First Design** → Optimized endpoints for mobile app integration
2. **Admin Role Separation** → Secure admin-only endpoints with proper verification
3. **Separate User Systems** → VPN users and admin users in separate tables with dedicated creation endpoints
4. **JWT-Based Security** → Token validation with role checking on all protected routes
5. **Real-time Features** → Separate WebSocket channels for mobile and admin

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
- Minimal response payloads for mobile networks
- Premium status filtering for server lists
- Real-time connection status via WebSocket

#### Admin Management APIs:
- Comprehensive user management with search/pagination
- System analytics and performance monitoring
- Real-time dashboard updates via WebSocket

## 🚀 Production Deployment Checklist

- [ ] Update JWT secret key
- [ ] Configure production database
- [ ] Set up Redis cluster
- [ ] Update Stripe live keys
- [ ] Implement email service
- [ ] Configure CORS origins for mobile app and admin panel
- [ ] Set up SSL certificates
- [ ] Create admin user
- [ ] Configure monitoring and alerts
- [ ] Set up backup strategy
- [ ] Replace WireGuard key placeholders
- [ ] Test mobile app integration
- [ ] Test admin panel integration

## 📖 API Documentation

Complete API reference with mobile and admin endpoints: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 🔒 Security

Security implementation with role-based access control: [SECURITY.md](SECURITY.md)

## 📝 License

MIT License