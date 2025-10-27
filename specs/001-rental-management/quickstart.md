# Meroghar Quick Start Guide

# Getting Started with Development

**Date**: 2025-10-26  
**Feature**: 001-rental-management  
**Audience**: Developers setting up local development environment

---

## Prerequisites

### System Requirements

- **OS**: macOS 10.15+, Ubuntu 20.04+, or Windows 10+ with WSL2
- **RAM**: Minimum 8GB (16GB recommended)
- **Disk**: 10GB free space
- **Docker**: 20.10+ with Docker Compose
- **Git**: 2.30+

### Development Tools

- **Python**: 3.11+ with pip and virtualenv
- **Node.js**: 18+ with npm (for tooling)
- **Flutter**: 3.10+ with Android SDK and/or Xcode
- **PostgreSQL Client**: psql 14+
- **Code Editor**: VS Code (recommended) or equivalent

---

## Backend Setup

### 1. Clone Repository

```bash
git clone https://github.com/meroghar/meroghar.git
cd meroghar
git checkout 001-rental-management
```

### 2. Set Up Python Environment

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

### 3. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
vim .env
```

**Required Environment Variables**:

```bash
# Database
DATABASE_URL=postgresql://meroghar_user:password@localhost:5432/meroghar_db

# JWT Authentication
SECRET_KEY=your-secret-key-min-32-chars-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS S3 (Document Storage)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=meroghar-documents-dev

# Redis (Celery)
REDIS_URL=redis://localhost:6379/0

# Payment Gateways (use test keys)
STRIPE_API_KEY=sk_test_...
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
PAYPAL_CLIENT_ID=...
PAYPAL_SECRET=...

# SMS/WhatsApp Gateway
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890

# Firebase Cloud Messaging
FCM_SERVER_KEY=...

# Application
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 4. Start Infrastructure Services

```bash
# Start PostgreSQL, Redis, and pgAdmin using Docker Compose
docker-compose up -d postgres redis pgadmin

# Verify services are running
docker-compose ps

# Access pgAdmin (optional - for database management)
# URL: http://localhost:5050
# Email: admin@meroghar.com
# Password: meroghar_admin_password
```

**pgAdmin Setup (Optional):**
If you want to manage the database via web UI:

1. Open http://localhost:5050
2. Login with credentials above
3. Click "Add New Server"
4. General tab: Name = "MeroGhar Dev"
5. Connection tab:
   - Host: `postgres`
   - Port: `5432`
   - Username: `meroghar`
   - Password: `meroghar_dev_password`
6. Click "Save"

### 5. Run Database Migrations

```bash
# Initialize Alembic (first time only)
alembic upgrade head

# Create initial admin user (optional)
python scripts/create_admin_user.py
```

### 6. Start Backend Server

```bash
# Development server with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Server should start at: http://localhost:8000
# API docs available at: http://localhost:8000/docs
```

### 7. Start Background Workers

```bash
# In separate terminal (activate venv first)
celery -A src.tasks.celery_app worker --loglevel=info

# Start Celery Beat for scheduled tasks (separate terminal)
celery -A src.tasks.celery_app beat --loglevel=info
```

---

## Frontend (Mobile) Setup

### 1. Navigate to Mobile Directory

```bash
cd mobile
```

### 2. Install Flutter Dependencies

```bash
# Get Flutter packages
flutter pub get

# Verify Flutter installation
flutter doctor
```

### 3. Configure Environment

```bash
# Copy example config
cp lib/config/env.example.dart lib/config/env.dart

# Edit with your backend URL
vim lib/config/env.dart
```

**Example Configuration**:

```dart
class Environment {
  static const String apiBaseUrl = 'http://localhost:8000/api/v1';
  static const bool isProduction = false;
  static const String appName = 'Meroghar Dev';
}
```

### 4. Generate Code (if needed)

```bash
# Generate JSON serialization code
flutter pub run build_runner build --delete-conflicting-outputs

# Generate localization files
flutter gen-l10n
```

### 5. Run Mobile App

#### Android

```bash
# List available devices
flutter devices

# Run on Android emulator/device
flutter run -d <device-id>

# Or simply (picks first available device)
flutter run
```

