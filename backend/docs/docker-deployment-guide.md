# Docker Deployment Guide

Complete guide for deploying MeroGhar backend using Docker and Docker Compose.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Production Deployment](#production-deployment)
6. [Container Management](#container-management)
7. [Monitoring & Logs](#monitoring--logs)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Overview

### Architecture

The MeroGhar backend runs as a multi-container Docker application:

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐            │
│  │PostgreSQL│  │  Redis   │  │  Backend   │            │
│  │  :5432   │  │  :6379   │  │   :8000    │            │
│  └────┬─────┘  └────┬─────┘  └──────┬─────┘            │
│       │             │               │                   │
│       │             └───────────────┘                   │
│       │                     │                           │
│  ┌────┴─────────────────────┴───────────────┐           │
│  │   Celery Worker   │  Celery Beat         │           │
│  └──────────────────────────────────────────┘           │
│                                                          │
│  ┌──────────┐                                            │
│  │ pgAdmin  │  (Database Management GUI)                │
│  │  :5050   │                                            │
│  └────┬─────┘                                            │
│       │                                                  │
│       └──────────────────────────────────────────────────│
│                                                          │
│  Volumes:                                                │
│  - postgres_data (persistent database)                   │
│  - redis_data (persistent cache)                         │
│  - pgadmin_data (persistent pgAdmin config)              │
└─────────────────────────────────────────────────────────┘
```

### Services

- **postgres**: PostgreSQL 14 database
- **redis**: Redis 7 cache and message broker
- **backend**: FastAPI application (Uvicorn server)
- **celery_worker**: Background task processor
- **celery_beat**: Periodic task scheduler
- **pgadmin**: pgAdmin 4 web interface for database management

---

## Prerequisites

### Required Software

- **Docker**: 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: 2.0+ (included with Docker Desktop)
- **Git**: For cloning the repository

### System Requirements

- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 10GB free space (for images + volumes)
- **OS**: Linux, macOS, or Windows (with WSL2)

### Verify Installation

```bash
docker --version
# Docker version 24.0.0 or higher

docker-compose --version
# Docker Compose version v2.20.0 or higher
```

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/meroghar/meroghar.git
cd meroghar
```

### 2. Configure Environment

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit configuration (see Configuration section)
nano backend/.env
```

### 3. Start Services

```bash
# Start all services in detached mode
docker-compose up -d

# Check service status
docker-compose ps
```

### 4. Run Database Migrations

```bash
# Run migrations inside backend container
docker-compose exec backend alembic upgrade head
```

### 5. Verify Deployment

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# View API documentation
open http://localhost:8000/docs

# Access pgAdmin (database management)
open http://localhost:5050
# Login with:
#   Email: admin@meroghar.com
#   Password: meroghar_admin_password
```

**pgAdmin First-Time Setup:**
1. Open http://localhost:5050
2. Login with credentials from .env file
3. Click "Add New Server"
4. In "General" tab: Name = "MeroGhar Dev"
5. In "Connection" tab:
   - Host: `postgres` (container name)
   - Port: `5432`
   - Username: `meroghar`
   - Password: `meroghar_dev_password`
   - Save password: Yes
6. Click "Save"

---

## Configuration

### Environment Variables

The `.env` file configures all services. Copy from `.env.example`:

```bash
cp backend/.env.example backend/.env
```

#### Required Variables

```bash
# Database
DATABASE_URL=postgresql://meroghar:meroghar_dev_password@postgres:5432/meroghar_dev

# pgAdmin (Database Management GUI)
PGADMIN_DEFAULT_EMAIL=admin@meroghar.com
PGADMIN_DEFAULT_PASSWORD=meroghar_admin_password

# Security (MUST change for production)
SECRET_KEY=your-secret-key-min-32-characters
JWT_SECRET_KEY=your-jwt-secret-min-32-characters

# Redis
REDIS_URL=redis://redis:6379/0

# Environment
ENVIRONMENT=production  # or development, staging
DEBUG=False  # True for development only
```

#### Optional Variables

```bash
# Payment Gateways
STRIPE_SECRET_KEY=sk_live_...
RAZORPAY_KEY_ID=rzp_live_...

# SMS Notifications
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...

# Error Monitoring
SENTRY_DSN=https://...@sentry.io/...
```

See `.env.example` for complete list with descriptions.

### Docker Compose Override

For local development customization without modifying `docker-compose.yml`:

```yaml
# docker-compose.override.yml
version: "3.8"

services:
  backend:
    volumes:
      - ./backend/src:/app/src # Live code reloading
    environment:
      - DEBUG=True
    ports:
      - "8001:8000" # Use different port
```

Docker Compose automatically merges `docker-compose.yml` + `docker-compose.override.yml`.

---

## Production Deployment

### 1. Security Hardening

#### Generate Secure Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY (different from SECRET_KEY)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Update Environment

```bash
# Edit .env with secure values
nano backend/.env

# Set production mode
ENVIRONMENT=production
DEBUG=False
```

#### Secure Database Password

```bash
# Generate strong password
openssl rand -base64 32

# Update in both .env and docker-compose.yml
DATABASE_URL=postgresql://meroghar:STRONG_PASSWORD@postgres:5432/meroghar_db
```

### 2. Resource Limits

Add resource constraints to `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 2G
        reservations:
          cpus: "1"
          memory: 1G
    restart: always

  postgres:
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 4G
        reservations:
          cpus: "1"
          memory: 2G
    restart: always
```

### 3. SSL/TLS Termination

Use Nginx reverse proxy for HTTPS:

```yaml
# docker-compose.prod.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
```

**nginx.conf**:

```nginx
server {
    listen 443 ssl;
    server_name api.meroghar.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name api.meroghar.com;
    return 301 https://$server_name$request_uri;
}
```

### 4. Deploy to Production

```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Verify health
curl https://api.meroghar.com/api/v1/health
```

---

## Container Management

### Start/Stop Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d postgres

# Stop all services
docker-compose stop

# Stop specific service
docker-compose stop backend

# Restart service
docker-compose restart backend
```

### Build & Rebuild

```bash
# Build images (first time)
docker-compose build

# Rebuild after code changes
docker-compose build backend

# Rebuild without cache (force fresh build)
docker-compose build --no-cache backend

# Build and start in one command
docker-compose up -d --build
```

### Scale Services

```bash
# Scale celery workers to 3 instances
docker-compose up -d --scale celery_worker=3

# Verify scaling
docker-compose ps
```

### Execute Commands in Containers

```bash
# Run shell in backend container
docker-compose exec backend bash

# Run Python shell
docker-compose exec backend python

# Run database migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "Add new feature"

# Access PostgreSQL
docker-compose exec postgres psql -U meroghar -d meroghar_dev

# Access Redis CLI
docker-compose exec redis redis-cli
```

### Remove Containers & Volumes

```bash
# Stop and remove containers (keeps volumes)
docker-compose down

# Remove containers and volumes (DELETES DATA)
docker-compose down -v

# Remove everything including images
docker-compose down -v --rmi all
```

---

## Monitoring & Logs

### View Logs

```bash
# View all logs
docker-compose logs

# Follow logs (real-time)
docker-compose logs -f

# Logs for specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Logs with timestamps
docker-compose logs -f -t backend
```

### Container Status

```bash
# List running containers
docker-compose ps

# Detailed container info
docker-compose ps -a

# Resource usage (CPU, memory)
docker stats

# Container health status
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Health Checks

```bash
# Check backend health endpoint
curl http://localhost:8000/api/v1/health

# Check PostgreSQL
docker-compose exec postgres pg_isready -U meroghar

# Check Redis
docker-compose exec redis redis-cli ping
```

### Monitoring Tools

#### pgAdmin (Database Management)
**Already included** in docker-compose.yml

Access at: http://localhost:5050

Features:
- Visual query builder
- Schema designer
- Data viewer and editor
- Query history
- Performance monitoring
- Backup/restore tools

Login credentials (from .env):
- Email: admin@meroghar.com
- Password: meroghar_admin_password

#### Flower (Celery Monitoring)

Add to `docker-compose.yml`:

```yaml
services:
  flower:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A src.tasks.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
```

Access at: http://localhost:5555

---

## Troubleshooting

### Issue: Container Fails to Start

**Check logs**:

```bash
docker-compose logs backend
```

**Common causes**:

1. Port already in use → Change port in docker-compose.yml
2. Missing environment variables → Check .env file
3. Database connection failed → Verify postgres is healthy

### Issue: Database Connection Refused

**Solution**:

```bash
# Check postgres health
docker-compose ps postgres

# Restart postgres
docker-compose restart postgres

# Check logs
docker-compose logs postgres

# Verify connection inside backend
docker-compose exec backend python -c "
from src.core.database import engine
print(engine.url)
"
```

### Issue: Migrations Fail

**Solution**:

```bash
# Check current migration version
docker-compose exec backend alembic current

# Check migration history
docker-compose exec backend alembic history

# Rollback one migration
docker-compose exec backend alembic downgrade -1

# Re-run migrations
docker-compose exec backend alembic upgrade head
```

### Issue: Out of Disk Space

**Clean up Docker**:

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a --volumes
```

### Issue: Container Keeps Restarting

**Check exit code**:

```bash
docker-compose ps

# View last logs before crash
docker-compose logs --tail=50 backend
```

**Common exit codes**:

- `Exit 0`: Clean shutdown
- `Exit 1`: Application error (check logs)
- `Exit 137`: Out of memory (increase limits)
- `Exit 139`: Segmentation fault

---

## Best Practices

### 1. Use Health Checks

Always configure healthchecks in `docker-compose.yml`:

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 2. Persist Data with Volumes

Use named volumes for persistent data:

```yaml
volumes:
  postgres_data: # Survives container restarts
  redis_data:
```

### 3. Separate Secrets from Code

- Never commit `.env` file
- Use `.env.example` as template
- For production, use secrets management (Docker Secrets, Vault)

### 4. Resource Limits

Always set limits in production:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 2G
```

### 5. Restart Policies

Configure automatic restarts:

```yaml
services:
  backend:
    restart: unless-stopped # or always, on-failure
```

### 6. Multi-Stage Builds

Use multi-stage Dockerfile to minimize image size:

```dockerfile
FROM python:3.11-slim as builder
# Build dependencies

FROM python:3.11-slim
# Copy only what's needed
```

### 7. Log Rotation

Configure Docker logging driver:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 8. Security Scanning

Scan images for vulnerabilities:

```bash
# Using Docker Scout
docker scout cve meroghar_backend

# Using Trivy
trivy image meroghar_backend
```

### 9. Backup Strategy

Regular backups for production:

```bash
# Database backup
docker-compose exec postgres pg_dump -U meroghar meroghar_db > backup.sql

# Restore
cat backup.sql | docker-compose exec -T postgres psql -U meroghar meroghar_db
```

### 10. Blue-Green Deployment

For zero-downtime updates:

```bash
# Build new version
docker-compose build backend

# Start new containers alongside old
docker-compose up -d --scale backend=2

# Health check new containers
curl http://localhost:8000/api/v1/health

# Stop old containers
docker-compose scale backend=1
```

---

## Advanced Topics

### Container Orchestration

For production at scale, consider:

- **Kubernetes**: Full orchestration with auto-scaling
- **Docker Swarm**: Simpler clustering
- **AWS ECS/Fargate**: Managed container service
- **Google Cloud Run**: Serverless containers

### CI/CD Pipeline

Example GitHub Actions workflow:

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t meroghar/backend:${{ github.sha }} ./backend

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push meroghar/backend:${{ github.sha }}

      - name: Deploy to production
        run: |
          ssh production-server "cd /app && docker-compose pull && docker-compose up -d"
```

---

## Support

### Documentation

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Redis Docker Image](https://hub.docker.com/_/redis)

### Monitoring

- **Logs**: `docker-compose logs -f`
- **Health**: http://localhost:8000/api/v1/health
- **API Docs**: http://localhost:8000/docs
- **Flower (Celery)**: http://localhost:5555

### Get Help

- **GitHub Issues**: https://github.com/meroghar/meroghar/issues
- **Email**: support@meroghar.com
- **Slack**: #meroghar-ops

---

**Last Updated**: 2025-01-26  
**Version**: 1.0  
**Maintained By**: MeroGhar DevOps Team
