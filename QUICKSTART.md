# Meroghar Rental Management System - Quick Start

This guide will help you set up and run the complete Meroghar application in under 10 minutes.

## ⚡ Prerequisites Check

Before starting, ensure you have:

- [ ] **Docker Desktop** or **Podman Desktop** installed and running
- [ ] **Flutter SDK** 3.10+ installed (`flutter --version`)
- [ ] **Git** installed
- [ ] At least 8GB RAM available
- [ ] 10GB free disk space

> **Note**: This guide supports both Docker and Podman. Commands are provided for both tools.

## 🚀 5-Step Quick Start

### Step 1: Start Backend Services (2 minutes)

#### Using Docker

```bash
# From project root directory
cd D:\Projects\python\meroghar

# Start all services
docker compose up -d

# Wait for services to be healthy (check status)
docker compose ps

# You should see all services as "Up" and "healthy"
```

#### Using Podman

```powershell
# From project root directory
cd D:\Projects\python\meroghar

# Start all services
podman-compose up -d
# Or using Podman Desktop GUI: Click "Play" on the compose file

# Check status
podman ps

# You should see all containers running (meroghar_backend, meroghar_postgres, etc.)
```

**Verify Backend**: Open http://localhost:8000/docs in your browser. You should see the API documentation.

### Step 2: Initialize Database (1 minute)

#### Using Docker

```bash
# Run database migrations
docker compose exec backend alembic upgrade head

# You should see "Running upgrade ... OK"
```

#### Using Podman

```powershell
# Run database migrations
podman exec -it meroghar_backend alembic upgrade head

# You should see "Running upgrade ... OK"
```

### Step 3: Setup Mobile App (2 minutes)

```bash
# Navigate to mobile directory
cd mobile

# Install Flutter dependencies
flutter pub get
```

**Note**: If you see any package version warnings, that's normal. The app will still work.

### Step 4: Configure API Endpoint (1 minute)

Open `mobile\lib\services\api_service.dart` and verify the API URL:

```dart
// For web builds (default)
static const String baseUrl = 'http://localhost:8000';

// For Android Emulator
// static const String baseUrl = 'http://10.0.2.2:8000';

// For iOS Simulator
// static const String baseUrl = 'http://localhost:8000';

// For Physical Device (uncomment and use your IP)
// static const String baseUrl = 'http://192.168.1.100:8000';
```

**Find your IP** (if using physical device):

```bash
# Windows
ipconfig
# Look for "IPv4 Address"

# Mac/Linux
ifconfig
# Look for "inet"
```

### Step 5: Run the App (2 minutes)

#### For Web (Recommended for Development)

```bash
# From mobile directory
cd D:\Projects\python\meroghar\mobile

# Run the web app
flutter run -d chrome --web-port 3000

# Or run on edge
flutter run -d edge --web-port 3000

# Wait for app to build and launch
# Access at: http://localhost:3000
```

#### For Android/iOS (Physical Device or Emulator)

```bash
# From mobile directory
cd D:\Projects\python\meroghar\mobile

# Check connected devices
flutter devices

# Run the app
flutter run

# Wait for app to build and launch
```

**Note**: For Android builds, you need Java JDK and Android SDK installed. Web builds work immediately without additional setup.

## ✅ Verify Everything Works

### Backend Verification

1. **API Docs**: http://localhost:8000/docs ✅
2. **Health Check**: http://localhost:8000/health ✅
3. **PgAdmin**: http://localhost:5050 ✅
   - Email: admin@meroghar.com
   - Password: meroghar_admin_password

### Mobile App Verification

1. App launches successfully ✅
2. You see the login screen ✅
3. Navigation works (tap between tabs) ✅

## 🎯 What You Have Now

### ✅ Working Components

- **Backend API** running on port 8000
- **PostgreSQL** database on port 5432
- **Redis** cache on port 6379
- **Celery** workers for background tasks
- **Mobile App** with authentication ready
- **Dashboard** with role-based navigation
- **Constants** properly configured
- **Routing** system set up

### 🔄 Ready to Implement

All placeholder screens are created. You can now implement:

1. Properties management
2. Tenants management
3. Payments tracking
4. Bills management
5. Expenses tracking
6. And more...

## 📁 Project Structure

```
meroghar/
├── backend/                  # Backend API (Python/FastAPI)
│   ├── src/
│   │   ├── core/
│   │   │   ├── config.py     # Backend config ✅
│   │   │   └── constants.py  # Backend constants ✅
│   │   ├── api/              # API endpoints
│   │   ├── models/           # Database models
│   │   └── ...
│   └── ...
│
├── mobile/                   # Mobile App (Flutter)
│   ├── lib/
│   │   ├── config/
│   │   │   ├── constants.dart  # App constants ✅
│   │   │   ├── env.dart        # Environment ✅
│   │   │   └── app_router.dart # Routing ✅
│   │   ├── screens/          # UI screens ✅
│   │   ├── services/         # API services ✅
│   │   └── ...
│   └── ...
│
└── docker-compose.yml        # Services config ✅
```

## 🛠️ Common Commands

### Backend (Docker)

```bash
# View logs
docker compose logs -f backend

# Restart backend
docker compose restart backend

# Stop all services
docker compose down

# Rebuild backend (after adding dependencies)
docker compose build --no-cache backend
docker compose up -d backend
```

### Backend (Podman)

