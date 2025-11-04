# Meroghar Mobile App

A comprehensive house rental management system built with Flutter for property owners, intermediaries, and tenants.

## 🚀 Quick Start

### Prerequisites

- Flutter SDK 3.10+
- Docker Desktop (for backend)
- Android Studio or VS Code

### Setup & Run

```bash
# 1. Install dependencies
flutter pub get

# 2. Create directory structure
cd lib
powershell -ExecutionPolicy Bypass -File create_directories.ps1

# 3. Start backend services (from project root)
cd ../..
docker-compose up -d

# 4. Run the app
cd mobile
flutter run
```

For detailed instructions, see [SETUP.md](SETUP.md)

## 📋 Features

### ✅ Implemented
- User Authentication (Login/Register/Logout)
- Role-based Access Control (Owner/Intermediary/Tenant)
- Dashboard with Quick Stats
- Bottom Navigation
- Secure Token Storage
- API Integration with Auto-refresh
- Multi-language Support Setup
- Offline-first Architecture
- Constants Management
- Routing System

### 🔄 In Progress
- Properties Management (CRUD)
- Tenants Management (CRUD)
- Payments Tracking
- Bills Management & Allocation
- Expenses Tracking
- Documents Storage
- Messaging System
- Analytics Dashboard
- Reports Generation
- Settings & Preferences

## 🏗️ Architecture

### Technology Stack

- **Framework**: Flutter 3.10+
- **Language**: Dart 3.0+
- **State Management**: Provider
- **HTTP Client**: Dio
- **Local Storage**: SQLite, Secure Storage
- **Charts**: FL Chart
- **PDF**: pdf, printing, pdfrx
- **Notifications**: Firebase Cloud Messaging

### Project Structure

```
lib/
├── config/               # Configuration files
│   ├── constants.dart    # App-wide constants ✅
│   ├── env.dart          # Environment config ✅
│   └── app_router.dart   # Navigation routing ✅
│
├── models/               # Data models
│   ├── property/
│   ├── tenant/
│   ├── payment/
│   └── ...
│
├── providers/            # State management
│   ├── auth_provider.dart      ✅
│   ├── language_provider.dart  ✅
│   └── ...
│
├── screens/              # UI screens
│   ├── auth/             ✅
│   ├── home_screen.dart  ✅
│   ├── dashboard/
│   ├── properties/
│   ├── tenants/
│   └── ...
│
├── services/             # Business logic
│   ├── api_service.dart           ✅
│   ├── secure_storage_service.dart ✅
│   └── ...
│
├── utils/                # Utilities
│   ├── helpers/
│   ├── validators/
│   └── formatters/
│
├── widgets/              # Reusable widgets
│   ├── common/
│   ├── charts/
│   └── forms/
│
└── main.dart             # App entry point ✅
```

## 🔧 Configuration

### API Endpoint

Update in `lib/config/env.dart`:

```dart
// Android Emulator
static const String apiBaseUrl = 'http://10.0.2.2:8000';

// iOS Simulator
static const String apiBaseUrl = 'http://localhost:8000';

// Physical Device (use your machine's IP)
static const String apiBaseUrl = 'http://192.168.1.100:8000';
```

### Constants

All app constants are centralized in `lib/config/constants.dart`:

- API Endpoints
- App Routes
- User Roles
- Payment Methods
- Validation Rules
- UI Constants
- Error/Success Messages
- And more...

## 📱 Running on Different Platforms

### Android Emulator
```bash
flutter run
```

### iOS Simulator (Mac only)
```bash
flutter run -d ios
```

### Physical Device
```bash
# Connect device via USB
# Enable USB debugging
flutter devices
flutter run -d <device-id>
```

## 🐳 Backend Services

The app connects to backend services running in Docker:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

Services:
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PgAdmin**: http://localhost:5050
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🧪 Testing

```bash
# Run all tests
flutter test

# Run specific test file
flutter test test/widget_test.dart

# Run with coverage
flutter test --coverage

# Integration tests
flutter test integration_test/
```

## 🔨 Build

### Android APK
```bash
flutter build apk --release
# Output: build/app/outputs/flutter-apk/app-release.apk
```

### Android App Bundle
```bash
flutter build appbundle --release
# Output: build/app/outputs/bundle/release/app-release.aab
```

### iOS (Mac only)
```bash
flutter build ios --release
```

## 📚 Documentation

- [SETUP.md](SETUP.md) - Complete setup instructions
- [DIRECTORY_SETUP.md](DIRECTORY_SETUP.md) - Directory structure guide
- [../SETUP_GUIDE.md](../SETUP_GUIDE.md) - Full system setup guide

## 🛠️ Development

### Code Quality

```bash
# Analyze code
flutter analyze

# Format code
dart format lib/

# Check formatting
dart format --output=none --set-exit-if-changed lib/
```

### Hot Reload

While app is running:
- Press `r` for hot reload
- Press `R` for hot restart
- Press `q` to quit

### Debugging

```bash
# Run in debug mode
flutter run --debug

# Run with DevTools
flutter run --observatory-port=8888
```

## 🚧 Troubleshooting

### Can't connect to backend
1. Verify backend is running: `docker-compose ps`
2. Check API URL in `env.dart`
3. For Android emulator, use `10.0.2.2` not `localhost`
4. For physical device, use your machine's IP

### Build errors
```bash
flutter clean
flutter pub get
flutter run
```

### Dependency issues
```bash
rm pubspec.lock
flutter pub get
```

## 📝 Environment Variables

Create `lib/config/env.dart` based on `env.example.dart`:

```dart
// API Configuration
static const String apiBaseUrl = 'YOUR_API_URL';

// Firebase Configuration
static const String firebaseAndroidApiKey = 'YOUR_KEY';
// ... more config
```

## 🎯 Roadmap

### Phase 1 (Current)
- [x] Project setup
- [x] Authentication
- [x] Constants management
- [x] Routing system
- [ ] Properties CRUD
- [ ] Tenants CRUD
- [ ] Payments tracking

### Phase 2
- [ ] Bills management
- [ ] Expenses tracking
- [ ] Documents storage
- [ ] Offline sync
- [ ] Push notifications

### Phase 3
- [ ] Analytics dashboard
- [ ] Reports generation
- [ ] Payment gateway integration
- [ ] Messaging system
- [ ] Multi-language support

### Phase 4
- [ ] Performance optimization
- [ ] Security hardening
- [ ] App store submission
- [ ] Production deployment

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Write tests
4. Submit a pull request

## 📄 License

Copyright © 2025 Meroghar. All rights reserved.

## 📞 Support

- Email: support@meroghar.com
- Issues: GitHub Issues
- Documentation: `docs/` folder

## 🙏 Acknowledgments

- Flutter team for the amazing framework
- Community packages used in this project
- All contributors

---

**Version**: 0.1.0  
**Flutter**: 3.10+  
**Dart**: 3.0+  
**Last Updated**: 2025-11-04
