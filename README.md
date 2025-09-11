# Prime VPN Backend

A robust and secure backend service for managing VPN connections, user subscriptions, and real-time metrics with premium access control.

## 🚀 Features

- 🔐 User Authentication with Email Verification & Password Reset
- 👤 User Management with Readable IDs & Profile Updates
- 💳 Independent Subscription Plans with Premium Access Control
- 🌐 VPN Server Management with Premium/Free Tier Separation
- 📊 Connection History & Session Stats (Premium Only)
- 🔄 Smart Server Selection with Load Balancing
- 🔒 WireGuard VPN Integration
- 📈 Real-time Connection Analytics & Usage Tracking
- 💰 Auto-renewal & Payment Method Tracking

## 🛠️ Tech Stack

- **FastAPI** (Python 3.9+) with async/await
- **PostgreSQL** with SQLAlchemy ORM
- **JWT Authentication** with OTP verification
- **Redis** for session management
- **Stripe Integration** for payments
- **WireGuard** VPN protocol

## 📁 Project Structure

```
VPN-backend/
├── app/
│   ├── api/v1/
│   │   ├── auth.py              # Authentication & OTP
│   │   ├── users.py             # User management & connections
│   │   ├── subscriptions.py     # Subscription management
│   │   └── vpn.py              # VPN servers & connections
│   ├── models/
│   │   ├── user.py             # User with readable ID & premium status
│   │   ├── subscription_plan.py # Independent subscription plans
│   │   ├── user_subscription.py # User-plan assignments
│   │   ├── vpn_server.py       # VPN servers with premium flag
│   │   ├── connection.py       # Connection tracking with duration
│   │   └── otp_verification.py # Email verification & password reset
│   ├── schemas/                # Pydantic request/response models
│   ├── services/               # Business logic & OTP service
│   └── main.py                # Application entry point
└── requirements.txt
```

## 🔌 API Endpoints

### Authentication (`/api/v1/auth`)
```http
POST /signup              # Register with name, email, password, phone, country
POST /verify-email        # Verify email with OTP code
POST /login              # Login with email validation
POST /forgot-password    # Send password reset OTP
POST /reset-password     # Reset password with OTP verification
```

### Users (`/api/v1/users`)
```http
GET  /profile?email=user@example.com        # Get user profile
GET  /by-id/{user_id}                       # Get user by readable ID
GET  /connections?email=user@example.com    # Connection history (Premium only)
PUT  /update?email=user@example.com         # Update name, phone, password
PUT  /status/{user_id}                      # Update active/premium status
```

### Subscriptions (`/api/v1/subscriptions`)
```http
GET  /plans                                 # List all subscription plans
GET  /user?email=user@example.com           # Get user's active subscription
POST /assign                               # Assign plan to user
PUT  /cancel?email=user@example.com         # Cancel subscription
```

### VPN (`/api/v1/vpn`)
```http
GET  /servers?is_premium=true&location=us-east  # Get servers with filters
POST /connect?user_email=user@example.com       # Connect with premium validation
POST /disconnect                               # Disconnect with session stats
```

## 🗄️ Database Schema

### Users Table
- `user_id` (readable integer ID)
- `name`, `email`, `phone`, `country`
- `is_premium`, `is_email_verified`
- `hashed_password`

### Subscription Plans (Independent)
- `plan_id`, `name`, `plan_type`, `price`
- `duration_days`, `is_premium`
- `features` (JSON)

### User Subscriptions (Links users to plans)
- `user_id` → `users.id`
- `plan_id` → `subscription_plans.id`
- `status`, `start_date`, `end_date`
- `auto_renew`, `payment_method`

### VPN Servers
- `hostname`, `location`, `ip_address`
- `is_premium` (premium server access)
- `current_load`, `ping`, `status`

### Connections (Session tracking)
- `user_id`, `server_id`, `client_ip`
- `bytes_sent`, `bytes_received`
- `duration_seconds`, `started_at`, `ended_at`

## 🔒 Premium Access Control

### Free Users
- Access only `is_premium=false` servers
- Cannot view connection history
- Basic server locations

### Premium Users  
- Access all servers (premium + free)
- Full connection history with stats
- All server locations
- Priority server selection

## 🧪 API Examples

### User Signup & Verification
```bash
# 1. Signup
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"secure123","phone":"+1234567890","country":"US"}'

# 2. Verify email (OTP sent to email)
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","otp_code":"123456"}'

# 3. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"secure123"}'
```

### VPN Connection Flow
```bash
# 1. Get available servers
curl "http://localhost:8000/api/v1/vpn/servers?is_premium=false"

# 2. Connect to VPN
curl -X POST "http://localhost:8000/api/v1/vpn/connect?user_email=john@example.com" \
  -H "Content-Type: application/json" \
  -d '{"client_public_key":"wireguard_key","location":"us-east"}'

# 3. Disconnect with stats
curl -X POST "http://localhost:8000/api/v1/vpn/disconnect?connection_id=uuid&user_email=john@example.com&bytes_sent=1048576&bytes_received=2097152"
```

### Connection History (Premium Only)
```bash
curl "http://localhost:8000/api/v1/users/connections?email=premium@example.com&limit=10"
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
git clone https://github.com/yourusername/VPN-backend.git
cd VPN-backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Database
```bash
# Update .env file
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/primevpn
JWT_SECRET=your-secret-key
REDIS_URL=redis://localhost:6379
```

### 3. Initialize Data
```bash
# Insert subscription plans
python insert_subscription_plans.py

# Insert sample VPN servers
python insert_sample_data.py
```

### 4. Start Server
```bash
python start_server.py
# Server runs on http://localhost:8000
# API docs: http://localhost:8000/docs
```

### 5. Test APIs
```bash
python test_updated_apis.py
```

## 📊 Session Stats Response
```json
{
  "connection_id": "uuid",
  "session_stats": {
    "duration_seconds": 3600,
    "duration_formatted": "01:00:00",
    "bytes_sent": 1048576,
    "bytes_received": 2097152,
    "total_bytes": 3145728,
    "total_data_mb": 3.0,
    "avg_speed_mbps": 0.87,
    "server_location": "us-east",
    "client_ip": "10.0.123.45"
  },
  "message": "VPN disconnected successfully. Session stats recorded."
}
```

## 🔧 Environment Variables
```env
# Application
APP_NAME="Prime VPN"
DEBUG=true
JWT_SECRET="your-secret-key"

# Database
DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/primevpn"

# Redis
REDIS_URL="redis://localhost:6379"

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]
```

## 📝 License

MIT License