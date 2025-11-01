# Multi-stage Dockerfile for MeroGhar Backend
# Optimized for production with minimal image size

# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Set non-interactive frontend for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    libmagic-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libtiff-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Set non-interactive frontend for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local /usr/local

# Make sure scripts are usable (they should be in /usr/local/bin now)
# No need to set PATH as /usr/local/bin is usually in PATH by default

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create non-root user for security
RUN useradd -m -u 1000 meroghar && \
    chown -R meroghar:meroghar /app

# Switch to non-root user
USER meroghar

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health').read()"

# Default command (can be overridden in docker-compose.yml)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
