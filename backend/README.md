# MeroGhar Backend

FastAPI-based backend for the MeroGhar rental management system.

## Quick Start

### With Docker (Recommended)

```bash
# Start all services (PostgreSQL, Redis, pgAdmin, Backend, Celery)
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# View logs
docker-compose logs -f backend

# Access services:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - pgAdmin: http://localhost:5050
```

**pgAdmin Login:**

- URL: http://localhost:5050
- Email: admin@meroghar.com
- Password: meroghar_admin_password

**pgAdmin Database Connection:**

- Host: `postgres`
- Port: 5432
- Username: meroghar
- Password: meroghar_dev_password
- Database: meroghar_dev

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Start PostgreSQL and Redis with Docker
docker-compose up -d postgres redis pgadmin

# Run migrations
alembic upgrade head

# Start development server
uvicorn src.main:app --reload
```

## Project Structure

```
backend/
├── alembic/              # Database migrations
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── src/
│   ├── api/             # API endpoints
│   │   └── v1/          # Version 1 endpoints
│   ├── core/            # Core functionality (config, database, security)
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── tasks/           # Celery tasks
└── tests/               # Tests
```

## Environment Configuration

Copy `.env.example` to `.env` and configure:

**Required:**

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Secret key for encryption
- `JWT_SECRET_KEY`: JWT token signing key
- `REDIS_URL`: Redis connection string

**Optional:**

- `PGADMIN_DEFAULT_EMAIL`: pgAdmin login email
- `PGADMIN_DEFAULT_PASSWORD`: pgAdmin login password
- Payment gateway credentials (Stripe, Razorpay)
- AWS S3 credentials (for document storage)
- Twilio credentials (for SMS)
- FCM credentials (for push notifications)
- Sentry DSN (for error monitoring)

## Development

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Database Management with pgAdmin

1. Start services: `docker-compose up -d`
2. Open http://localhost:5050
3. Login with credentials from `.env`
4. Add server (one-time setup):
   - Name: MeroGhar Dev
   - Host: `postgres` (container name)
   - Port: 5432
   - Username: meroghar
   - Password: meroghar_dev_password

### Background Tasks

```bash
# Start Celery worker
celery -A src.tasks.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A src.tasks.celery_app beat --loglevel=info
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_auth_service.py
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Services

- **Backend API**: http://localhost:8000
- **pgAdmin**: http://localhost:5050
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Documentation

- **Docker Deployment**: [docs/docker-deployment-guide.md](docs/docker-deployment-guide.md)
- **Quickstart Guide**: [../specs/001-rental-management/quickstart.md](../specs/001-rental-management/quickstart.md)
- **API Documentation**: [docs/api.md](docs/api.md)
- **Caching Guide**: [docs/caching-guide.md](docs/caching-guide.md)
- **Security Audit**: [docs/security-audit.md](docs/security-audit.md)

## License

Proprietary - MeroGhar Development Team
