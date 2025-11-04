# Meroghar - Complete Application Setup Guide

This guide provides step-by-step instructions to set up and run the complete Meroghar Rental Management System.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Running the Application](#running-the-application)
5. [Architecture Overview](#architecture-overview)
6. [Configuration](#configuration)
7. [Development Workflow](#development-workflow)
8. [Troubleshooting](#troubleshooting)

## System Requirements

### Required Software

- **Docker Desktop** 4.0+ (for backend services)
- **Flutter SDK** 3.10+ (for mobile app)
- **Git** (for version control)

### Operating System

- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 20.04+)

### Hardware

- Minimum 8GB RAM
- 10GB free disk space
- Stable internet connection

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd meroghar
```

### 2. Start Backend Services

```bash
# Start all Docker services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# Run database migrations
docker-compose exec backend alembic upgrade head
```

### 3. Setup Mobile App

```bash
cd mobile

# Install dependencies
flutter pub get

# Create required directories (Windows)
powershell -ExecutionPolicy Bypass -File create_dirs.ps1

# Or manually follow DIRECTORY_SETUP.md instructions
```

### 4. Run Mobile App

```bash
# List available devices
flutter devices

# Run on connected device/emulator
flutter run
```

## Detailed Setup

### Backend Setup

#### 1. Environment Configuration

```bash
cd backend
cp .env.example .env
```

Edit `.env` and configure:

```env
# Database (Docker services use container names)
DATABASE_URL=postgresql://meroghar:meroghar_dev_password@postgres:5432/meroghar

# Redis
REDIS_URL=redis://redis:6379/0

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-minimum-32-characters-long-here
JWT_SECRET_KEY=your-jwt-secret-key-minimum-32-characters-long

# Environment
ENVIRONMENT=development
DEBUG=True
```

#### 2. Start Services

```bash
# From project root
docker-compose up -d

# Verify all services are running
docker-compose ps

# Expected services:
# - meroghar_postgres (database)
# - meroghar_redis (cache)
# - meroghar_backend (API)
# - meroghar_celery_worker (background tasks)
# - meroghar_celery_beat (scheduled tasks)
# - meroghar_pgadmin (database UI)
```

#### 3. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Optional: Create seed data
docker-compose exec backend python scripts/seed_data.py
```

#### 4. Verify Backend

Visit these URLs:

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **PgAdmin**: http://localhost:5050
  - Email: admin@meroghar.com
  - Password: meroghar_admin_password

### Mobile App Setup

#### 1. Install Flutter

Follow official guide: https://flutter.dev/docs/get-started/install

Verify installation:
```bash
flutter doctor
```

#### 2. Configure Project

```bash
cd mobile

# Install dependencies
flutter pub get

# Verify configuration
flutter doctor -v
```

#### 3. Configure API Endpoint

Edit `lib/config/env.dart`:

```dart
// Choose based on your setup:

// Option 1: Android Emulator
static const String apiBaseUrl = 'http://10.0.2.2:8000';

// Option 2: iOS Simulator (Mac only)
static const String apiBaseUrl = 'http://localhost:8000';

// Option 3: Physical Device (use your machine's IP)
static const String apiBaseUrl = 'http://192.168.1.100:8000';
```

To find your machine's IP:

**Windows:**
```cmd
ipconfig
# Look for "IPv4 Address" under your network adapter
```

**Mac/Linux:**
```bash
ifconfig
# Look for "inet" under your network interface
```

#### 4. Create Directory Structure

**Windows (PowerShell):**
```powershell
cd lib
.\create_directories.ps1
```

**Windows (Command Prompt):**
```cmd
cd lib
call create_dirs.bat
```

**Mac/Linux:**
```bash
cd lib
chmod +x create_directories.sh
./create_directories.sh
```

Or manually follow `DIRECTORY_SETUP.md`

#### 5. Setup Firebase (Optional for Push Notifications)

1. Create Firebase project: https://console.firebase.google.com
2. Add Android/iOS apps
3. Download config files:
   - Android: `google-services.json` → `android/app/`
   - iOS: `GoogleService-Info.plist` → `ios/Runner/`
4. Update `lib/config/env.dart` with Firebase credentials

## Running the Application

### Backend

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Mobile App

```bash
cd mobile

# Check available devices
flutter devices

# Run on default device
flutter run

# Run on specific device
flutter run -d <device-id>

# Run in release mode
flutter run --release

# Build APK (Android)
flutter build apk --release

# Build iOS (Mac only)
flutter build ios --release
```

### Development Mode

```bash
# Backend with hot reload
docker-compose up backend

# Mobile with hot reload (default)
flutter run
```

## Architecture Overview

### Technology Stack

**Backend:**
- FastAPI (Python web framework)
- PostgreSQL (Database)
- Redis (Cache & Task Queue)
- Celery (Background tasks)
- SQLAlchemy (ORM)
- Alembic (Migrations)

**Frontend:**
- Flutter 3.10+ (Mobile framework)
- Dart 3.0+ (Programming language)
- Provider (State management)
- Dio (HTTP client)
- SQLite (Local storage)

**Infrastructure:**
- Docker & Docker Compose
- Nginx (Production reverse proxy)

### Project Structure

```
meroghar/
├── backend/                    # FastAPI backend
│   ├── src/
│   │   ├── api/               # API endpoints
│   │   ├── core/              # Configuration & constants
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── tasks/             # Celery tasks
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Backend tests
│   └── requirements.txt       # Python dependencies
│
├── mobile/                     # Flutter mobile app
│   ├── lib/
│   │   ├── config/            # Configuration files
│   │   │   ├── constants.dart # App constants ✅
│   │   │   ├── env.dart       # Environment config ✅
│   │   │   └── app_router.dart # Routing ✅
│   │   ├── models/            # Data models
│   │   ├── providers/         # State management
│   │   ├── screens/           # UI screens
│   │   ├── services/          # API & local services
│   │   ├── utils/             # Utilities
│   │   ├── widgets/           # Reusable widgets
│   │   └── main.dart          # App entry point
│   ├── test/                  # Mobile tests
│   └── pubspec.yaml           # Flutter dependencies
│
└── docker-compose.yml          # Docker services ✅
```

### Data Flow

```
Mobile App ← → Backend API ← → PostgreSQL
    ↓              ↓                ↓
 SQLite        Redis Cache    Background Jobs
(Offline)     (Fast Access)   (Celery Workers)
```

## Configuration

### Backend Configuration

All constants are in `backend/src/core/constants.py`:

```python
# User roles
class UserRole(str, Enum):
    OWNER = "OWNER"
    INTERMEDIARY = "INTERMEDIARY"
    TENANT = "TENANT"

# Payment methods
class PaymentMethod(str, Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    KHALTI = "KHALTI"
    # ... more
```

### Frontend Configuration

All constants are in `mobile/lib/config/constants.dart`:

```dart
// API endpoints
class ApiEndpoints {
  static const String login = '/auth/login';
  static const String properties = '/properties';
  // ... more
}

// App routes
class AppRoutes {
  static const String login = '/login';
  static const String home = '/home';
  // ... more
}
```

### Environment Variables

**Backend** (`.env`):
- Database connection
- Redis URL
- Secret keys
- External API keys
- Email/SMS configuration

**Frontend** (`env.dart`):
- API base URL
- Feature flags
- Firebase configuration
- Payment gateway keys

## Development Workflow

### 1. Start Development Environment

```bash
# Terminal 1: Backend services
docker-compose up -d
docker-compose logs -f backend

# Terminal 2: Mobile app
cd mobile
flutter run
```

### 2. Make Changes

**Backend:**
- Edit files in `backend/src/`
- Changes auto-reload (development mode)
- Run tests: `docker-compose exec backend pytest`

**Mobile:**
- Edit files in `mobile/lib/`
- Hot reload: Press `r` in terminal
- Hot restart: Press `R` in terminal
- Run tests: `flutter test`

### 3. Database Changes

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migration
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

### 4. Code Quality

**Backend:**
```bash
# Linting
docker-compose exec backend ruff check .

# Formatting
docker-compose exec backend ruff format .

# Type checking
docker-compose exec backend mypy src/
```

**Mobile:**
```bash
# Analysis
flutter analyze

# Formatting
dart format lib/

# Tests
flutter test
```

### 5. Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Description of changes"

# Push to remote
git push origin feature/your-feature-name

# Create pull request on GitHub
```

## Troubleshooting

### Backend Issues

**Problem: Services won't start**
```bash
# Check Docker status
docker-compose ps

# View logs
docker-compose logs

# Restart services
docker-compose restart

# Clean restart
docker-compose down -v
docker-compose up -d
```

**Problem: Database connection error**
```bash
# Check postgres is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

**Problem: Port already in use**
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Mac/Linux

# Kill process or change port in docker-compose.yml
```

### Mobile App Issues

**Problem: Can't connect to backend**

1. **Verify backend is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check API URL in `env.dart`:**
   - Android Emulator: `http://10.0.2.2:8000`
   - iOS Simulator: `http://localhost:8000`
   - Physical device: `http://YOUR_IP:8000`

3. **Verify firewall isn't blocking**

4. **Check network connectivity**

**Problem: Build errors**
```bash
# Clean build
flutter clean
flutter pub get
flutter run

# Clear cache
flutter pub cache repair

# Update Flutter
flutter upgrade
```

**Problem: Dependency conflicts**
```bash
# Remove lock file
rm pubspec.lock

# Get fresh dependencies
flutter pub get
```

### Common Issues

**Problem: Hot reload not working**
- Restart app with `R`
- Check for syntax errors
- Rebuild: `flutter run`

**Problem: Slow performance**
- Use release mode: `flutter run --release`
- Profile app: `flutter run --profile`
- Check for memory leaks

**Problem: SSL/Certificate errors**
- Check system date/time
- Update certificates
- Disable SSL pinning in development

## Next Steps

### Immediate Tasks
1. ✅ Complete directory structure setup
2. 🔄 Implement Properties CRUD screens
3. 🔄 Implement Tenants CRUD screens
4. 🔄 Implement Payments recording
5. 🔄 Implement Bills management

### Phase 2
- Add offline sync with SQLite
- Integrate payment gateways (Khalti, eSewa)
- Add push notifications (Firebase)
- Implement analytics dashboards
- Add report generation

### Phase 3
- Add automated tests
- Performance optimization
- Security hardening
- Production deployment
- App store submission

## Support

- **Documentation**: Check `docs/` folder
- **Issues**: Create GitHub issue
- **Email**: support@meroghar.com

## License

Copyright © 2025 Meroghar. All rights reserved.
