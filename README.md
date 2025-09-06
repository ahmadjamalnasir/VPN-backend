# Prime VPN Backend

A robust and secure backend service for managing VPN connections, user subscriptions, and real-time metrics with Stripe integration.

## 🚀 Features

- 🔐 Secure User Authentication & Authorization
- 🌐 VPN Server Management & Load Balancing
- 💳 Subscription Plans & Stripe Integration
- 📊 Real-time Connection Metrics via WebSocket
- 🔄 Smart Server Selection Algorithm
- 🔒 WireGuard VPN Integration
- 📈 Connection Analytics & Usage Tracking
- 💰 Premium & Free Tier Support
- 🔄 Automatic Subscription Management
- 📱 Cross-Platform Supportackend

A robust and secure backend service for managing VPN connections, user subscriptions, and real-time metrics.

## 🚀 Features

- 🔐 Secure User Authentication & Authorization
- 🌐 VPN Server Management & Load Balancing
- 💳 Subscription Plans & Billing
- 📊 Real-time Connection Metrics via WebSocket
- 🔄 Smart Server Selection Algorithm
- �️ WireGuard VPN Integration
- � Connection Analytics & Usage Tracking

## 🛠️ Tech Stack

### Backend Framework
- FastAPI (Python 3.9+)
- Uvicorn ASGI Server
- WebSocket Support for Real-time Metrics
- WireGuard VPN Protocol
- Stripe Integration for Payments

### Database
- PostgreSQL 14
- SQLAlchemy ORM with Async Support
- Alembic for Database Migrations
- Connection Tracking & Analytics

### Authentication & Security
- JWT (JSON Web Tokens)
- WebSocket Authentication
- Rate Limiting
- Secure VPN Key Management
- Payment Data Encryption

### Caching & Performance
- Redis for Session Management
- Connection Pooling
- Real-time Metrics Aggregation
- Server Load Balancing

### Testing
- Pytest with Async Support
- In-memory SQLite for Testing
- 100% Test Coverage Target
- End-to-End Integration Tests

## 📁 Project Structure

```
VPN-backend/
├── alembic/                    # Database migrations
│   ├── versions/              # Migration versions
│   └── env.py                # Migration environment
├── app/
│   ├── api/                  # API implementation
│   │   └── v1/              # API version 1
│   │       └── routes/      # Route handlers
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py         # User model
│   │   ├── subscription.py # Subscription model
│   │   ├── vpn_server.py  # VPN server model
│   │   └── vpn_connection.py # Connection model
│   ├── schemas/             # Pydantic schemas
│   ├── services/           # Business logic
│   │   ├── auth_service.py     # Authentication
│   │   ├── metrics_service.py  # Real-time metrics
│   │   └── wireguard_service.py # VPN management
│   ├── main.py             # Application entry
│   └── database.py         # Database setup
└── requirements.txt         # Dependencies
```

## 🚦 API Documentation

### User Management
```http
# User Profile
GET /users/me
Response:
{
  "id": "<uuid>",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "subscription": {
    "plan_type": "monthly|yearly|free",
    "status": "active|past_due|canceled",
    "start_date": "2025-08-31T12:00:00Z",
    "end_date": "2026-08-31T12:00:00Z"
  }
}
```

### Subscription Management
```http
# Subscription Status
GET /subscriptions/status
Response:
{
  "plan_type": "monthly|yearly|free",
  "status": "active|past_due|canceled",
  "start_date": "2025-08-31T12:00:00Z",
  "end_date": "2026-08-31T12:00:00Z"
}
```

### VPN Connection Management
```http
# Connect to VPN Server
POST /vpn/connect
Request:
{
  "server_id": "<uuid>",
  "client_public_key": "<wireguard_public_key>"
}
Response:
{
  "status": "active",
  "server_endpoint": "vpn1.example.com:51820",
  "server_public_key": "<server_public_key>",
  "assigned_ip": "10.0.0.2",
  "dns": ["1.1.1.1", "1.0.0.1"]
}

# Disconnect from VPN
POST /vpn/disconnect
Request:
{
  "bytes_sent": 1024,
  "bytes_received": 2048
}
Response:
{
  "status": "ended",
  "total_bytes": 3072,
  "duration": 3600,
  "summary": {
    "avg_speed": "1.2 MB/s",
    "peak_speed": "2.5 MB/s"
  }
}

# Real-time Metrics WebSocket
WS /ws/connection/{user_id}
Messages:
{
  "type": "metrics",
  "data": {
    "bytes_sent": 1024,
    "bytes_received": 2048,
    "current_speed": "1.2 MB/s",
    "latency": 50
  }
}
```

