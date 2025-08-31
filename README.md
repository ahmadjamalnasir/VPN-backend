# Prime VPN Backend

A robust and secure backend service for managing VPN connections, user subscriptions, and payments.

## 🚀 Features

- 🔐 Secure User Authentication & Authorization
- 🌐 VPN Server Management
- 💳 Subscription Plans & Billing
- 📊 Real-time Server Metrics
- 🔄 Automatic Server Selection
- 💰 Payment Processing Integration
- 🛡️ Enhanced Security Measures

## 🛠️ Tech Stack

### Backend Framework
- FastAPI (Python 3.9+)
- Uvicorn ASGI Server
- WebSocket Support for Real-time Communication

### Database
- PostgreSQL 14
- SQLAlchemy ORM
- Alembic for Database Migrations

### Authentication & Security
- JWT (JSON Web Tokens)
- Bcrypt for Password Hashing
- Email Validation
- Rate Limiting

### Caching & Performance
- Redis for Session Management and Caching
- Connection Pooling

### Payment Processing
- Stripe Integration
- PayPal Integration (optional)

### Development Tools
- Poetry for Dependency Management
- Black for Code Formatting
- Flake8 for Linting
- Pytest for Unit Testing

## 📁 Project Structure

```
VPN-backend/
├── alembic/                  # Database migrations
│   ├── versions/            # Migration versions
│   └── env.py              # Migration environment
├── app/
│   ├── main.py             # Application entry point
│   ├── config.py           # Configuration settings
│   ├── database.py         # Database connection
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   └── routers/            # API endpoints
├── tests/                   # Test suite
├── .env                     # Environment variables
├── alembic.ini             # Alembic configuration
└── requirements.txt         # Project dependencies
```

## 🚦 API Documentation

All API endpoints are prefixed with `/api/v1` for versioning. Authentication is handled via JWT tokens passed in the `Authorization` header.

### 🔐 Authentication & Authorization
```http
# User Registration and Authentication
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh-token
POST /api/v1/auth/logout
POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password
POST /api/v1/auth/verify-email

# Session Management
GET /api/v1/auth/sessions
DELETE /api/v1/auth/sessions/{session_id}
DELETE /api/v1/auth/sessions/all
```

#### Authentication Response Example
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "is_verified": true,
        "subscription_status": "active",
        "subscription_expiry": "2025-12-31T23:59:59Z"
    }
}
```

### 👤 User Management
```http
# Profile Management
GET /api/v1/users/me
PUT /api/v1/users/me
PATCH /api/v1/users/me/password

# Device Management
GET /api/v1/users/me/devices
POST /api/v1/users/me/devices
DELETE /api/v1/users/me/devices/{device_id}

# Admin Routes
GET /api/v1/users
GET /api/v1/users/{user_id}
PUT /api/v1/users/{user_id}/status
```

#### User Profile Response Example
```json
{
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2025-01-01T00:00:00Z",
    "is_verified": true,
    "subscription": {
        "status": "active",
        "plan": "premium",
        "expiry_date": "2025-12-31T23:59:59Z",
        "auto_renew": true
    },
    "devices": [
        {
            "id": "device_uuid",
            "name": "iPhone 15",
            "last_connected": "2025-08-31T15:30:00Z",
            "ip_address": "192.168.1.1"
        }
    ]
}
```

### 🌐 VPN Servers
```http
# Server Management
GET /api/v1/servers
GET /api/v1/servers/{server_id}
GET /api/v1/servers/recommended

# Connection Management
POST /api/v1/connection/connect
POST /api/v1/connection/disconnect
GET /api/v1/connection/status
GET /api/v1/connection/statistics

# Server Filtering
GET /api/v1/servers?country=US&streaming=true&protocol=wireguard
```

#### Server Response Example
```json
{
    "servers": [
        {
            "id": "server_uuid",
            "hostname": "us-east-1.vpn.example.com",
            "country": "United States",
            "city": "New York",
            "ip_address": "10.0.0.1",
            "protocols": ["wireguard", "openvpn"],
            "status": "operational",
            "load": 45.5,
            "ping": 25,
            "bandwidth": {
                "download": 1000,
                "upload": 1000
            },
            "streaming_services": ["netflix", "hulu", "prime"],
            "features": ["double_vpn", "obfuscation"]
        }
    ],
    "total": 100,
    "page": 1,
    "per_page": 20
}
```

### 💳 Subscriptions & Billing
```http
# Subscription Management
GET /api/v1/subscriptions/plans
GET /api/v1/subscriptions/status
POST /api/v1/subscriptions/subscribe
PUT /api/v1/subscriptions/cancel
PUT /api/v1/subscriptions/resume

