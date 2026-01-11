# EquiShard (InvestSaaS)

A **Fractional Investment Marketplace** demonstrating advanced patterns: **DDD**, **CQRS**, **Multi-tenancy**, and **ABAC**.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ASGI Router                            │
│  /api/* → FastAPI (Reads)  |  Other → Django (Writes)       │
└─────────────────────────────────────────────────────────────┘
         ↓                              ↓
┌─────────────────────┐      ┌─────────────────────────────────┐
│   Query Layer       │      │        Command Layer            │
│   (FastAPI)         │      │        (Django)                 │
│                     │      │                                 │
│ • Analytics API     │      │ • User Service                  │
│ • Store API         │      │ • Ledger Service (Double-Entry) │
│ • Raw SQL queries   │      │ • Catalog Service (Locking)     │
│                     │      │ • Invest Service (Transaction)  │
└─────────────────────┘      └─────────────────────────────────┘
                    ↘          ↙
              ┌─────────────────────┐
              │   PostgreSQL    │
              └─────────────────────┘
```

## 🚀 Quick Start

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Seed database with test data
docker-compose exec web python scripts/seed.py

# View logs
docker-compose logs -f web
```

#### Environment Variables

You can configure the price fluctuation service using the following environment variables in your `.env` file or docker-compose environment:

| Variable | Default | Description |
|----------|---------|-------------|
| `PRICE_FLUCTUATION_INTERVAL` | `60` | Interval in seconds between price updates |
| `MAX_INCREASE_PERCENTAGE` | `5` | Maximum percentage a price can increase per interval (5 = 5%) |
| `MAX_DECREASE_PERCENTAGE` | `5` | Maximum percentage a price can decrease per interval (5 = 5%) |


### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database settings

# Run migrations
python manage.py migrate

# Seed database
python scripts/seed.py

# Start server
python manage.py runserver
```

## 📚 API Documentation

- **Django Admin**: http://localhost:8000/admin/
- **FastAPI Docs**: http://localhost:8000/api/docs
- **FastAPI ReDoc**: http://localhost:8000/api/redoc

## 🔐 Authentication

```bash
# Get JWT tokens
curl -X POST http://localhost:8000/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "investor1_alpha", "password": "password123"}'

# Use token for authenticated requests
curl http://localhost:8000/api/v1/analytics/summary \
  -H "Authorization: Bearer <access_token>"
```

## 📊 Key Endpoints

### Command Layer (Django)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/token/` | POST | Get JWT tokens |
| `/commands/users/register/` | POST | Register user |
| `/commands/ledger/faucet/` | POST | Add test funds |
| `/commands/catalog/invest/` | POST | Make investment |

### Query Layer (FastAPI)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/store/assets` | GET | Browse assets |
| `/api/v1/store/assets/{id}` | GET | Asset details |
| `/api/v1/analytics/portfolio-growth` | GET | Portfolio chart data |
| `/api/v1/analytics/allocation` | GET | Allocation pie chart |
| `/api/v1/analytics/summary` | GET | Portfolio summary |

## 🧪 Test Credentials

| Username | Password | Role |
|----------|----------|------|
| `admin` | `password123` | **Superuser** / Admin Panel |
| `investor1_alpha` | `password123` | Regular Investor (Alpha) |
| `vip_investor_alpha` | `password123` | VIP Investor (Alpha) |

## 📁 Project Structure

```
equishard/
├── manage.py
├── equishard/          # Django config
│   ├── settings.py
│   ├── asgi.py         # CQRS router
│   ├── urls.py
│   ├── views.py
│   └── wsgi.py
├── apps/               # Domain Layer (Commands)
│   ├── users/          # Identity context
│   ├── ledger/         # Double-entry banking
│   └── catalog/        # Assets & inventory
├── api/                # Query Layer (FastAPI)
│   ├── main.py
│   ├── dependencies.py
│   └── v1/
│       ├── analytics.py
│       └── store.py
├── shared/             # Shared Kernel
│   ├── abac/           # Policy engine
│   └── utils/          # Helpers
├── templates/          # Django Templates
│   ├── base.html
│   ├── home.html
│   └── ...
├── scripts/
│   └── seed.py
├── Dockerfile
└── docker-compose.yml
```

## 📝 License

MIT
