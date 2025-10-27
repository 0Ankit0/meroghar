#!/bin/bash
#
# Database and File Restore Script for MeroGhar Rental Management System
# Task: T270 - Create backup and restore scripts
#
# This script restores backups created by backup.sh:
# 1. PostgreSQL database restoration
# 2. Redis data restoration
#
# ⚠️ WARNING: This script will OVERWRITE existing data!
# Always create a backup before restoring.
#
# Usage:
#   ./restore.sh --file /path/to/backup.sql.gz
#   ./restore.sh --s3 s3://bucket/path/to/backup.sql.gz
#   ./restore.sh --latest                    # Restore latest backup from S3
#   ./restore.sh --date 20251027            # Restore backup from specific date
#   ./restore.sh --type redis --file /path/to/dump.rdb.gz
#
# Environment Variables Required:
#   DATABASE_URL            # PostgreSQL connection string
#   REDIS_URL              # Redis connection string (optional)
#   AWS_ACCESS_KEY_ID      # AWS credentials for S3 download
#   AWS_SECRET_ACCESS_KEY  # AWS secret key
#   S3_BACKUP_BUCKET       # S3 bucket where backups are stored
#   BACKUP_ENCRYPTION_KEY  # If backups are encrypted
#
# Safety Features:
#   - Requires explicit confirmation before restore
#   - Creates safety backup before restore
#   - Validates backup file before restore
#   - Supports dry-run mode for testing

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

# Restore configuration
RESTORE_TYPE="db"  # db or redis
RESTORE_FILE=""
RESTORE_FROM_S3=""
RESTORE_LATEST=false
RESTORE_DATE=""
DRY_RUN=false
SKIP_CONFIRMATION=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --file)
            RESTORE_FILE="$2"
            shift 2
            ;;
        --s3)
            RESTORE_FROM_S3="$2"
            shift 2
            ;;
        --latest)
            RESTORE_LATEST=true
            shift
            ;;
        --date)
            RESTORE_DATE="$2"
            shift 2
            ;;
        --type)
            RESTORE_TYPE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --yes|-y)
            SKIP_CONFIRMATION=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--file FILE | --s3 S3_PATH | --latest | --date DATE] [--type db|redis] [--dry-run] [--yes]"
            exit 1
            ;;
    esac
done

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-meroghar}"
DB_USER="${DB_USER:-meroghar}"
DB_PASSWORD="${PGPASSWORD:-}"

# Redis configuration
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

# S3 configuration
S3_BACKUP_BUCKET="${S3_BACKUP_BUCKET:-meroghar-backups}"
S3_BACKUP_PREFIX="${S3_BACKUP_PREFIX:-backups/production}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Working directory
TEMP_DIR="/tmp/meroghar_restore_$$"
LOG_FILE="${LOG_FILE:-$PROJECT_ROOT/restore.log}"

# Encryption
ENABLE_ENCRYPTION="${ENABLE_ENCRYPTION:-false}"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"

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
# SAFETY FUNCTIONS
# ========================================

confirm_restore() {
    if [ "$SKIP_CONFIRMATION" = true ]; then
        log "Skipping confirmation (--yes flag)"
        return 0
    fi
    
    echo ""
    echo "⚠️  WARNING: This will OVERWRITE all existing data!"
    echo ""
    echo "Restore details:"
    echo "  Type: $RESTORE_TYPE"
    echo "  Source: ${RESTORE_FILE:-${RESTORE_FROM_S3:-latest/date}}"
    echo "  Target database: $DB_NAME on $DB_HOST"
    echo ""
    echo "A safety backup will be created before restore."
    echo ""
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirmation
    
    if [ "$confirmation" != "yes" ]; then
        log "Restore cancelled by user"
        exit 0
    fi
    
    log "User confirmed restore operation"
}

create_safety_backup() {
    log "Creating safety backup before restore..."
    
    local safety_file="/tmp/meroghar_safety_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
    
    export PGPASSWORD="$DB_PASSWORD"
    pg_dump \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="$DB_NAME" \
        --format=plain \
        --no-owner \
        --no-acl \
        | gzip -9 > "$safety_file"
    
    if [ $? -eq 0 ]; then
        log "Safety backup created: $safety_file"
        echo "Safety backup: $safety_file"
    else
        error "Failed to create safety backup"
        return 1
    fi
}

# ========================================
# DOWNLOAD FUNCTIONS
# ========================================

