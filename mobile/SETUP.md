# Meroghar Mobile App - Setup Instructions

## Prerequisites

Before running the application, ensure you have the following installed:

1. **Flutter SDK** (3.10 or higher)
   - Download from: https://flutter.dev/docs/get-started/install
   
2. **Android Studio** or **VS Code** with Flutter extensions

3. **Docker Desktop** (for running backend services)
   - Download from: https://www.docker.com/products/docker-desktop

## Backend Setup (Docker)

The backend, database, and other services run in Docker containers.

### 1. Start Docker Services

```bash
# Navigate to project root
cd D:\Projects\python\meroghar

# Start all services (backend, postgres, redis, celery, pgadmin)
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs if needed
docker-compose logs -f backend
```

### 2. Service URLs

Once Docker is running, the following services will be available:

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PgAdmin** (Database UI): http://localhost:5050
  - Email: admin@meroghar.com
  - Password: meroghar_admin_password
- **PostgreSQL Database**: localhost:5432
- **Redis**: localhost:6379

### 3. Run Database Migrations

```bash
# Run migrations inside the backend container
docker-compose exec backend alembic upgrade head

# Or if you want to run migrations from your local machine:
cd backend
alembic upgrade head
```

## Mobile App Setup

### 1. Install Dependencies

```bash
cd mobile
flutter pub get
```

### 2. Configure API Endpoint

The API endpoint is already configured in `lib/config/env.dart`. By default, it's set to:

- **Android Emulator**: `http://10.0.2.2:8000`
- **iOS Simulator**: `http://localhost:8000`
- **Physical Device**: Update to your machine's IP (e.g., `http://192.168.1.100:8000`)

To change the API endpoint:

1. Open `mobile/lib/config/env.dart`
2. Update the `apiBaseUrl` constant:

```dart
static const String apiBaseUrl = 'http://YOUR_MACHINE_IP:8000';
```

### 3. Run the App

**On Android Emulator:**
```bash
flutter run
```

**On iOS Simulator (Mac only):**
```bash
flutter run -d ios
```

**On Physical Device:**
1. Enable USB debugging on your device
2. Connect via USB
3. Run:
```bash
flutter run -d <device-id>
```

To see available devices:
```bash
flutter devices
```

## Project Structure

```
meroghar/
├── backend/                 # FastAPI backend
│   ├── src/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configurations
│   │   │   ├── config.py   # Environment settings
│   │   │   └── constants.py # Backend constants
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── alembic/            # Database migrations
│   └── requirements.txt    # Python dependencies
│
├── mobile/                 # Flutter mobile app
│   ├── lib/
│   │   ├── config/
│   │   │   ├── constants.dart  # App constants
│   │   │   └── env.dart       # Environment config
│   │   ├── models/         # Data models
│   │   ├── providers/      # State management
│   │   ├── screens/        # UI screens
│   │   ├── services/       # API & local services
│   │   ├── utils/          # Utility functions
│   │   └── widgets/        # Reusable widgets
│   └── pubspec.yaml        # Flutter dependencies
│
└── docker-compose.yml      # Docker services configuration
```

## Available Features

The app currently includes:

### Completed:
✅ Authentication (Login/Register/Logout)
✅ Role-based navigation (Owner, Intermediary, Tenant)
✅ Dashboard with quick stats
✅ Constants management (frontend & backend)
✅ API service with auto-refresh tokens
✅ Secure storage for tokens
✅ Multi-language support setup
✅ Offline-first architecture

### In Progress (Placeholders Created):
🔄 Properties Management
🔄 Tenants Management
🔄 Payments Tracking
🔄 Bills Management
🔄 Expenses Tracking
🔄 Documents Storage
🔄 Messaging System
🔄 Analytics Dashboard
🔄 Reports Generation
🔄 Settings & Preferences

## Environment Variables

### Backend (.env)

The backend uses environment variables defined in `backend/.env`. Copy from `.env.example`:

```bash
cd backend
cp .env.example .env
```

Key variables for Docker setup:
```
DATABASE_URL=postgresql://meroghar:meroghar_dev_password@postgres:5432/meroghar
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-here-change-in-production
```

### Frontend (env.dart)

Frontend configuration is in `mobile/lib/config/env.dart`. Update for your environment:

```dart
// For Android Emulator
static const String apiBaseUrl = 'http://10.0.2.2:8000';

// For iOS Simulator  
static const String apiBaseUrl = 'http://localhost:8000';

// For Physical Device (use your machine's IP)
static const String apiBaseUrl = 'http://192.168.1.100:8000';
```

## Troubleshooting

### Backend Issues

**Services won't start:**
```bash
# Stop all containers
docker-compose down

# Remove volumes and restart
docker-compose down -v
docker-compose up -d
```

**Database connection errors:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View postgres logs
docker-compose logs postgres
```

### Mobile App Issues

**API connection errors:**
1. Verify backend is running: visit http://localhost:8000/docs
2. Check API URL in `env.dart` matches your setup
3. For Android Emulator, ensure using `10.0.2.2` not `localhost`
4. For physical devices, ensure your machine and device are on same network

**Build errors:**
```bash
# Clean and rebuild
flutter clean
flutter pub get
flutter run
```

**Dependencies issues:**
```bash
# Update Flutter
flutter upgrade

# Re-download dependencies
rm pubspec.lock
flutter pub get
```

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Mobile Tests
```bash
cd mobile
flutter test
```

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Default Test Users

After running migrations, you can create test users via the API or use seed data.

Example test accounts (if seeded):
- **Owner**: owner@meroghar.com / password123
- **Intermediary**: intermediary@meroghar.com / password123
- **Tenant**: tenant@meroghar.com / password123

## Next Steps

1. **Complete Screen Implementation**: Implement full CRUD operations for each module
2. **Add Offline Sync**: Implement SQLite local storage and sync logic
3. **Payment Gateway Integration**: Add Khalti, eSewa, IME Pay
4. **Push Notifications**: Configure Firebase Cloud Messaging
5. **Analytics**: Implement charts and reports
6. **Testing**: Add comprehensive unit and integration tests

## Support

For issues or questions:
- Email: support@meroghar.com
- Documentation: Check `docs/` folder for detailed guides

## License

Copyright © 2025 Meroghar. All rights reserved.