```powershell
# View logs
podman logs -f meroghar_backend

# Restart backend
podman restart meroghar_backend

# Stop all services
podman-compose down

# Rebuild backend (after adding dependencies)
podman build --no-cache -t meroghar_backend -f backend/Dockerfile backend
podman-compose up -d
```

### Mobile

```bash
# Hot reload (while app running)
Press 'r'

# Hot restart (while app running)
Press 'R'

# Clean build
flutter clean && flutter pub get && flutter run

# Build for web
flutter build web --release

# Build APK (requires Android setup)
flutter build apk --release
```

## 🐛 Quick Troubleshooting

### Issue: Backend won't start

#### Docker

```bash
docker compose down -v
docker compose up -d
```

#### Podman

```powershell
podman-compose down
podman volume prune -f
podman-compose up -d
```

### Issue: "ModuleNotFoundError: No module named 'asyncpg'"

This means the backend image needs to be rebuilt with updated dependencies:

#### Docker

```bash
docker compose build --no-cache backend
docker compose up -d backend
```

#### Podman

```powershell
podman build --no-cache -t meroghar_backend -f backend/Dockerfile backend
podman-compose up -d
```

### Issue: Can't connect to API from mobile

1. Check backend is running: `docker compose ps` or `podman ps`
2. Verify API URL in `mobile/lib/services/api_service.dart`
3. For Android emulator, use `10.0.2.2` not `localhost`
4. For web builds, use `localhost:8000`
5. Check backend logs for CORS errors

### Issue: Flutter build errors

```bash
flutter clean
flutter pub get
flutter run
```

### Issue: Blank screen on Flutter web

1. Check browser console (F12) for JavaScript errors
2. Verify API endpoint is correct in `api_service.dart`
3. Check backend is running and accessible
4. Look for CORS errors in browser console
5. Try clearing browser cache (Ctrl+Shift+Delete)

### Issue: Port already in use

```bash
# Windows - Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:8000 | xargs kill -9
```

### Issue: Database connection errors

Check that PostgreSQL is running and the database name is correct:

```bash
# Docker
docker compose exec postgres psql -U meroghar -d meroghar -c "SELECT 1"

# Podman
podman exec -it meroghar_postgres psql -U meroghar -d meroghar -c "SELECT 1"
```

## 📚 Next Steps

### Immediate (Today)

1. ✅ Familiarize yourself with the codebase
2. ✅ Review `mobile/lib/config/constants.dart`
3. ✅ Check API documentation at http://localhost:8000/docs
4. 🔄 Implement Properties list screen

### Short Term (This Week)

1. Implement CRUD for Properties
2. Implement CRUD for Tenants
3. Add payment recording functionality
4. Create bills management screens

### Medium Term (This Month)

1. Implement offline sync with SQLite
2. Add payment gateway integration
3. Implement analytics dashboard
4. Add report generation

## 📖 Documentation

- **Setup Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Mobile Setup**: [mobile/SETUP.md](mobile/SETUP.md)
- **Directory Setup**: [mobile/DIRECTORY_SETUP.md](mobile/DIRECTORY_SETUP.md)
- **API Docs**: http://localhost:8000/docs (when running)

## 🆘 Need Help?

### Resources

- **Spec Document**: `specs/001-rental-management/spec.md`
- **Backend API Docs**: http://localhost:8000/docs
- **Flutter Docs**: https://flutter.dev/docs

### Support

- Create an issue on GitHub
- Email: support@meroghar.com
- Check documentation in `docs/` folder

## 🎉 Success!

If you've made it here and everything is working, congratulations! 🎊

You now have:

- ✅ A fully functional backend API
- ✅ A mobile app with authentication
- ✅ Proper constants management
- ✅ Clean architecture setup
- ✅ Ready-to-implement features

**Happy Coding! 🚀**

---

## 💡 Pro Tips

1. **Keep backend logs open**: `docker-compose logs -f backend`
2. **Use hot reload**: Press 'r' instead of restarting the app
3. **Check constants first**: All routes and endpoints are in constants files
4. **Use API docs**: Test endpoints at http://localhost:8000/docs
5. **Commit often**: Make small, focused commits

## ⚙️ Configuration Reference

### Backend (.env)

```env
DATABASE_URL=postgresql://meroghar:meroghar_dev_password@postgres:5432/meroghar
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-here
```

### Frontend (env.dart)

```dart
// In mobile/lib/services/api_service.dart
baseUrl = 'http://localhost:8000'     // Web builds
baseUrl = 'http://10.0.2.2:8000'      // Android Emulator
baseUrl = 'http://localhost:8000'     // iOS Simulator
baseUrl = 'http://YOUR_IP:8000'       // Physical Device
```

## 🔧 Recent Updates

### November 2025

- ✅ Added **asyncpg** dependency for async PostgreSQL support
- ✅ Added Nepali payment gateway SDKs (eSewa, Khalti, IME Pay)
- ✅ Fixed database connection issues
- ✅ Added Podman Desktop support
- ✅ Configured Flutter web platform
- ✅ Created home screen with navigation
- ✅ Fixed authentication provider setup

### Known Issues

- Android builds require Java JDK and Android SDK setup
- Some Flutter packages have newer versions available (safe to ignore)
- Browser may show blank screen if backend is not running

---

**Version**: 1.1.0  
**Last Updated**: 2025-11-04  
**Status**: ✅ Ready for Development  
**Container Runtime**: Docker or Podman supported