### Payment & Subscription
```http
# Create Payment Session
POST /payments/create
Request:
{
  "plan_type": "monthly",
  "currency": "usd",
  "success_url": "https://example.com/success",
  "cancel_url": "https://example.com/cancel"
}
Response:
{
  "checkout_url": "https://checkout.stripe.com/...",
  "client_secret": "<stripe_client_secret>",
  "payment_intent_id": "<stripe_payment_intent_id>"
}

# Stripe Webhook
POST /payments/webhook
Header: stripe-signature: <signature>
Response: 200 OK
```

## 🧪 Testing

### Setup
```bash
# Install test dependencies
pip install -r tests/requirements-test.txt

# Run tests with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/api/test_auth.py -v

# Run rate limiting tests
pytest tests/test_rate_limiting.py -v

# Run security tests
pytest tests/test_security_fixes.py -v

# Run tests with live output
pytest -s tests/
```

### Test Coverage Areas
- Authentication flows (register, login, refresh, logout)
- Rate limiting and DDoS protection
- VPN connection management
- Subscription handling
- Payment processing
- WebSocket metrics
- Database operations
- Admin security endpoints

### Load Testing Rate Limits
```bash
# Install load testing tool
pip install locust

# Create simple load test
echo 'from locust import HttpUser, task
class RateLimitTest(HttpUser):
    @task
    def test_endpoint(self):
        self.client.get("/health")' > locustfile.py

# Run load test
locust --host=http://localhost:8000 --users=50 --spawn-rate=10
```

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL 14
- Redis (required for rate limiting)
- WireGuard
- Stripe Account

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/VPN-backend.git
cd VPN-backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (latest secure versions)
pip install -r requirements.txt

# Install test dependencies
pip install -r tests/requirements-test.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Setup and test rate limiting
python scripts/setup_rate_limiting.py

# Run security tests
pytest tests/test_security_fixes.py -v

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Rate Limiting Setup Verification
```bash
# Test rate limiting is working
curl -I http://localhost:8000/health
# Should return X-RateLimit-* headers

# Check rate limiting stats (requires admin auth)
curl http://localhost:8000/api/v1/admin/rate-limits/stats

# Test rate limit exceeded
for i in {1..10}; do curl http://localhost:8000/api/v1/auth/login; done
# Should return 429 after configured limit
```

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_MONTHLY_PRICE_ID=price_...
STRIPE_YEARLY_PRICE_ID=price_...

# VPN
WIREGUARD_INTERFACE=wg0
VPN_SUBNET=10.0.0.0/24
```

## 📚 Documentation

- API Documentation: http://localhost:8000/docs
- ReDoc Interface: http://localhost:8000/redoc
- Changelog: [CHANGELOG.md](CHANGELOG.md)

## 🧪 Development

### Creating Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html tests/

# Run specific test file
pytest tests/api/test_auth.py -v
```

### Code Quality
```bash
# Run linter
flake8

# Run type checker
mypy app/

# Format code
black app/
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
# Establish VPN Connection
POST /vpn/connect
Query Parameters:
  - location (optional): Preferred server location

Response:
{
  "connection_id": "<uuid>",
  "server": {
    "id": "<uuid>",
    "hostname": "vpn-server-1",
    "ip_address": "1.2.3.4",
    "location": "us-west",
    "endpoint": "1.2.3.4:51820"
  },
  "wg_config": "[Interface]\nPrivateKey=...\nAddress=10.0.0.2/32\n...",
  "started_at": "2025-08-31T12:00:00Z",
  "expires_at": null
}

# Disconnect VPN
POST /vpn/disconnect/{connection_id}
Response:
{
  "connection_id": "<uuid>",
  "started_at": "2025-08-31T12:00:00Z",
  "ended_at": "2025-08-31T13:00:00Z",
  "duration_seconds": 3600,
  "bytes_sent": 1000000,
  "bytes_received": 2000000,
  "total_bytes": 3000000
}
```

