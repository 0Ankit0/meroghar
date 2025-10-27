# MeroGhar Backup and Restore Scripts

**Task**: T270 - Create backup and restore scripts  
**Version**: 1.0  
**Date**: October 27, 2025

## Overview

This directory contains automated backup and restore scripts for the MeroGhar Rental Management System. These scripts provide enterprise-grade data protection with the following features:

- **Automated Backups**: PostgreSQL database and Redis data
- **S3 Integration**: Upload backups to AWS S3 for off-site storage
- **Encryption**: Optional GPG encryption for sensitive data
- **Retention Management**: Automatic cleanup of old backups
- **Safety Features**: Pre-restore safety backups and confirmation prompts
- **Notifications**: Slack and email alerts for backup status
- **Verification**: Integrity checks and restore verification

## Files

- **`backup.sh`**: Creates backups of database and Redis
- **`restore.sh`**: Restores from backup files or S3
- **`seed_demo_data.py`**: Seeds database with demo data for testing
- **`README.md`**: This documentation file

---

## Prerequisites

### System Requirements

```bash
# PostgreSQL client tools
sudo apt-get install postgresql-client

# Redis client tools
sudo apt-get install redis-tools

# AWS CLI
sudo apt-get install awscli

# GPG for encryption (optional)
sudo apt-get install gnupg

# Mail utility for email notifications (optional)
sudo apt-get install mailutils
```

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=meroghar
DB_USER=meroghar
PGPASSWORD=your_db_password

# Redis Configuration (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
S3_BACKUP_BUCKET=meroghar-backups
S3_BACKUP_PREFIX=backups/production

# Backup Configuration
BACKUP_DIR=/var/backups/meroghar
RETENTION_DAYS=90

# Encryption (optional)
ENABLE_ENCRYPTION=false
BACKUP_ENCRYPTION_KEY=your_gpg_passphrase

# Notifications (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
BACKUP_EMAIL=admin@example.com
```

---

## Backup Script (`backup.sh`)

### Basic Usage

```bash
# Make script executable
chmod +x backup.sh

# Full backup (database + Redis)
./backup.sh

# Database only
./backup.sh db

# Redis only
./backup.sh redis

# Custom retention (30 days instead of default 90)
./backup.sh full 30
```

### Features

1. **Automated Backups**: Creates compressed SQL dumps and Redis RDB backups
2. **S3 Upload**: Automatically uploads to S3 with STANDARD_IA storage class
3. **Encryption**: Optional GPG symmetric encryption (AES-256)
4. **Verification**: Checks backup integrity after creation
5. **Cleanup**: Removes local and S3 backups older than retention period
6. **Notifications**: Sends Slack/email notifications on success or failure

### Backup Locations

**Local**:

- Database: `$BACKUP_DIR/database/meroghar_db_YYYYMMDD_HHMMSS.sql.gz`
- Redis: `$BACKUP_DIR/redis/meroghar_redis_YYYYMMDD_HHMMSS.rdb.gz`

**S3**:

- Database: `s3://meroghar-backups/backups/production/database/meroghar_db_YYYYMMDD_HHMMSS.sql.gz`
- Redis: `s3://meroghar-backups/backups/production/redis/meroghar_redis_YYYYMMDD_HHMMSS.rdb.gz`

### Cron Setup

Add to crontab for automated daily backups:

```bash
# Edit crontab
crontab -e

# Add backup job (daily at 2 AM)
0 2 * * * /path/to/meroghar/backend/scripts/backup.sh full 90 >> /var/log/meroghar-backup.log 2>&1

# Weekly full backup to separate location (Sunday at 3 AM)
0 3 * * 0 /path/to/meroghar/backend/scripts/backup.sh full 365 >> /var/log/meroghar-backup-weekly.log 2>&1
```

### Backup Strategy Recommendations

**3-2-1 Backup Rule**:

- **3** copies of data: Production + Local backup + S3 backup
- **2** different media: Local disk + Cloud (S3)
- **1** off-site copy: S3 in different region

**Retention Schedule**:

- Daily backups: Keep for 7 days
- Weekly backups: Keep for 30 days
- Monthly backups: Keep for 1 year
- Yearly backups: Keep for 7 years (compliance)

**Example cron setup**:

```bash
# Daily backups (7 days retention)
0 2 * * * /path/to/backup.sh full 7

# Weekly backups (30 days retention) - Sunday at 3 AM
0 3 * * 0 /path/to/backup.sh full 30

# Monthly backups (365 days retention) - 1st of month at 4 AM
0 4 1 * * /path/to/backup.sh full 365
```

