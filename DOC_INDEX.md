# Meroghar Documentation Index

Welcome to the Meroghar Rental Management System documentation! This index will help you find the right documentation for your needs.

## 🚀 Getting Started (Start Here!)

Choose based on your goal:

### I want to run the app quickly
→ **[QUICKSTART.md](QUICKSTART.md)** - 5-step guide to get running in 10 minutes

### I want detailed setup instructions
→ **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete setup with troubleshooting

### I want to understand what's been built
→ **[SETUP_SUMMARY.md](SETUP_SUMMARY.md)** - Overview of all created files and features

## 📁 Project Documentation

### Backend
- **Configuration**: `backend/src/core/config.py`
- **Constants**: `backend/src/core/constants.py` ✅ Created
- **Environment Template**: `backend/.env.example`
- **API Documentation**: http://localhost:8000/docs (when running)

### Frontend
- **Main README**: [mobile/README.md](mobile/README.md) ✅ Updated
- **Setup Guide**: [mobile/SETUP.md](mobile/SETUP.md) ✅ Created
- **Directory Setup**: [mobile/DIRECTORY_SETUP.md](mobile/DIRECTORY_SETUP.md) ✅ Created
- **Constants**: `mobile/lib/config/constants.dart` ✅ Created
- **Environment**: `mobile/lib/config/env.dart` ✅ Created
- **Routing**: `mobile/lib/config/app_router.dart` ✅ Created

## 📚 Documentation by Topic