### Real-time Metrics
```http
# WebSocket Connection
WS /ws/connection/{user_id}?token={jwt_token}

# Metrics Stream (JSON messages)
{
  "timestamp": "2025-08-31T12:00:00Z",
  "connection_id": "<uuid>",
  "bytes_sent": 1000000,
  "bytes_received": 2000000,
  "upload_speed_mbps": 5.67,
  "download_speed_mbps": 12.34,
  "ping_ms": 45,
  "server_load_pct": 35.5
}
```

## 💾 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
```

### Subscriptions Table
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan_type VARCHAR(10) CHECK (plan_type IN ('monthly', 'yearly', 'free')),
    status VARCHAR(10) CHECK (status IN ('active', 'past_due', 'canceled')),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
```

### VPN Servers Table
```sql
CREATE TABLE vpn_servers (
    id UUID PRIMARY KEY,
    hostname VARCHAR NOT NULL,
    location VARCHAR NOT NULL,
    ip_address VARCHAR NOT NULL,
    endpoint VARCHAR NOT NULL,
    public_key VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'active',
    current_load FLOAT DEFAULT 0.0,
    ping INTEGER DEFAULT 0,
    available_ips VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    CONSTRAINT valid_server_status CHECK (status IN ('active', 'maintenance', 'offline'))
);
```

### VPN Connections Table
```sql
CREATE TABLE connections (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    server_id UUID REFERENCES vpn_servers(id) ON DELETE SET NULL,
    client_ip VARCHAR NOT NULL,
    client_public_key VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'connected',
    bytes_sent BIGINT DEFAULT 0,
    bytes_received BIGINT DEFAULT 0,
    started_at TIMESTAMP DEFAULT now(),
    ended_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    CONSTRAINT valid_connection_status CHECK (status IN ('connected', 'disconnected'))
);
```

## 🚫 Rate Limiting & DDoS Protection

### Overview
Prime VPN implements a comprehensive multi-layer security system to protect against abuse, DDoS attacks, and ensure fair resource usage.

### Architecture
```
Client Request → DDoS Protection → Rate Limiting → Authentication → API Endpoint
```

### DDoS Protection Layer
- **Traffic Analysis**: Real-time monitoring of request patterns
- **IP Reputation**: Automatic blacklisting of malicious IPs
- **Threshold Detection**: 500+ requests/minute triggers protection
- **Geographic Filtering**: Optional country-based restrictions
- **Whitelist Support**: Bypass protection for trusted IPs/networks

### Rate Limiting Layer
- **Sliding Window**: Precise request counting with Redis
- **Burst Support**: Allow temporary spikes within limits
- **Endpoint-Specific**: Different limits for different API endpoints
- **User-Based**: Per-user limits for authenticated requests
- **Adaptive**: Dynamic adjustment based on system load

### Admin Management
```http
# View rate limiting statistics
GET /api/v1/admin/rate-limits/stats

# Check specific IP status
GET /api/v1/admin/rate-limits/status/{ip}?endpoint=auth_login

# Ban/unban IP addresses
POST /api/v1/admin/bans
DELETE /api/v1/admin/bans/{ip}

# Reset rate limits
DELETE /api/v1/admin/rate-limits/reset/{ip}?endpoint=auth_login
```

### Monitoring & Alerts
- **Real-time Metrics**: Track violations and bans
- **Top Offenders**: Identify problematic IPs
- **Endpoint Analysis**: Monitor which endpoints are most targeted
- **Performance Impact**: Measure protection overhead

### Configuration
All settings are configurable via environment variables:
```env
# Enable/disable protection
RATE_LIMIT_ENABLED=true
DDOS_PROTECTION_ENABLED=true

# Global limits
GLOBAL_RATE_LIMIT=1000  # requests/minute
IP_RATE_LIMIT=100       # requests/minute per IP

# DDoS thresholds
DDOS_THRESHOLD=500      # requests/minute to trigger ban
DDOS_BAN_DURATION=3600  # ban duration in seconds

# Suspicious activity
SUSPICIOUS_ACTIVITY_THRESHOLD=50  # failed attempts
SUSPICIOUS_ACTIVITY_WINDOW=300    # time window (seconds)
SUSPICIOUS_ACTIVITY_BAN=1800      # ban duration (seconds)
```

## 🔄 Server Selection Algorithm