#### iOS (macOS only)

```bash
# Navigate to iOS directory
cd ios

# Install CocoaPods dependencies
pod install

# Return to mobile root
cd ..

# Run on iOS simulator/device
flutter run -d <ios-device-id>
```

### 6. Hot Reload

Press `r` in terminal to hot reload, `R` to hot restart, or `q` to quit.

---

## Running Tests

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_bill_division.py

# Run integration tests (requires Docker)
pytest tests/integration/ -v

# Run contract tests
pytest tests/contract/ -v
```

### Frontend Tests

```bash
cd mobile

# Run all tests
flutter test

# Run specific test file
flutter test test/unit/models_test.dart

# Run integration tests
flutter test integration_test/

# Run with coverage
flutter test --coverage
flutter pub run test_cov_console
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/add-rent-increment
```

### 2. Make Changes Following TDD

```bash
# 1. Write failing test
vim tests/unit/test_rent_increment.py

# 2. Run tests (should fail)
pytest tests/unit/test_rent_increment.py

# 3. Implement feature
vim src/services/rent_service.py

# 4. Run tests (should pass)
pytest tests/unit/test_rent_increment.py

# 5. Refactor and repeat
```

### 3. Commit Changes

```bash
git add .
git commit -m "feat(rent): implement automatic rent increment calculation"
```

### 4. Push and Create Pull Request

```bash
git push origin feature/add-rent-increment
# Then create PR on GitHub/GitLab
```

---

## Common Tasks

### Create Database Migration

```bash
cd backend
source venv/bin/activate

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add rent_increment_rate to tenants"

# Edit generated migration file if needed
vim migrations/versions/<timestamp>_add_rent_increment_rate_to_tenants.py

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Access Database

```bash
# Connect to PostgreSQL
psql -h localhost -U meroghar_user -d meroghar_db

# List tables
\dt

# Query data
SELECT * FROM users LIMIT 10;

# Exit
\q
```

### View Logs

```bash
# Backend logs
tail -f logs/app.log

# Celery logs
tail -f logs/celery.log

# Docker logs
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Clear Redis Cache

```bash
redis-cli
> FLUSHALL
> EXIT
```

### Rebuild Docker Containers

```bash
docker-compose down
docker-compose up -d --build
```

---

## Troubleshooting

### Issue: Database Connection Refused

**Solution**:

```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### Issue: Module Not Found (Python)

**Solution**:

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check if in correct directory
pwd  # Should be in backend/
```

### Issue: Flutter Build Fails

**Solution**:

```bash
# Clean build artifacts
flutter clean

# Get dependencies
flutter pub get

# Rebuild
flutter run
```

### Issue: Tests Failing with Database Errors

**Solution**:

```bash
# Ensure test database is clean
pytest --create-db

# Or manually drop test database
dropdb meroghar_test_db
createdb meroghar_test_db
```

### Issue: Port Already in Use

**Solution**:

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn src.main:app --port 8001
```

---

## Additional Resources

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Monitoring Tools

- **pgAdmin**: http://localhost:5050 (Database management - included in Docker Compose)
  - Email: admin@meroghar.com
  - Password: meroghar_admin_password
- **Flower (Celery)**: http://localhost:5555
- **Database GUI Alternatives**: TablePlus, DBeaver

### Documentation

- **Architecture**: `/docs/architecture/`
- **API Contracts**: `/specs/001-rental-management/contracts/`
- **Data Model**: `/specs/001-rental-management/data-model.md`

### Support

- **GitHub Issues**: https://github.com/meroghar/meroghar/issues
- **Slack**: #meroghar-dev channel
- **Email**: dev@meroghar.com

---

## Next Steps

After successful setup:

1. **Explore API**: Use Swagger UI to test endpoints
2. **Read Codebase**: Start with `/backend/src/main.py` and `/mobile/lib/main.dart`
3. **Run Example Tests**: Familiarize yourself with test structure
4. **Pick First Task**: Check `/speckit.tasks` output or GitHub issues labeled `good-first-issue`
5. **Join Team Chat**: Introduce yourself on Slack

**Happy Coding! 🚀**
