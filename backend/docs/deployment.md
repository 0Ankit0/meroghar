# MeroGhar Deployment Guide

**Version**: 1.0.0  
**Last Updated**: January 29, 2025

This guide covers deployment of the MeroGhar rental management system to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Environment Setup](#environment-setup)
4. [Database Setup](#database-setup)
5. [Backend Deployment](#backend-deployment)
6. [Mobile App Deployment](#mobile-app-deployment)
7. [Infrastructure Setup](#infrastructure-setup)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Security Considerations](#security-considerations)
10. [Backup and Recovery](#backup-and-recovery)
11. [Scaling](#scaling)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Services

- **PostgreSQL 14+**: Database server
- **Redis 6+**: Cache and Celery broker
- **Python 3.11+**: Backend runtime
- **Node.js 18+**: Build tools
- **Nginx**: Reverse proxy (production)
- **AWS S3 or compatible**: File storage
- **Firebase**: Push notifications (FCM)
- **Domain and SSL Certificate**: HTTPS
- **Payment Gateway Accounts**: Khalti, eSewa, IME Pay

### Development Tools

- Docker and Docker Compose (local development)
- Git (version control)
- VS Code or PyCharm (IDE)

### Cloud Providers (Choose One)

- **AWS**: EC2, RDS, S3, CloudFront, Route53
- **DigitalOcean**: Droplets, Managed PostgreSQL, Spaces
- **Heroku**: App platform (easiest for small deployments)
- **Google Cloud Platform**: Compute Engine, Cloud SQL

---

## Architecture Overview

### System Components

```
┌─────────────────┐
│   Mobile App    │ (Flutter)
│   iOS/Android   │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│  Load Balancer  │ (Nginx/ALB)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ API-1  │ │ API-2  │ (FastAPI + Gunicorn)
└───┬────┘ └───┬────┘
    │          │
    └────┬─────┘
         │
    ┌────┴─────────┬──────────┬──────────┐
    │              │          │          │
    ▼              ▼          ▼          ▼
┌────────┐  ┌──────────┐ ┌────────┐ ┌────────┐
│Postgres│  │  Redis   │ │Celery  │ │   S3   │
│   DB   │  │  Cache   │ │Workers │ │Storage │
└────────┘  └──────────┘ └────────┘ └────────┘
```

### Technology Stack

**Backend**:

- FastAPI (async web framework)
- SQLAlchemy (ORM)
- Alembic (migrations)
- Celery (background tasks)
- Gunicorn (WSGI server)
- Redis (cache + broker)
- PostgreSQL (database)

**Mobile**:

- Flutter (cross-platform framework)
- Provider (state management)
- SQLite (local database)
- Firebase Cloud Messaging (push notifications)

**Infrastructure**:

- Nginx (reverse proxy)
- Docker (containerization)
- GitHub Actions (CI/CD)
- Sentry (error monitoring)

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/meroghar.git
cd meroghar
```

### 2. Backend Environment Variables

Create `backend/.env`:

```bash
# Application
APP_NAME=MeroGhar
ENV=production
DEBUG=false
SECRET_KEY=<generate-strong-random-key-64-chars>
API_VERSION=v1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/meroghar_prod
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=<your-redis-password>

# JWT Authentication
JWT_SECRET_KEY=<generate-strong-random-key-64-chars>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS
ALLOWED_ORIGINS=https://app.meroghar.com,https://meroghar.com
ALLOWED_HOSTS=api.meroghar.com,*.meroghar.com

# File Storage (S3)
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
AWS_S3_BUCKET=meroghar-prod
AWS_S3_REGION=ap-south-1
AWS_S3_ENDPOINT_URL=https://s3.ap-south-1.amazonaws.com

# Payment Gateways
KHALTI_SECRET_KEY=<your-khalti-secret>
KHALTI_PUBLIC_KEY=<your-khalti-public>
KHALTI_WEBHOOK_SECRET=<webhook-secret>

ESEWA_MERCHANT_ID=<your-esewa-merchant-id>
ESEWA_SECRET_KEY=<your-esewa-secret>
ESEWA_ENVIRONMENT=production

IMEPAY_MERCHANT_CODE=<your-imepay-code>
IMEPAY_API_KEY=<your-imepay-api-key>
IMEPAY_SECRET_KEY=<your-imepay-secret>

# Messaging
TWILIO_ACCOUNT_SID=<your-twilio-sid>
TWILIO_AUTH_TOKEN=<your-twilio-token>
TWILIO_PHONE_NUMBER=<your-twilio-number>
TWILIO_WHATSAPP_NUMBER=<your-twilio-whatsapp>

# Firebase Cloud Messaging
FCM_SERVER_KEY=<your-fcm-server-key>
FCM_PROJECT_ID=<your-firebase-project-id>

# Monitoring
SENTRY_DSN=<your-sentry-dsn>
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Email (for reports)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@meroghar.com
SMTP_PASSWORD=<your-smtp-password>
SMTP_FROM=MeroGhar <noreply@meroghar.com>

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_TASK_ALWAYS_EAGER=false

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_AUTH_REQUESTS=10/minute
RATE_LIMIT_API_REQUESTS=100/minute
```

### 3. Mobile Environment Variables

Create `mobile/lib/config/env.dart`:

```dart
class Environment {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://api.meroghar.com/api/v1',
  );

  static const String appName = 'MeroGhar';
  static const String appVersion = '1.0.0';
  static const String environment = 'production';

  // Firebase
  static const String firebaseProjectId = '<your-firebase-project>';

  // Payment Gateways
  static const String khaltiPublicKey = '<your-khalti-public-key>';

  // Feature Flags
  static const bool enableOfflineMode = true;
  static const bool enablePushNotifications = true;
  static const bool enableAnalytics = true;

  // Timeouts
  static const Duration apiTimeout = Duration(seconds: 30);
  static const Duration syncInterval = Duration(minutes: 15);
}
```

---

## Database Setup

### 1. Install PostgreSQL

**Ubuntu/Debian**:

```bash
sudo apt update
sudo apt install postgresql-14 postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS**:

```bash
brew install postgresql@14
brew services start postgresql@14
```

### 2. Create Database and User

```bash
sudo -u postgres psql

-- Create database
CREATE DATABASE meroghar_prod;

-- Create user with strong password
CREATE USER meroghar_user WITH ENCRYPTED PASSWORD '<strong-password>';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE meroghar_prod TO meroghar_user;

-- Exit
\q
```

### 3. Configure PostgreSQL (Production)

Edit `/etc/postgresql/14/main/postgresql.conf`:

```conf
# Performance tuning
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 2621kB
min_wal_size = 1GB
max_wal_size = 4GB

# Enable row-level security
row_security = on
```

Edit `/etc/postgresql/14/main/pg_hba.conf`:

```conf
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   all             all                                     peer
host    all             all             127.0.0.1/32           scram-sha-256
host    all             all             ::1/128                scram-sha-256
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### 4. Run Migrations

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run all migrations
alembic upgrade head

# Verify
alembic current
```

### 5. Create Indexes (Performance)

```sql
-- Connect to database
psql meroghar_prod -U meroghar_user

-- Payments indexes
CREATE INDEX IF NOT EXISTS idx_payments_tenant_id ON payments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_payments_payment_date ON payments(payment_date DESC);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at DESC);

-- Bills indexes
CREATE INDEX IF NOT EXISTS idx_bills_property_id ON bills(property_id);
CREATE INDEX IF NOT EXISTS idx_bills_due_date ON bills(due_date);
CREATE INDEX IF NOT EXISTS idx_bills_status ON bills(status);

-- Tenants indexes
CREATE INDEX IF NOT EXISTS idx_tenants_property_id ON tenants(property_id);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);
CREATE INDEX IF NOT EXISTS idx_tenants_user_id ON tenants(user_id);

-- Expenses indexes
CREATE INDEX IF NOT EXISTS idx_expenses_property_id ON expenses(property_id);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
CREATE INDEX IF NOT EXISTS idx_expenses_expense_date ON expenses(expense_date DESC);

-- Documents indexes
CREATE INDEX IF NOT EXISTS idx_documents_tenant_id ON documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_expiration_date ON documents(expiration_date);

-- Notifications indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_payments_tenant_date ON payments(tenant_id, payment_date DESC);
CREATE INDEX IF NOT EXISTS idx_bills_property_status ON bills(property_id, status);
CREATE INDEX IF NOT EXISTS idx_expenses_property_date ON expenses(property_id, expense_date DESC);
```

---

## Backend Deployment

### Option 1: Docker Deployment (Recommended)

#### 1. Create Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run with Gunicorn
CMD ["gunicorn", "src.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

#### 2. Create Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:14-alpine
    container_name: meroghar-postgres
    environment:
      POSTGRES_DB: meroghar_prod
      POSTGRES_USER: meroghar_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U meroghar_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: meroghar-redis
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 256mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: ./backend
    container_name: meroghar-api
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://meroghar_user:${DB_PASSWORD}@postgres:5432/meroghar_prod
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    env_file:
      - ./backend/.env
    ports:
      - "8000:8000"
    volumes:
      - ./backend/logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery-worker:
    build: ./backend
    container_name: meroghar-celery-worker
    command: celery -A src.tasks.celery_app worker --loglevel=info --concurrency=4
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://meroghar_user:${DB_PASSWORD}@postgres:5432/meroghar_prod
      CELERY_BROKER_URL: redis://:${REDIS_PASSWORD}@redis:6379/1
      CELERY_RESULT_BACKEND: redis://:${REDIS_PASSWORD}@redis:6379/2
    env_file:
      - ./backend/.env
    volumes:
      - ./backend/logs:/app/logs
    restart: unless-stopped

  celery-beat:
    build: ./backend
    container_name: meroghar-celery-beat
    command: celery -A src.tasks.celery_app beat --loglevel=info
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://meroghar_user:${DB_PASSWORD}@postgres:5432/meroghar_prod
      CELERY_BROKER_URL: redis://:${REDIS_PASSWORD}@redis:6379/1
      CELERY_RESULT_BACKEND: redis://:${REDIS_PASSWORD}@redis:6379/2
    env_file:
      - ./backend/.env
    volumes:
      - ./backend/logs:/app/logs
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: meroghar-nginx
    depends_on:
      - api
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/logs:/var/log/nginx
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### 3. Deploy with Docker

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=4
```

### Option 2: Manual Deployment (VPS)

#### 1. Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install PostgreSQL and Redis
sudo apt install postgresql-14 redis-server -y

# Install Nginx
sudo apt install nginx -y

# Install system libraries
sudo apt install build-essential libpq-dev libssl-dev libffi-dev -y
```

#### 2. Setup Application

```bash
# Create app user
sudo useradd -m -s /bin/bash meroghar

# Clone repository
sudo su - meroghar
git clone https://github.com/yourusername/meroghar.git
cd meroghar/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Copy environment file
cp .env.example .env
nano .env  # Edit with production values

# Run migrations
alembic upgrade head
```

#### 3. Create Systemd Services

Create `/etc/systemd/system/meroghar-api.service`:

```ini
[Unit]
Description=MeroGhar API Server
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=meroghar
Group=meroghar
WorkingDirectory=/home/meroghar/meroghar/backend
Environment="PATH=/home/meroghar/meroghar/backend/venv/bin"
ExecStart=/home/meroghar/meroghar/backend/venv/bin/gunicorn src.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile /home/meroghar/meroghar/backend/logs/access.log \
    --error-logfile /home/meroghar/meroghar/backend/logs/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/meroghar-celery-worker.service`:

```ini
[Unit]
Description=MeroGhar Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=meroghar
Group=meroghar
WorkingDirectory=/home/meroghar/meroghar/backend
Environment="PATH=/home/meroghar/meroghar/backend/venv/bin"
ExecStart=/home/meroghar/meroghar/backend/venv/bin/celery -A src.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --logfile=/home/meroghar/meroghar/backend/logs/celery-worker.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/meroghar-celery-beat.service`:

```ini
[Unit]
Description=MeroGhar Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=simple
User=meroghar
Group=meroghar
WorkingDirectory=/home/meroghar/meroghar/backend
Environment="PATH=/home/meroghar/meroghar/backend/venv/bin"
ExecStart=/home/meroghar/meroghar/backend/venv/bin/celery -A src.tasks.celery_app beat \
    --loglevel=info \
    --logfile=/home/meroghar/meroghar/backend/logs/celery-beat.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 4. Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable meroghar-api
sudo systemctl enable meroghar-celery-worker
sudo systemctl enable meroghar-celery-beat

# Start services
sudo systemctl start meroghar-api
sudo systemctl start meroghar-celery-worker
sudo systemctl start meroghar-celery-beat

# Check status
sudo systemctl status meroghar-api
sudo systemctl status meroghar-celery-worker
sudo systemctl status meroghar-celery-beat
```

#### 5. Configure Nginx

Create `/etc/nginx/sites-available/meroghar`:

```nginx
upstream api_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name api.meroghar.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.meroghar.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/api.meroghar.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.meroghar.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/meroghar-access.log;
    error_log /var/log/nginx/meroghar-error.log;

    # Client body size (for file uploads)
    client_max_body_size 10M;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    location / {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Disable buffering for SSE
        proxy_buffering off;

        # Keep-alive
        proxy_set_header Connection "";
    }

    # Health check endpoint (no auth)
    location /health {
        proxy_pass http://api_backend;
        access_log off;
    }

    # Static files (if any)
    location /static/ {
        alias /home/meroghar/meroghar/backend/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/meroghar /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d api.meroghar.com

# Auto-renewal (cron job already created by certbot)
sudo certbot renew --dry-run
```

---

## Mobile App Deployment

### iOS Deployment

#### 1. Prerequisites

- macOS with Xcode 14+
- Apple Developer Account ($99/year)
- iOS device or simulator

#### 2. Configure iOS Project

```bash
cd mobile
flutter pub get

# Open iOS project
open ios/Runner.xcworkspace
```

In Xcode:

1. Update Bundle Identifier: `com.meroghar.app`
2. Select Development Team
3. Configure Signing & Capabilities
4. Add Push Notifications capability
5. Add Background Modes capability (Remote notifications)

#### 3. Configure Firebase

1. Download `GoogleService-Info.plist` from Firebase Console
2. Add to `ios/Runner/` directory
3. Configure in `ios/Runner/Info.plist`

#### 4. Build Release

```bash
# Build IPA
flutter build ipa --release

# Or build for specific device
flutter build ios --release
```

#### 5. Upload to App Store

1. Open `build/ios/archive/Runner.xcarchive` in Xcode
2. Click "Distribute App"
3. Select "App Store Connect"
4. Follow upload wizard
5. Submit for review in App Store Connect

### Android Deployment

#### 1. Configure Signing

Create `android/key.properties`:

```properties
storePassword=<your-keystore-password>
keyPassword=<your-key-password>
keyAlias=meroghar
storeFile=../keystore.jks
```

Generate keystore:

```bash
keytool -genkey -v -keystore android/keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias meroghar
```

#### 2. Update `android/app/build.gradle`

```gradle
android {
    defaultConfig {
        applicationId "com.meroghar.app"
        minSdkVersion 21
        targetSdkVersion 33
        versionCode 1
        versionName "1.0.0"
    }

    signingConfigs {
        release {
            keyAlias keystoreProperties['keyAlias']
            keyPassword keystoreProperties['keyPassword']
            storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
            storePassword keystoreProperties['storePassword']
        }
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            shrinkResources true
        }
    }
}
```

#### 3. Configure Firebase

1. Download `google-services.json` from Firebase Console
2. Add to `android/app/` directory

#### 4. Build Release

```bash
# Build APK
flutter build apk --release

# Build App Bundle (recommended for Play Store)
flutter build appbundle --release
```

#### 5. Upload to Play Store

1. Go to Google Play Console
2. Create new application
3. Upload `build/app/outputs/bundle/release/app-release.aab`
4. Fill out store listing information
5. Submit for review

---

## Infrastructure Setup

### AWS Deployment

#### 1. RDS for PostgreSQL

```bash
# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier meroghar-prod \
    --db-instance-class db.t3.medium \
    --engine postgres \
    --engine-version 14.7 \
    --master-username meroghar_user \
    --master-user-password <strong-password> \
    --allocated-storage 100 \
    --storage-type gp3 \
    --backup-retention-period 7 \
    --multi-az \
    --publicly-accessible false \
    --vpc-security-group-ids sg-xxxxx
```

#### 2. ElastiCache for Redis

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
    --cache-cluster-id meroghar-redis \
    --engine redis \
    --cache-node-type cache.t3.medium \
    --num-cache-nodes 1 \
    --engine-version 7.0 \
    --security-group-ids sg-xxxxx
```

#### 3. S3 for File Storage

```bash
# Create S3 bucket
aws s3api create-bucket \
    --bucket meroghar-prod \
    --region ap-south-1 \
    --create-bucket-configuration LocationConstraint=ap-south-1

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket meroghar-prod \
    --versioning-configuration Status=Enabled

# Set CORS
aws s3api put-bucket-cors \
    --bucket meroghar-prod \
    --cors-configuration file://cors-config.json
```

`cors-config.json`:

```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["https://api.meroghar.com"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

#### 4. EC2 for API Servers

```bash
# Launch EC2 instance
aws ec2 run-instances \
    --image-id ami-xxxxx \
    --instance-type t3.medium \
    --key-name meroghar-key \
    --security-group-ids sg-xxxxx \
    --subnet-id subnet-xxxxx \
    --iam-instance-profile Name=meroghar-api-role \
    --user-data file://user-data.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=meroghar-api}]'
```

#### 5. Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
    --name meroghar-alb \
    --subnets subnet-xxxxx subnet-yyyyy \
    --security-groups sg-xxxxx \
    --scheme internet-facing \
    --type application

# Create target group
aws elbv2 create-target-group \
    --name meroghar-api-targets \
    --protocol HTTP \
    --port 8000 \
    --vpc-id vpc-xxxxx \
    --health-check-path /health \
    --health-check-interval-seconds 30
```

---

## Monitoring and Logging

### 1. Sentry Setup

```python
# In backend/src/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENV,
    traces_sample_rate=0.1,
    integrations=[
        FastApiIntegration(),
        CeleryIntegration(),
    ],
)
```

### 2. Structured Logging

```python
# In backend/src/core/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        return json.dumps(log_data)

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("/app/logs/app.log"),
        logging.StreamHandler(),
    ]
)
```

### 3. Health Check Endpoints

```python
# In backend/src/api/v1/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from redis import Redis

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Basic health check"""
    return {"status": "healthy"}

@router.get("/health/db")
async def db_health(db: Session = Depends(get_db)):
    """Check database connectivity"""
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@router.get("/health/redis")
async def redis_health():
    """Check Redis connectivity"""
    try:
        redis_client = Redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "redis": "disconnected", "error": str(e)}
```

### 4. Prometheus Metrics (Optional)

```python
# Install prometheus_client
pip install prometheus-client

# In backend/src/core/metrics.py
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    request_duration.observe(duration)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## Security Considerations

### 1. Environment Variables

- **NEVER** commit `.env` files to Git
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Rotate credentials regularly
- Use different credentials for each environment

### 2. Database Security

```sql
-- Enable SSL connections only
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/path/to/cert.pem';
ALTER SYSTEM SET ssl_key_file = '/path/to/key.pem';

-- Enforce SSL
hostssl all all 0.0.0.0/0 scram-sha-256

-- Limit connections per user
ALTER ROLE meroghar_user CONNECTION LIMIT 50;
```

### 3. API Security Checklist

- [x] HTTPS only (no HTTP in production)
- [x] JWT token expiration (short-lived access tokens)
- [x] Rate limiting on all endpoints
- [x] Input validation with Pydantic
- [x] SQL injection prevention (SQLAlchemy ORM)
- [x] XSS protection (escape user input)
- [x] CSRF protection (for web interface)
- [x] CORS configuration (whitelist origins only)
- [x] Row-level security in PostgreSQL
- [x] Password hashing (bcrypt cost 12+)
- [x] Webhook signature verification
- [x] File upload validation (size, type, virus scan)
- [x] Secure headers (HSTS, X-Frame-Options, etc.)

### 4. Firewall Rules

```bash
# UFW firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (redirect to HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 5. Regular Security Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
pip list --outdated
pip install --upgrade <package>

# Update Flutter
flutter upgrade

# Audit dependencies
pip-audit  # Python
flutter pub outdated  # Flutter
```

---

## Backup and Recovery

### 1. PostgreSQL Backups

**Automated Daily Backups**:

```bash
# Create backup script
sudo nano /usr/local/bin/backup-postgres.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATABASE="meroghar_prod"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U meroghar_user -h localhost $DATABASE | gzip > $BACKUP_DIR/${DATABASE}_${TIMESTAMP}.sql.gz

# Delete backups older than 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

# Upload to S3
aws s3 cp $BACKUP_DIR/${DATABASE}_${TIMESTAMP}.sql.gz s3://meroghar-backups/postgres/
```

```bash
chmod +x /usr/local/bin/backup-postgres.sh

# Add cron job (daily at 2 AM)
sudo crontab -e
0 2 * * * /usr/local/bin/backup-postgres.sh
```

### 2. Restore from Backup

```bash
# Download from S3
aws s3 cp s3://meroghar-backups/postgres/meroghar_prod_20250129_020000.sql.gz .

# Restore
gunzip meroghar_prod_20250129_020000.sql.gz
psql -U meroghar_user -h localhost meroghar_prod < meroghar_prod_20250129_020000.sql
```

### 3. Redis Backups

Redis automatically saves snapshots to disk. Configure in `redis.conf`:

```conf
save 900 1      # Save after 15 min if 1 key changed
save 300 10     # Save after 5 min if 10 keys changed
save 60 10000   # Save after 1 min if 10000 keys changed

dir /var/lib/redis
dbfilename dump.rdb
```

### 4. S3 Versioning

Enable versioning on S3 bucket to recover deleted files:

```bash
aws s3api put-bucket-versioning \
    --bucket meroghar-prod \
    --versioning-configuration Status=Enabled
```

---

## Scaling

### Horizontal Scaling

**API Servers**:

```bash
# Add more API instances behind load balancer
docker-compose -f docker-compose.prod.yml up -d --scale api=4
```

**Celery Workers**:

```bash
# Add more worker instances
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=8
```

### Vertical Scaling

**Database**:

- Upgrade to larger RDS instance type
- Increase connection pool size
- Add read replicas for read-heavy workloads

**Redis**:

- Upgrade to larger ElastiCache node
- Enable clustering for high availability

### Caching Strategy

```python
# In backend/src/core/cache.py
import redis
from functools import wraps

redis_client = redis.from_url(settings.REDIS_URL)

def cache_response(expire=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expire, json.dumps(result))
            return result
        return wrapper
    return decorator

# Usage
@cache_response(expire=600)
async def get_property_list(owner_id: str):
    return await db.query(Property).filter_by(owner_id=owner_id).all()
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Errors**

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connections
psql -U meroghar_user -h localhost meroghar_prod

# View connection logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

**2. Celery Tasks Not Running**

```bash
# Check Celery worker status
sudo systemctl status meroghar-celery-worker

# View Celery logs
sudo journalctl -u meroghar-celery-worker -f

# Check Redis connectivity
redis-cli ping

# Inspect queued tasks
redis-cli -n 1 LLEN celery
```

**3. API Errors**

```bash
# Check API logs
sudo journalctl -u meroghar-api -f

# Check Nginx logs
sudo tail -f /var/log/nginx/meroghar-error.log

# Test API directly
curl http://localhost:8000/health
```

**4. High Memory Usage**

```bash
# Check memory
free -h
htop

# Check largest processes
ps aux --sort=-%mem | head -10

# Restart services if needed
sudo systemctl restart meroghar-api
sudo systemctl restart meroghar-celery-worker
```

**5. SSL Certificate Issues**

```bash
# Check certificate expiration
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test Nginx configuration
sudo nginx -t
```

### Performance Tuning

**Database**:

```sql
-- Find slow queries
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;

-- Analyze table statistics
ANALYZE tenants;
ANALYZE payments;

-- Vacuum database
VACUUM ANALYZE;
```

**API**:

```python
# Enable SQL query logging in development
# In backend/src/core/database.py
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,  # Log all SQL queries
)
```

---

## Rollback Procedure

### Database Rollback

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# View migration history
alembic history
```

### Application Rollback

**Docker**:

```bash
# Tag previous version
docker tag meroghar-api:latest meroghar-api:rollback

# Deploy previous version
docker-compose -f docker-compose.prod.yml up -d api
```

**Manual**:

```bash
# Checkout previous version
git checkout <previous-commit>

# Restart services
sudo systemctl restart meroghar-api
sudo systemctl restart meroghar-celery-worker
```

---

## Maintenance Windows

Schedule regular maintenance windows:

1. **Database Maintenance** (Monthly):

   - Vacuum and analyze tables
   - Update statistics
   - Check for index bloat

2. **Security Updates** (Weekly):

   - System package updates
   - Python dependency updates
   - SSL certificate renewal check

3. **Backup Verification** (Monthly):
   - Test restore from backup
   - Verify backup integrity
   - Check backup retention

---

## Support and Resources

- **Documentation**: https://docs.meroghar.com
- **Status Page**: https://status.meroghar.com
- **Support Email**: devops@meroghar.com
- **On-Call**: PagerDuty integration

---

**Last Updated**: January 29, 2025  
**Deployment Guide Version**: 1.0.0