The VPN server selection process uses the following criteria:
1. Filter servers by status == "active"
2. If location is specified, filter by matching location
3. Sort by:
   - current_load (ascending)
   - ping (ascending)
4. Select the first available server

## 📊 Real-time Metrics System

The WebSocket-based metrics system provides:
- Real-time connection statistics
- Network speed calculations
- Server load monitoring
- Latency measurements
- Bandwidth usage tracking

Authentication is required via JWT token and metrics are pushed every second.

## 🛡️ Security Features

- JWT-based authentication for REST APIs
- Token-based WebSocket authentication
- WireGuard key pair generation and management
- Secure configuration distribution
- Rate limiting on sensitive endpoints
- Automatic connection cleanup
- Server load balancing

## 📦 Setup & Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up PostgreSQL database
4. Run migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## 🧪 Running Tests

```bash
pytest
```

## 📄 License

MIT License
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
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/primevpn

# Redis
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting & DDoS Protection
RATE_LIMIT_ENABLED=true
DDOS_PROTECTION_ENABLED=true
GLOBAL_RATE_LIMIT=1000
IP_RATE_LIMIT=100
DDOS_THRESHOLD=500
DDOS_BAN_DURATION=3600
DDOS_WHITELIST_IPS=["127.0.0.1","::1"]
SUSPICIOUS_ACTIVITY_THRESHOLD=50
SUSPICIOUS_ACTIVITY_WINDOW=300
SUSPICIOUS_ACTIVITY_BAN=1800

# Stripe
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
```

## 🔄 Process Flow

1. **Request Processing & Security**
   - **DDoS Protection**: First layer checks for malicious traffic patterns
   - **Rate Limiting**: Second layer applies endpoint-specific limits
   - **Authentication**: JWT token validation for protected endpoints
   - **Authorization**: Role-based access control

2. **User Registration & Authentication**
   - User registers with email and password (rate limited: 3/hour)
   - System validates email and hashes password
   - Login attempts rate limited (5/5min) with suspicious activity detection
   - JWT tokens issued upon successful login

3. **Subscription Management**
   - User browses available subscription plans
   - Selects plan and proceeds to payment (rate limited: 10/5min)
   - System creates payment intent with Stripe
   - Upon successful payment, subscription activated

4. **VPN Connection**
   - User requests VPN connection (rate limited: 20/min)
   - System selects optimal server based on load and location
   - Connection details returned to client
   - Real-time monitoring of connection status

5. **Server Management**
   - Continuous monitoring of server health
   - Automatic load balancing
   - Server metrics collection and analysis
   - Automatic failover in case of server issues

6. **Security Monitoring**
   - Real-time tracking of rate limit violations
   - Automatic IP banning for DDoS attempts
   - Admin dashboard for security metrics
   - Suspicious activity alerts and logging

## 🧪 Testing

```bash
# Run unit tests
pytest

# Run with coverage report
pytest --cov=app tests/
```

## 🔒 Security Features

### Authentication & Authorization
- Password hashing with bcrypt
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Session management with Redis

### Rate Limiting & DDoS Protection
- **Multi-layer Rate Limiting**: Endpoint-specific limits with burst support
- **DDoS Protection**: Automatic IP banning for suspicious traffic patterns
- **Adaptive Throttling**: Dynamic rate adjustment based on system load
- **IP Whitelisting**: Bypass protection for trusted IPs
- **Suspicious Activity Detection**: Automatic banning for repeated failed attempts

#### Rate Limiting Configuration
```yaml
Endpoint Limits (requests/window):
- Authentication Login: 5 req/5min (burst: 2)
- Registration: 3 req/hour (burst: 1)
- Password Reset: 3 req/hour (burst: 1)
- VPN Connect: 20 req/min (burst: 5)
- VPN Disconnect: 30 req/min (burst: 10)
- Payments: 10 req/5min (burst: 3)
- WebSocket: 5 connections/min (burst: 2)
- General API: 60 req/min (burst: 20)
```

#### DDoS Protection Thresholds
- **Detection Threshold**: 500 requests/minute
- **Auto-ban Duration**: 1 hour
- **Suspicious Activity**: 50 failed attempts in 5 minutes → 30 min ban
- **Global IP Limit**: 100 requests/minute

### Additional Security
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- CORS protection with configurable origins
- HTTP Security Headers
- Request/Response logging for audit trails

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.