download_from_s3() {
    local s3_path="$1"
    local local_file="$2"
    
    log "Downloading from S3: $s3_path"
    
    aws s3 cp "$s3_path" "$local_file" \
        --region "$AWS_REGION" \
        2>&1 | tee -a "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        log "Download successful: $local_file"
        echo "$local_file"
    else
        error "Download failed: $s3_path"
        return 1
    fi
}

find_latest_backup() {
    local backup_type="$1"
    
    log "Finding latest backup in S3..."
    
    local latest_file=$(aws s3 ls "s3://${S3_BACKUP_BUCKET}/${S3_BACKUP_PREFIX}/${backup_type}/" \
        | sort -r \
        | head -n 1 \
        | awk '{print $4}')
    
    if [ -z "$latest_file" ]; then
        error "No backups found in S3"
        return 1
    fi
    
    local s3_path="s3://${S3_BACKUP_BUCKET}/${S3_BACKUP_PREFIX}/${backup_type}/${latest_file}"
    log "Latest backup: $s3_path"
    echo "$s3_path"
}

find_backup_by_date() {
    local backup_type="$1"
    local date="$2"
    
    log "Finding backup from date: $date"
    
    local backup_file=$(aws s3 ls "s3://${S3_BACKUP_BUCKET}/${S3_BACKUP_PREFIX}/${backup_type}/" \
        | grep "$date" \
        | sort -r \
        | head -n 1 \
        | awk '{print $4}')
    
    if [ -z "$backup_file" ]; then
        error "No backup found for date: $date"
        return 1
    fi
    
    local s3_path="s3://${S3_BACKUP_BUCKET}/${S3_BACKUP_PREFIX}/${backup_type}/${backup_file}"
    log "Found backup: $s3_path"
    echo "$s3_path"
}

# ========================================
# DECRYPTION FUNCTIONS
# ========================================

decrypt_backup() {
    local encrypted_file="$1"
    local decrypted_file="${encrypted_file%.gpg}"
    
    log "Decrypting backup: $encrypted_file"
    
    if [ -z "$ENCRYPTION_KEY" ]; then
        error "Encryption key not provided (BACKUP_ENCRYPTION_KEY)"
        return 1
    fi
    
    gpg --decrypt \
        --batch \
        --yes \
        --passphrase "$ENCRYPTION_KEY" \
        --output "$decrypted_file" \
        "$encrypted_file"
    
    if [ $? -eq 0 ]; then
        log "Decryption successful: $decrypted_file"
        rm "$encrypted_file"  # Remove encrypted file
        echo "$decrypted_file"
    else
        error "Decryption failed"
        return 1
    fi
}

# ========================================
# RESTORE FUNCTIONS
# ========================================

restore_database() {
    local backup_file="$1"
    
    log "Starting database restore from: $backup_file"
    
    # Decompress if needed
    if [[ "$backup_file" == *.gz ]]; then
        log "Decompressing backup..."
        local sql_file="${backup_file%.gz}"
        gunzip -c "$backup_file" > "$sql_file"
        backup_file="$sql_file"
    fi
    
    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would restore database from $backup_file"
        log "DRY RUN: Would run: psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < $backup_file"
        return 0
    fi
    
    # Create safety backup
    create_safety_backup
    
    # Drop existing connections
    log "Terminating existing database connections..."
    export PGPASSWORD="$DB_PASSWORD"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<-EOF
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();
EOF
    
    # Drop and recreate database
    log "Dropping and recreating database..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<-EOF
        DROP DATABASE IF EXISTS $DB_NAME;
        CREATE DATABASE $DB_NAME;
EOF
    
    # Restore database
    log "Restoring database..."
    psql \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="$DB_NAME" \
        --single-transaction \
        --set ON_ERROR_STOP=on \
        < "$backup_file" 2>&1 | tee -a "$LOG_FILE"
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log "Database restore completed successfully"
    else
        error "Database restore failed"
        return 1
    fi
    
    # Run migrations to ensure schema is up to date
    log "Running database migrations..."
    cd "$PROJECT_ROOT/backend"
    alembic upgrade head 2>&1 | tee -a "$LOG_FILE"
    
    log "Database restore complete"
}

