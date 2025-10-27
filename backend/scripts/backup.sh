#!/bin/bash
#
# Database and File Backup Script for MeroGhar Rental Management System
# Task: T270 - Create backup and restore scripts
#
# This script creates automated backups of:
# 1. PostgreSQL database
# 2. Redis data (if persistence enabled)
# 3. S3 file metadata (optional)
#
# Usage:
#   ./backup.sh                    # Create backup with default settings
#   ./backup.sh --type full        # Full backup (database + redis + files)
#   ./backup.sh --type db          # Database only
#   ./backup.sh --retention 30     # Keep backups for 30 days
#
# Environment Variables Required:
#   DATABASE_URL            # PostgreSQL connection string
#   REDIS_URL              # Redis connection string (optional)
#   AWS_ACCESS_KEY_ID      # AWS credentials for S3 upload
#   AWS_SECRET_ACCESS_KEY  # AWS secret key
#   S3_BACKUP_BUCKET       # S3 bucket for backup storage
#   BACKUP_ENCRYPTION_KEY  # Optional: GPG key for encryption
#
# Cron Setup (Daily at 2 AM):
#   0 2 * * * /path/to/backup.sh >> /var/log/meroghar-backup.log 2>&1

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Catch errors in pipes

# ========================================
# CONFIGURATION
# ========================================

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Backup configuration
BACKUP_TYPE="${1:-full}"  # full, db, redis, files
RETENTION_DAYS="${2:-90}"  # Keep backups for 90 days
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
LOG_FILE="${LOG_FILE:-$BACKUP_DIR/backup.log}"

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-meroghar}"
DB_USER="${DB_USER:-meroghar}"
DB_PASSWORD="${PGPASSWORD:-}"

# Redis configuration
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_DB="${REDIS_DB:-0}"

# S3 configuration
S3_BACKUP_BUCKET="${S3_BACKUP_BUCKET:-meroghar-backups}"
S3_BACKUP_PREFIX="${S3_BACKUP_PREFIX:-backups/production}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Encryption configuration
ENABLE_ENCRYPTION="${ENABLE_ENCRYPTION:-false}"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"

# Notification configuration
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
EMAIL_RECIPIENT="${BACKUP_EMAIL:-}"

# ========================================
# LOGGING FUNCTIONS
# ========================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

# ========================================
# NOTIFICATION FUNCTIONS
# ========================================

send_slack_notification() {
    local message="$1"
    local status="$2"  # success or failure
    
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        local color="good"
        if [ "$status" = "failure" ]; then
            color="danger"
        fi
        
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"MeroGhar Backup Notification\",
                    \"text\": \"$message\",
                    \"footer\": \"Backup Script\",
                    \"ts\": $(date +%s)
                }]
            }" 2>/dev/null || true
    fi
}

send_email_notification() {
    local subject="$1"
    local body="$2"
    
    if [ -n "$EMAIL_RECIPIENT" ]; then
        echo "$body" | mail -s "$subject" "$EMAIL_RECIPIENT" 2>/dev/null || true
    fi
}

# ========================================
# SETUP FUNCTIONS
# ========================================

setup_backup_directory() {
    log "Setting up backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$BACKUP_DIR/database"
    mkdir -p "$BACKUP_DIR/redis"
    mkdir -p "$BACKUP_DIR/logs"
}

check_dependencies() {
    log "Checking required dependencies..."
    
    local missing_deps=()
    
    # Check pg_dump
    if ! command -v pg_dump &> /dev/null; then
        missing_deps+=("pg_dump (PostgreSQL client)")
    fi
    
    # Check redis-cli
    if ! command -v redis-cli &> /dev/null && [ "$BACKUP_TYPE" != "db" ]; then
        missing_deps+=("redis-cli (Redis client)")
    fi
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        missing_deps+=("aws (AWS CLI)")
    fi
    
    # Check GPG for encryption
    if [ "$ENABLE_ENCRYPTION" = "true" ] && ! command -v gpg &> /dev/null; then
        missing_deps+=("gpg (GnuPG)")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        error "Missing required dependencies:"
        for dep in "${missing_deps[@]}"; do
            error "  - $dep"
        done
        exit 1
    fi
    
    log "All dependencies satisfied"
}

# ========================================
# BACKUP FUNCTIONS
# ========================================

