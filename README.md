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
│   ├── api/v1/              # Modern API endpoints (ACTIVE)
│   │   ├── auth.py          # Authentication & OTP
│   │   ├── users.py         # User management & connections
│   │   ├── subscriptions.py # Subscription management
│   │   ├── vpn.py          # VPN servers & connections
│   │   ├── admin.py        # Admin dashboard & management
│   │   ├── mobile.py       # Mobile-optimized endpoints
│   │   ├── analytics.py    # Usage analytics & metrics
│   │   ├── health.py       # System health monitoring
│   │   └── websocket.py    # Real-time WebSocket APIs
│   ├── models/             # Database models
│   │   ├── user.py         # User with readable ID & premium status
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
│   └── main.py            # Application entry point
├── alembic/               # Database migrations
├── requirements.txt       # Python dependencies
└── API_DOCUMENTATION.md   # Complete API reference
```

## 🗑️ Removed Components (v2.0.0 Cleanup)

### **Duplicate Services Removed:**
- ❌ `app/services/auth_service.py` - **DUPLICATE** (replaced by `auth.py`)
- ❌ `app/services/payment_service.py` - **DUPLICATE** (replaced by `payment.py`)
- ❌ `app/services/subscription_service.py` - **NON-FUNCTIONAL** (referenced non-existent models)

### **Legacy API Structure Removed:**
- ❌ `app/routers/` - **OLD SYSTEM** (replaced by `app/api/v1/`)
  - `auth.py`, `users.py`, `vpn.py`, `payments.py`, `subscription.py`
- ❌ `app/dependencies/` - **OLD AUTH SYSTEM** (replaced by modern JWT auth)
- ❌ `app/schemas/vpn_server.py` - **DUPLICATE** (functionality moved to `vpn.py`)

### **Impact of Removals:**
- ✅ **No Functionality Lost** - All features migrated to modern system
- ✅ **Improved Performance** - Single async system instead of mixed sync/async
- ✅ **Better Security** - Consolidated auth with comprehensive validation
- ✅ **Cleaner Code** - No duplicate imports or circular dependencies

## 🔧 Step-by-Step Setup Guide

### 1. Environment Setup
```bash
# Clone repository
git clone <repository-url>
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
ALLOWED_ORIGINS: List[str] = ["https://your-frontend.com", "https://admin.your-domain.com"]
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
```sql
-- Create first admin user in database:
UPDATE users SET is_superuser = true WHERE email = 'admin@yourdomain.com';
```

## 📚 Understanding the Application

### Modern API Architecture (v2.0.0):
1. **Single Auth System** → JWT-based authentication across all endpoints
2. **Async-First** → All database operations use async SQLAlchemy
3. **Comprehensive Security** → Input validation, rate limiting, DDoS protection
4. **Real-time Features** → WebSocket support for live updates

### Core Flow:
1. **User Registration** → Email verification → Login (JWT token)
2. **Subscription Assignment** → Premium status update
3. **VPN Connection** → Server selection → WireGuard config
4. **Session Tracking** → Usage analytics → Billing data

### Key Components:

#### Authentication System (`app/services/auth.py`):
- JWT token generation and verification
- Password hashing with bcrypt
- Token-based route protection

#### Security Layer:
- `middleware/ddos_protection.py` → IP banning & request tracking
- `utils/security.py` → Input validation & sanitization
- `services/rate_limit_service.py` → Advanced rate limiting

#### VPN Management:
- `models/vpn_server.py` → Server definitions with premium flags
- `models/connection.py` → Session tracking with detailed stats
- `api/v1/vpn.py` → Connect/disconnect with WireGuard integration

## 🚀 Production Deployment Checklist

- [ ] Update JWT secret key
- [ ] Configure production database
- [ ] Set up Redis cluster
- [ ] Update Stripe live keys
- [ ] Implement email service
- [ ] Configure CORS origins
- [ ] Set up SSL certificates
- [ ] Create admin user
- [ ] Configure monitoring
- [ ] Set up backup strategy
- [ ] Replace WireGuard key placeholders
- [ ] Test all API endpoints

## 📖 API Documentation

Complete API reference available at: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 🔒 Security

Security implementation details: [SECURITY.md](SECURITY.md)

## 📝 License

MIT License