# Prime VPN Backend

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

### Database
- PostgreSQL 14
- SQLAlchemy ORM
- Alembic for Database Migrations

### Authentication & Security
- JWT (JSON Web Tokens)
- WebSocket Authentication
- Rate Limiting
- Secure VPN Key Management

### Caching & Performance
- Redis for Session Management
- Connection Pooling
- Real-time Metrics Aggregation

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