backup_database() {
    log "Starting PostgreSQL database backup..."
    
    local backup_file="$BACKUP_DIR/database/meroghar_db_${TIMESTAMP}.sql"
    local compressed_file="${backup_file}.gz"
    
    # Set PostgreSQL password
    export PGPASSWORD="$DB_PASSWORD"
    
    # Create database dump
    log "Creating database dump: $backup_file"
    pg_dump \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="$DB_NAME" \
        --format=plain \
        --no-owner \
        --no-acl \
        --verbose \
        --file="$backup_file" 2>&1 | tee -a "$LOG_FILE"
    
    if [ $? -ne 0 ]; then
        error "Database backup failed"
        return 1
    fi
    
    # Compress backup
    log "Compressing backup..."
    gzip -9 "$backup_file"
    
    # Verify compressed file
    if [ ! -f "$compressed_file" ]; then
        error "Compressed backup file not found"
        return 1
    fi
    
    local file_size=$(du -h "$compressed_file" | cut -f1)
    log "Database backup completed: $compressed_file ($file_size)"
    
    # Encrypt if enabled
    if [ "$ENABLE_ENCRYPTION" = "true" ]; then
        encrypt_backup "$compressed_file"
    fi
    
    # Upload to S3
    upload_to_s3 "$compressed_file" "database"
    
    echo "$compressed_file"
}

backup_redis() {
    log "Starting Redis backup..."
    
    local backup_file="$BACKUP_DIR/redis/meroghar_redis_${TIMESTAMP}.rdb"
    
    # Trigger Redis BGSAVE
    log "Triggering Redis background save..."
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" BGSAVE
    
    # Wait for save to complete
    log "Waiting for Redis save to complete..."
    local max_wait=60
    local waited=0
    while [ $waited -lt $max_wait ]; do
        local last_save=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" LASTSAVE)
        sleep 1
        local current_save=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" LASTSAVE)
        
        if [ "$current_save" -gt "$last_save" ]; then
            break
        fi
        
        waited=$((waited + 1))
    done
    
    if [ $waited -ge $max_wait ]; then
        error "Redis save timeout"
        return 1
    fi
    
    # Copy RDB file
    local redis_rdb_path="/var/lib/redis/dump.rdb"
    if [ -f "$redis_rdb_path" ]; then
        cp "$redis_rdb_path" "$backup_file"
        gzip -9 "$backup_file"
        
        local compressed_file="${backup_file}.gz"
        local file_size=$(du -h "$compressed_file" | cut -f1)
        log "Redis backup completed: $compressed_file ($file_size)"
        
        # Encrypt if enabled
        if [ "$ENABLE_ENCRYPTION" = "true" ]; then
            encrypt_backup "$compressed_file"
        fi
        
        # Upload to S3
        upload_to_s3 "$compressed_file" "redis"
        
        echo "$compressed_file"
    else
        error "Redis RDB file not found at $redis_rdb_path"
        return 1
    fi
}

encrypt_backup() {
    local file="$1"
    log "Encrypting backup: $file"
    
    if [ -z "$ENCRYPTION_KEY" ]; then
        error "Encryption key not provided"
        return 1
    fi
    
    # Encrypt using GPG symmetric encryption
    gpg --symmetric \
        --cipher-algo AES256 \
        --batch \
        --yes \
        --passphrase "$ENCRYPTION_KEY" \
        --output "${file}.gpg" \
        "$file"
    
    if [ $? -eq 0 ]; then
        log "Encryption successful: ${file}.gpg"
        rm "$file"  # Remove unencrypted file
    else
        error "Encryption failed"
        return 1
    fi
}

upload_to_s3() {
    local file="$1"
    local backup_type="$2"
    
    # Add .gpg extension if encrypted
    if [ "$ENABLE_ENCRYPTION" = "true" ]; then
        file="${file}.gpg"
    fi
    
    log "Uploading to S3: $file"
    
    local s3_path="s3://${S3_BACKUP_BUCKET}/${S3_BACKUP_PREFIX}/${backup_type}/$(basename "$file")"
    
    aws s3 cp "$file" "$s3_path" \
        --region "$AWS_REGION" \
        --storage-class STANDARD_IA \
        --metadata "backup-date=${TIMESTAMP},backup-type=${backup_type},retention-days=${RETENTION_DAYS}" \
        2>&1 | tee -a "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        log "Upload successful: $s3_path"
    else
        error "Upload failed: $s3_path"
        return 1
    fi
}