restore_redis() {
    local backup_file="$1"
    
    log "Starting Redis restore from: $backup_file"
    
    # Decompress if needed
    if [[ "$backup_file" == *.gz ]]; then
        log "Decompressing backup..."
        local rdb_file="${backup_file%.gz}"
        gunzip -c "$backup_file" > "$rdb_file"
        backup_file="$rdb_file"
    fi
    
    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would restore Redis from $backup_file"
        return 0
    fi
    
    # Stop Redis
    log "Stopping Redis..."
    sudo systemctl stop redis || redis-cli shutdown
    
    # Copy RDB file
    log "Copying RDB file..."
    local redis_data_dir="/var/lib/redis"
    sudo cp "$backup_file" "$redis_data_dir/dump.rdb"
    sudo chown redis:redis "$redis_data_dir/dump.rdb"
    
    # Start Redis
    log "Starting Redis..."
    sudo systemctl start redis
    
    # Verify Redis is running
    sleep 2
    if redis-cli ping | grep -q "PONG"; then
        log "Redis restore completed successfully"
    else
        error "Redis failed to start after restore"
        return 1
    fi
}

# ========================================
# VERIFICATION FUNCTIONS
# ========================================

verify_restore() {
    local restore_type="$1"
    
    log "Verifying restore..."
    
    case "$restore_type" in
        db|database)
            # Check database connection
            export PGPASSWORD="$DB_PASSWORD"
            if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &>/dev/null; then
                log "Database connection: OK"
            else
                error "Database connection: FAILED"
                return 1
            fi
            
            # Check table count
            local table_count=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
            log "Tables restored: $table_count"
            
            if [ "$table_count" -lt 10 ]; then
                error "Too few tables restored (expected 15+, got $table_count)"
                return 1
            fi
            ;;
            
        redis)
            # Check Redis connection
            if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping | grep -q "PONG"; then
                log "Redis connection: OK"
            else
                error "Redis connection: FAILED"
                return 1
            fi
            
            # Check key count
            local key_count=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" DBSIZE | awk '{print $2}')
            log "Redis keys restored: $key_count"
            ;;
    esac
    
    log "Verification passed"
    return 0
}

# ========================================
# MAIN EXECUTION
# ========================================

main() {
    log "========================================="
    log "Starting restore process"
    log "Restore type: $RESTORE_TYPE"
    log "========================================="
    
    # Setup
    mkdir -p "$TEMP_DIR"
    cd "$TEMP_DIR"
    
    # Determine backup file
    local backup_file=""
    
    if [ -n "$RESTORE_FILE" ]; then
        # Use specified file
        backup_file="$RESTORE_FILE"
        log "Using backup file: $backup_file"
        
    elif [ -n "$RESTORE_FROM_S3" ]; then
        # Download from S3
        backup_file=$(download_from_s3 "$RESTORE_FROM_S3" "$TEMP_DIR/$(basename "$RESTORE_FROM_S3")")
        
    elif [ "$RESTORE_LATEST" = true ]; then
        # Find and download latest backup
        local s3_path=$(find_latest_backup "$RESTORE_TYPE")
        backup_file=$(download_from_s3 "$s3_path" "$TEMP_DIR/$(basename "$s3_path")")
        
    elif [ -n "$RESTORE_DATE" ]; then
        # Find and download backup by date
        local s3_path=$(find_backup_by_date "$RESTORE_TYPE" "$RESTORE_DATE")
        backup_file=$(download_from_s3 "$s3_path" "$TEMP_DIR/$(basename "$s3_path")")
        
    else
        error "No backup source specified"
        error "Use --file, --s3, --latest, or --date"
        exit 1
    fi
    
    # Decrypt if needed
    if [[ "$backup_file" == *.gpg ]]; then
        backup_file=$(decrypt_backup "$backup_file")
    fi
    
    # Verify backup file exists
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi
    
    # Confirm restore
    confirm_restore
    
    # Perform restore
    local success=true
    case "$RESTORE_TYPE" in
        db|database)
            restore_database "$backup_file" || success=false
            verify_restore "db" || success=false
            ;;
        redis)
            restore_redis "$backup_file" || success=false
            verify_restore "redis" || success=false
            ;;
        *)
            error "Invalid restore type: $RESTORE_TYPE"
            exit 1
            ;;
    esac
    
    # Cleanup
    log "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
    
    # Final status
    if [ "$success" = true ]; then
        log "Restore completed successfully"
        log "========================================="
        exit 0
    else
        error "Restore failed"
        error "Safety backup available in /tmp/meroghar_safety_backup_*.sql.gz"
        log "========================================="
        exit 1
    fi
}

# Run main function
main