### Setup & Installation
1. [QUICKSTART.md](QUICKSTART.md) - Quick start (10 minutes)
2. [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup guide
3. [mobile/SETUP.md](mobile/SETUP.md) - Mobile app setup
4. [mobile/DIRECTORY_SETUP.md](mobile/DIRECTORY_SETUP.md) - Directory structure

### Architecture & Design
- [SETUP_SUMMARY.md](SETUP_SUMMARY.md) - Architecture overview
- `specs/001-rental-management/spec.md` - Feature specifications
- `specs/001-rental-management/data-model.md` - Data model

### Configuration
- **Backend Config**: `backend/src/core/config.py` & `constants.py`
- **Frontend Config**: `mobile/lib/config/` folder
- **Docker Config**: `docker-compose.yml`

### Development
- **Backend Development**: See [SETUP_GUIDE.md](SETUP_GUIDE.md#development-workflow)
- **Frontend Development**: See [mobile/README.md](mobile/README.md#-development)
- **Testing**: Each README has testing section

## 🎯 Documentation by User Type

### For Developers Starting Development

**Read in this order:**
1. [QUICKSTART.md](QUICKSTART.md) - Get everything running
2. [SETUP_SUMMARY.md](SETUP_SUMMARY.md) - Understand what exists
3. [mobile/README.md](mobile/README.md) - Understand mobile app structure
4. `mobile/lib/config/constants.dart` - Review available constants
5. `specs/001-rental-management/spec.md` - Review feature requirements

### For System Administrators / DevOps

**Read in this order:**
1. [SETUP_GUIDE.md](SETUP_GUIDE.md) - Complete system setup
2. `docker-compose.yml` - Understand services
3. `backend/.env.example` - Environment variables
4. [SETUP_GUIDE.md#troubleshooting](SETUP_GUIDE.md#troubleshooting) - Common issues

### For Frontend Developers

**Read in this order:**
1. [mobile/SETUP.md](mobile/SETUP.md) - Mobile setup
2. [mobile/README.md](mobile/README.md) - App overview
3. [mobile/DIRECTORY_SETUP.md](mobile/DIRECTORY_SETUP.md) - Structure
4. `mobile/lib/config/constants.dart` - Constants reference
5. `mobile/lib/config/app_router.dart` - Routing system

### For Backend Developers

**Read in this order:**
1. [SETUP_GUIDE.md](SETUP_GUIDE.md) - System setup
2. `backend/src/core/config.py` - Configuration
3. `backend/src/core/constants.py` - Constants
4. http://localhost:8000/docs - API documentation
5. `specs/001-rental-management/spec.md` - Requirements

## 🔍 Quick Reference

### Common Commands

**Start Backend:**
```bash
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

**Run Mobile App:**
```bash
cd mobile
flutter pub get
flutter run
```

**View Logs:**
```bash
docker-compose logs -f backend
```

**Stop Services:**
```bash
docker-compose down
```

### Important URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| PgAdmin | http://localhost:5050 | admin@meroghar.com / meroghar_admin_password |
| PostgreSQL | localhost:5432 | meroghar / meroghar_dev_password |
| Redis | localhost:6379 | - |

### Configuration Files

| Purpose | File | Status |
|---------|------|--------|
| Backend constants | `backend/src/core/constants.py` | ✅ Created |
| Backend config | `backend/src/core/config.py` | ✅ Exists |
| Frontend constants | `mobile/lib/config/constants.dart` | ✅ Created |
| Frontend config | `mobile/lib/config/env.dart` | ✅ Created |
| Routing | `mobile/lib/config/app_router.dart` | ✅ Created |
| Docker services | `docker-compose.yml` | ✅ Exists |

### Key Directories

| Directory | Purpose | Status |
|-----------|---------|--------|
| `backend/src/core/` | Backend configuration | ✅ |
| `backend/src/api/` | API endpoints | ✅ |
| `backend/src/models/` | Database models | ✅ |
| `mobile/lib/config/` | App configuration | ✅ |
| `mobile/lib/screens/` | UI screens | 🔄 Partial |
| `mobile/lib/services/` | Business logic | ✅ |
| `mobile/lib/providers/` | State management | ✅ |

Legend: ✅ Complete | 🔄 In Progress | ❌ Not Started

## 📊 Feature Status

### Completed Features ✅
- Authentication (Login, Register, Logout)
- JWT token management with auto-refresh
- Role-based navigation (Owner, Intermediary, Tenant)
- Dashboard with quick stats
- Constants management (frontend & backend)
- Routing system
- Docker configuration
- API service with interceptors
- Secure storage

### In Progress 🔄
- Properties CRUD
- Tenants CRUD
- Payments tracking
- Bills management
- Expenses tracking

### Planned 📋
- Offline sync
- Payment gateway integration
- Push notifications
- Analytics dashboard
- Reports generation
- Document management
- Messaging system

## 🐛 Troubleshooting

**Can't find what you need?**

1. Check the [Quick Reference](#-quick-reference) section above
2. See [SETUP_GUIDE.md#troubleshooting](SETUP_GUIDE.md#troubleshooting)
3. Check service-specific documentation:
   - Backend: API docs at http://localhost:8000/docs
   - Frontend: [mobile/README.md#-troubleshooting](mobile/README.md#-troubleshooting)

## 📞 Support

- **Email**: support@meroghar.com
- **Issues**: Create a GitHub issue
- **Documentation**: Check docs in each module

## 🗺️ Documentation Map

```
meroghar/
├── QUICKSTART.md              ← Start here!
├── SETUP_GUIDE.md             ← Detailed setup
├── SETUP_SUMMARY.md           ← What's been created
├── DOC_INDEX.md               ← This file
│
├── backend/
│   ├── README.md              ← Backend overview
│   ├── src/core/
│   │   ├── config.py          ← Backend configuration
│   │   └── constants.py       ← Backend constants ✅
│   └── .env.example           ← Environment template
│
├── mobile/
│   ├── README.md              ← Mobile app overview ✅
│   ├── SETUP.md               ← Mobile setup guide ✅
│   ├── DIRECTORY_SETUP.md     ← Directory structure ✅
│   └── lib/
│       ├── config/
│       │   ├── constants.dart ← App constants ✅
│       │   ├── env.dart       ← Environment ✅
│       │   └── app_router.dart ← Routing ✅
│       └── ...
│
├── specs/
│   └── 001-rental-management/
│       ├── spec.md            ← Feature specifications
│       ├── data-model.md      ← Data model
│       └── tasks.md           ← Implementation tasks
│
└── docker-compose.yml         ← Services configuration
```

## ✅ Setup Verification

Use this checklist to verify your setup:

- [ ] Read QUICKSTART.md
- [ ] Backend services running (`docker-compose ps`)
- [ ] Database initialized (`alembic upgrade head`)
- [ ] Mobile directories created
- [ ] Flutter dependencies installed
- [ ] App runs successfully
- [ ] Can login to the app
- [ ] Navigation works
- [ ] API accessible at http://localhost:8000/docs
- [ ] Reviewed constants files
- [ ] Familiar with project structure

## 🎯 Next Steps

Once you're set up:

1. **Implement Properties Module** (Priority 1)
   - Create property form
   - List properties
   - View property details

2. **Implement Tenants Module** (Priority 1)
   - Create tenant form
   - List tenants
   - View tenant details

3. **Implement Payments Module** (Priority 1)
   - Record payment form
   - Payment history
   - Generate receipts

## 📝 Notes

- All documentation is in Markdown format
- Code examples use actual project paths
- Configuration is Docker-aware
- Constants are centralized
- Routing is pre-configured

---

**Last Updated**: 2025-11-04  
**Version**: 1.0.0  
**Maintained By**: Meroghar Development Team

**Happy Coding! 🚀**