# ========================================
# CLEANUP FUNCTIONS
# ========================================

cleanup_old_backups() {
    log "Cleaning up local backups older than $RETENTION_DAYS days..."
    
    # Remove old database backups
    find "$BACKUP_DIR/database" -type f -mtime +$RETENTION_DAYS -exec rm {} \;
    
    # Remove old Redis backups
    find "$BACKUP_DIR/redis" -type f -mtime +$RETENTION_DAYS -exec rm {} \;
    
    log "Local cleanup completed"
}

cleanup_s3_backups() {
    log "Cleaning up S3 backups older than $RETENTION_DAYS days..."
    
    # Calculate cutoff date
    local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y%m%d)
    
    # List and delete old backups
    aws s3 ls "s3://${S3_BACKUP_BUCKET}/${S3_BACKUP_PREFIX}/" --recursive | \
    while read -r line; do
        local file_date=$(echo "$line" | awk '{print $1}' | tr -d '-')
        local file_path=$(echo "$line" | awk '{print $4}')
        
        if [ "$file_date" -lt "$cutoff_date" ]; then
            log "Deleting old S3 backup: $file_path"
            aws s3 rm "s3://${S3_BACKUP_BUCKET}/${file_path}"
        fi
    done
    
    log "S3 cleanup completed"
}

# ========================================
# VERIFICATION FUNCTIONS
# ========================================

verify_backup() {
    local backup_file="$1"
    
    log "Verifying backup integrity: $backup_file"
    
    # Check if file exists
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        return 1
    fi
    
    # Check if file is not empty
    if [ ! -s "$backup_file" ]; then
        error "Backup file is empty: $backup_file"
        return 1
    fi
    
    # Verify gzip integrity
    if [[ "$backup_file" == *.gz ]]; then
        if ! gzip -t "$backup_file" 2>/dev/null; then
            error "Backup file is corrupted: $backup_file"
            return 1
        fi
    fi
    
    log "Backup verification passed"
    return 0
}

# ========================================
# MAIN EXECUTION
# ========================================

main() {
    log "========================================="
    log "Starting backup process"
    log "Backup type: $BACKUP_TYPE"
    log "Retention days: $RETENTION_DAYS"
    log "========================================="
    
    # Setup
    setup_backup_directory
    check_dependencies
    
    # Track success
    local success=true
    local backed_up_files=()
    
    # Perform backups based on type
    case "$BACKUP_TYPE" in
        full)
            log "Performing full backup (database + redis)..."
            db_file=$(backup_database) || success=false
            redis_file=$(backup_redis) || success=false
            backed_up_files+=("$db_file" "$redis_file")
            ;;
        db|database)
            log "Performing database backup only..."
            db_file=$(backup_database) || success=false
            backed_up_files+=("$db_file")
            ;;
        redis)
            log "Performing Redis backup only..."
            redis_file=$(backup_redis) || success=false
            backed_up_files+=("$redis_file")
            ;;
        *)
            error "Invalid backup type: $BACKUP_TYPE"
            error "Valid types: full, db, redis"
            exit 1
            ;;
    esac
    
    # Verify backups
    for file in "${backed_up_files[@]}"; do
        verify_backup "$file" || success=false
    done
    
    # Cleanup old backups
    cleanup_old_backups
    cleanup_s3_backups
    
    # Send notifications
    if [ "$success" = true ]; then
        local message="Backup completed successfully\nType: $BACKUP_TYPE\nTimestamp: $TIMESTAMP\nFiles: ${backed_up_files[*]}"
        log "Backup process completed successfully"
        send_slack_notification "$message" "success"
        send_email_notification "MeroGhar Backup Success" "$message"
    else
        local message="Backup failed!\nType: $BACKUP_TYPE\nTimestamp: $TIMESTAMP\nCheck logs: $LOG_FILE"
        error "Backup process failed"
        send_slack_notification "$message" "failure"
        send_email_notification "MeroGhar Backup FAILED" "$message"
        exit 1
    fi
    
    log "========================================="
    log "Backup process finished"
    log "========================================="
}

# Run main function
main "$@"