# Billing
GET /api/v1/billing/history
GET /api/v1/billing/invoices/{invoice_id}
PUT /api/v1/billing/payment-method
```

#### Subscription Plan Response Example
```json
{
    "plans": [
        {
            "id": "premium_monthly",
            "name": "Premium Monthly",
            "price": 9.99,
            "currency": "USD",
            "billing_period": "monthly",
            "features": [
                "unlimited_bandwidth",
                "all_locations",
                "5_devices"
            ],
            "details": {
                "max_devices": 5,
                "max_connections": 5,
                "streaming_support": true
            }
        }
    ]
}
```

### 💰 Payments
```http
# Payment Processing
POST /api/v1/payments/create-intent
POST /api/v1/payments/confirm
POST /api/v1/payments/webhook

# Refunds
POST /api/v1/payments/refund
GET /api/v1/payments/refund/{refund_id}
```

### 📊 Analytics & Metrics
```http
# Usage Statistics
GET /api/v1/analytics/usage
GET /api/v1/analytics/connections
GET /api/v1/analytics/bandwidth

# Server Metrics
GET /api/v1/analytics/servers/status
GET /api/v1/analytics/servers/load
```

## 🔒 API Security

1. **Authentication**
   - OAuth 2.0/JWT-based authentication
   - Short-lived access tokens (30 minutes)
   - Secure refresh token rotation
   - PKCE flow for mobile apps

2. **Authorization**
   - Role-based access control (RBAC)
   - Resource-level permissions
   - Subscription-based feature access

3. **Security Measures**
   - HTTPS-only endpoints
   - Strict CORS policy
   - Rate limiting
   - Input validation & sanitization
   - SQL injection prevention
   - XSS protection
   - CSRF tokens for state-changing operations

4. **Headers**
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
X-API-Version: 1.0
X-Request-ID: <unique_request_id>
```

## 📝 API Standards

1. **HTTP Methods**
   - GET: Read resources
   - POST: Create resources
   - PUT: Update resources (full)
   - PATCH: Update resources (partial)
   - DELETE: Remove resources

2. **Status Codes**
   - 200: Success
   - 201: Created
   - 400: Bad Request
   - 401: Unauthorized
   - 403: Forbidden
   - 404: Not Found
   - 429: Too Many Requests
   - 500: Server Error

3. **Error Response Format**
```json
{
    "error": {
        "code": "INVALID_INPUT",
        "message": "The provided input is invalid",
        "details": [
            {
                "field": "email",
                "message": "Must be a valid email address"
            }
        ],
        "request_id": "req_abc123"
    }
}
```

4. **Pagination**
```json
{
    "data": [...],
    "meta": {
        "total": 100,
        "page": 1,
        "per_page": 20,
        "total_pages": 5
    },
    "links": {
        "self": "/api/v1/resource?page=1",
        "next": "/api/v1/resource?page=2",
        "prev": null
    }
}
```

## 💾 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Subscriptions Table
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    plan_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### VPN Servers Table
```sql
CREATE TABLE vpn_servers (
    id UUID PRIMARY KEY,
    hostname VARCHAR(255) NOT NULL,
    ip_address INET NOT NULL,
    location VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_load FLOAT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 Getting Started

1. Clone the repository:
```bash
git clone https://github.com/ahmadjamalnasir/VPN-backend.git
cd VPN-backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configurations
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📝 Environment Variables

```env
# Application
APP_NAME=Prime VPN
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/primevpn

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
```

## 🔄 Process Flow

1. **User Registration & Authentication**
   - User registers with email and password
   - System validates email and hashes password
   - JWT tokens issued upon successful login

2. **Subscription Management**
   - User browses available subscription plans
   - Selects plan and proceeds to payment
   - System creates payment intent with Stripe
   - Upon successful payment, subscription activated

3. **VPN Connection**
   - User requests VPN connection
   - System selects optimal server based on load and location
   - Connection details returned to client
   - Real-time monitoring of connection status

4. **Server Management**
   - Continuous monitoring of server health
   - Automatic load balancing
   - Server metrics collection and analysis
   - Automatic failover in case of server issues

## 🧪 Testing

```bash
# Run unit tests
pytest

# Run with coverage report
pytest --cov=app tests/
```

## 🔒 Security Features

- Password hashing with bcrypt
- JWT-based authentication
- Rate limiting on sensitive endpoints
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- CORS protection
- HTTP Security Headers

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.