### Monitoring Backup Jobs

Check backup logs:

```bash
# View recent backup logs
tail -f /var/log/meroghar-backup.log

# Check backup job status
grep "completed successfully" /var/log/meroghar-backup.log

# List recent S3 backups
aws s3 ls s3://meroghar-backups/backups/production/database/ --recursive | tail -10
```

---

## Restore Script (`restore.sh`)

### ⚠️ WARNING

**The restore script will OVERWRITE all existing data!**

- Always create a safety backup before restoring (done automatically)
- Test restore procedure in a non-production environment first
- Verify backup file integrity before restoring
- Notify users of scheduled downtime

### Basic Usage

```bash
# Make script executable
chmod +x restore.sh

# Restore from local file
./restore.sh --file /path/to/backup.sql.gz

# Restore latest backup from S3
./restore.sh --latest

# Restore backup from specific date
./restore.sh --date 20251027

# Restore from specific S3 path
./restore.sh --s3 s3://meroghar-backups/backups/production/database/meroghar_db_20251027_020000.sql.gz

# Dry run (test without actually restoring)
./restore.sh --latest --dry-run

# Skip confirmation prompt (for automation)
./restore.sh --latest --yes
```

### Restore Process

1. **Download** backup from S3 (if needed)
2. **Decrypt** backup (if encrypted)
3. **Confirm** restore operation with user
4. **Create safety backup** of current database
5. **Terminate** existing database connections
6. **Drop and recreate** database
7. **Restore** data from backup file
8. **Run migrations** to update schema
9. **Verify** restore success
10. **Cleanup** temporary files

### Safety Features

1. **Confirmation Prompt**: Requires user to type "yes" before proceeding
2. **Safety Backup**: Creates backup of current state before restore
3. **Dry Run Mode**: Test restore process without making changes
4. **Verification**: Checks database connection and table count after restore
5. **Rollback**: Safety backup available if restore fails

### Restore Scenarios

#### Disaster Recovery

```bash
# 1. Stop application servers
sudo systemctl stop meroghar-api
sudo systemctl stop meroghar-celery-worker

# 2. Restore latest backup
./restore.sh --latest --yes

# 3. Verify restore
psql -h localhost -U meroghar -d meroghar -c "SELECT COUNT(*) FROM users;"

# 4. Start application servers
sudo systemctl start meroghar-api
sudo systemctl start meroghar-celery-worker
```

#### Point-in-Time Recovery

```bash
# Restore backup from October 27, 2025
./restore.sh --date 20251027

# Or restore specific backup file
./restore.sh --file /backups/meroghar_db_20251027_020000.sql.gz
```

#### Testing Restore Procedure

```bash
# Dry run - test without making changes
./restore.sh --latest --dry-run

# Review what would happen
cat restore.log
```

### Redis Restore

```bash
# Restore Redis from latest backup
./restore.sh --type redis --latest

# Restore Redis from specific file
./restore.sh --type redis --file /path/to/dump.rdb.gz
```

---

## Demo Data Seeding (`seed_demo_data.py`)

### Purpose

Seeds the database with realistic demo data for:

- Testing and development
- Client demonstrations
- Training environments
- QA validation

### Usage

```bash
# Navigate to backend directory
cd backend

# Run seeding script
python -m scripts.seed_demo_data

# Confirm when prompted
# Type 'yes' to proceed
```

### What Gets Created

- **3 Owners**: Rajesh Sharma, Priya Thapa, Anil Kumar
- **2 Intermediaries**: Sanjay Rai, Sunita Gurung
- **12 Tenants**: Various names
- **4 Properties**: Green Valley Apartments, Sunrise Residency, Himalaya Heights, Peace Plaza
- **200+ Payments**: 90% payment rate with various methods
- **24+ Bills**: Electricity and water bills for 3 months
- **30+ Expenses**: Maintenance, repairs, insurance, etc.
- **15+ Documents**: Lease agreements and ID proofs
- **Messages**: SMS reminders
- **Notifications**: Payment confirmations, bill allocations, document warnings

### Demo Credentials

All demo users have the same password: `Demo123!`

**Owners**:

- owner1@meroghar.demo / Demo123!
- owner2@meroghar.demo / Demo123!
- owner3@meroghar.demo / Demo123!

**Intermediaries**:

- intermediary1@meroghar.demo / Demo123!
- intermediary2@meroghar.demo / Demo123!

**Tenants**:

- tenant1@meroghar.demo / Demo123!
- tenant2@meroghar.demo / Demo123!
- ... (tenant3-12@meroghar.demo)

### ⚠️ Important Notes

- **For development/demo environments ONLY**
- **Deletes ALL existing data** before seeding
- Requires confirmation before proceeding
- Creates realistic data with proper relationships

---

## Troubleshooting

### Backup Issues

**Issue**: Backup script fails with "pg_dump: command not found"

```bash
# Install PostgreSQL client tools
sudo apt-get install postgresql-client
```

**Issue**: S3 upload fails with permission denied

```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify S3 bucket exists
aws s3 ls s3://meroghar-backups/

# Check IAM permissions (needs s3:PutObject, s3:GetObject, s3:ListBucket)
```

**Issue**: Backup file is empty or very small

```bash
# Check database connection
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM users;"

# Check pg_dump output
pg_dump --help

# Run backup manually to see errors
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME
```

### Restore Issues

**Issue**: Restore fails with "database is being accessed by other users"

```bash
# Stop application servers
sudo systemctl stop meroghar-api meroghar-celery-worker

# Terminate connections manually
psql -h $DB_HOST -U postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();
"
```

**Issue**: Restore completes but tables are missing

```bash
# Check backup file
gunzip -c backup.sql.gz | head -100

# Verify backup integrity
gzip -t backup.sql.gz

# Try restoring with verbose output
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f backup.sql -v ON_ERROR_STOP=1 -e
```

**Issue**: Redis restore fails

```bash
# Check Redis is stopped
sudo systemctl status redis

# Verify RDB file location
sudo ls -la /var/lib/redis/

# Check Redis permissions
sudo chown redis:redis /var/lib/redis/dump.rdb
```

---

## Best Practices

### Security

1. **Encrypt Backups**: Enable encryption for sensitive data

   ```bash
   export ENABLE_ENCRYPTION=true
   export BACKUP_ENCRYPTION_KEY="your-strong-passphrase"
   ```

2. **Restrict Access**: Limit access to backup files and scripts

   ```bash
   chmod 700 backup.sh restore.sh
   chmod 600 .env
   ```

3. **Secure S3 Buckets**:

   - Enable versioning
   - Enable server-side encryption (SSE-S3 or SSE-KMS)
   - Configure lifecycle policies
   - Restrict public access
   - Enable access logging

4. **Rotate Credentials**: Regularly rotate database passwords and AWS keys

### Monitoring

1. **Test Restores**: Regularly test restore procedure

   ```bash
   # Monthly restore test
   ./restore.sh --latest --dry-run
   ```

2. **Monitor Backup Size**: Alert on significant size changes

   ```bash
   # Check recent backup sizes
   aws s3 ls s3://meroghar-backups/backups/production/database/ --recursive --human-readable
   ```

3. **Verify Backup Integrity**: Regularly verify backups can be restored
   ```bash
   # Test restore in staging environment
   ./restore.sh --latest --yes
   ```

### Documentation

1. **Document Restore Procedure**: Create runbooks for disaster recovery
2. **Update Contact Information**: Keep emergency contact list current
3. **Document RTO/RPO**: Define Recovery Time Objective and Recovery Point Objective
   - RTO: How quickly can we restore? (Target: < 1 hour)
   - RPO: How much data loss is acceptable? (Target: < 24 hours with daily backups)

---

## Compliance and Retention

### Data Retention Policies

- **Transactional Data**: 7 years (tax compliance)
- **User Data**: As per GDPR/local regulations
- **Backup Retention**: Align with data retention policies

### GDPR Compliance

For backups containing EU user data:

1. **Encryption**: Encrypt backups containing PII
2. **Access Control**: Restrict access to backups
3. **Retention**: Delete old backups per retention policy
4. **Right to Erasure**: Document procedure for removing user data from backups

### Audit Trail

Maintain records of:

- Backup creation timestamps
- Backup upload to S3
- Restore operations
- Failed backups/restores
- Access to backup files

---

## Support

For issues or questions:

1. **Check Logs**: Review `/var/log/meroghar-backup.log`
2. **Documentation**: Refer to `backend/docs/deployment.md`
3. **Contact**: DevOps team or admin@meroghar.com

---

## Changelog

### Version 1.0 (2025-10-27)

- Initial release
- PostgreSQL backup and restore
- Redis backup and restore
- S3 integration
- Encryption support
- Notifications (Slack, email)
- Retention management
- Safety features

---

**End of README**
