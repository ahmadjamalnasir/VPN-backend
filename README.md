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

## 🚦 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/refresh` - Refresh access token

### User Management
- `GET /users/me` - Get current user info
- `PUT /users/me` - Update user info
- `GET /users/{user_id}` - Get user by ID (admin only)

### VPN Servers
- `GET /vpn/servers` - List all VPN servers
- `GET /vpn/servers/{server_id}` - Get server details
- `POST /vpn/connect` - Connect to VPN server
- `POST /vpn/disconnect` - Disconnect from VPN

### Subscriptions
- `GET /subscriptions/plans` - List all subscription plans
- `POST /subscriptions/subscribe` - Subscribe to a plan
- `GET /subscriptions/status` - Get subscription status

### Payments
- `POST /payments/create` - Create payment intent
- `POST /payments/webhook` - Handle payment webhooks

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