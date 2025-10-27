# pgAdmin Setup Guide

Complete guide for using pgAdmin to manage the MeroGhar PostgreSQL database.

---

## Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [First-Time Setup](#first-time-setup)
4. [Common Tasks](#common-tasks)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Overview

pgAdmin 4 is a web-based database management tool that provides:
- Visual query builder
- Schema designer
- Data viewer and editor
- Query history
- Performance monitoring
- Backup/restore tools
- User-friendly interface for database operations

### Access Information

- **URL**: http://localhost:5050
- **Email**: admin@meroghar.com
- **Password**: meroghar_admin_password

*Credentials can be customized in `.env` file*

---

## Quick Start

### 1. Start Services

```bash
# Start all services including pgAdmin
docker-compose up -d

# Verify pgAdmin is running
docker-compose ps pgadmin
```

### 2. Access pgAdmin

1. Open browser: http://localhost:5050
2. Login with credentials:
   - Email: `admin@meroghar.com`
   - Password: `meroghar_admin_password`

### 3. Connect to Database (First Time Only)

See [First-Time Setup](#first-time-setup) below.

---

## First-Time Setup

### Step 1: Add Server

1. Login to pgAdmin at http://localhost:5050
2. Right-click **"Servers"** in left sidebar
3. Select **"Create" → "Server"**

### Step 2: General Tab

- **Name**: `MeroGhar Dev`
- **Server Group**: Servers (default)
- **Comments**: Development database for MeroGhar

### Step 3: Connection Tab

Configure connection details:

| Field | Value |
|-------|-------|
| **Host** | `postgres` (Docker container name) |
| **Port** | `5432` |
| **Maintenance database** | `meroghar_dev` |
| **Username** | `meroghar` |
| **Password** | `meroghar_dev_password` |
| **Save password** | ✅ Yes |

### Step 4: Advanced (Optional)

- **DB restriction**: Leave empty
- **SSL Mode**: Prefer (for development)

### Step 5: Save

Click **"Save"** button. The server should appear in the left sidebar.

---

## Common Tasks

### 1. Browse Data

**View Tables:**
1. Expand **"Servers" → "MeroGhar Dev" → "Databases" → "meroghar_dev" → "Schemas" → "public" → "Tables"**
2. Right-click table name
3. Select **"View/Edit Data" → "All Rows"**

**Filter Data:**
1. Click filter icon (funnel) in data view
2. Add filter conditions
3. Click "OK"

**Sort Data:**
- Click column header to sort

### 2. Run SQL Queries

**Query Tool:**
1. Right-click **"meroghar_dev"** database
2. Select **"Query Tool"**
3. Type SQL query
4. Press **F5** or click ▶️ Execute button

**Example Queries:**
```sql
-- View all users
SELECT * FROM users;

-- View tenants with rent > 10000
SELECT * FROM tenants WHERE rent_amount > 10000;

-- Count payments by month
SELECT 
    DATE_TRUNC('month', payment_date) AS month,
    COUNT(*) AS payment_count,
    SUM(amount) AS total_amount
FROM payments
GROUP BY month
ORDER BY month DESC;
```

### 3. Export Data

**Export Table to CSV:**
1. Right-click table → **"View/Edit Data" → "All Rows"**
2. Click download icon (⬇️) in toolbar
3. Select format: **CSV**
4. Click "Download"

**Export Query Results:**
1. Run query in Query Tool
2. Click download icon (⬇️)
3. Select format (CSV, Excel, JSON)
4. Save file

### 4. Import Data

**Import CSV:**
1. Right-click table → **"Import/Export Data"**
2. Toggle **"Import"**
3. Select file
4. Configure column mapping
5. Click "OK"

### 5. Backup Database

**Full Backup:**
1. Right-click **"meroghar_dev"** database
2. Select **"Backup"**
3. Choose filename: `meroghar_backup_2025-01-26.sql`
4. Format: **Plain** (SQL script)
5. Click "Backup"

**Scheduled Backups:**
Use the backend backup script instead:
```bash
cd backend/scripts
./backup.sh
```

### 6. Restore Database

**From Backup File:**
1. Right-click **"meroghar_dev"** database
2. Select **"Restore"**
3. Choose backup file
4. Click "Restore"

### 7. View Database Schema

**ERD (Entity Relationship Diagram):**
1. Right-click **"meroghar_dev"** → **"ERD For Database"**
2. View visual schema diagram
3. Export as image (PNG/SVG)

**Schema Details:**
1. Expand **"Schemas" → "public" → "Tables"**
2. Click table name
3. View **"Columns"**, **"Constraints"**, **"Indexes"** tabs

### 8. Monitor Performance

**Active Queries:**
1. Right-click **"MeroGhar Dev"** server
2. Select **"Dashboard"**
3. View **"Server Activity"** section

**Slow Query Analysis:**
```sql
-- Enable query logging (if needed)
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries > 1 second
SELECT pg_reload_conf();

-- View slow queries (if logging enabled)
SELECT * FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

### 9. Create Database User

```sql
-- Create new user
CREATE USER intermediary WITH PASSWORD 'secure_password';

-- Grant permissions
GRANT CONNECT ON DATABASE meroghar_dev TO intermediary;
GRANT USAGE ON SCHEMA public TO intermediary;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO intermediary;
```

### 10. Check Table Sizes

```sql
-- Table sizes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Best Practices

### 1. Read-Only for Production

**Important**: For production databases, create a read-only connection:

```sql
-- Create read-only user
CREATE USER pgadmin_readonly WITH PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE meroghar_prod TO pgadmin_readonly;
GRANT USAGE ON SCHEMA public TO pgadmin_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO pgadmin_readonly;
```

Then configure pgAdmin connection with this user.

### 2. Use Query Tool for Updates

Never edit data directly in grid view for production. Use Query Tool with transactions:

```sql
BEGIN;
UPDATE tenants SET rent_amount = 15000 WHERE id = 123;
-- Verify changes
SELECT * FROM tenants WHERE id = 123;
-- If correct:
COMMIT;
-- If wrong:
-- ROLLBACK;
```

### 3. Regular Backups

Schedule regular backups:
```bash
# Use backend backup script
cd backend/scripts
./backup.sh

# Or set up cron job
0 2 * * * cd /path/to/backend/scripts && ./backup.sh
```

### 4. Monitor Database Size

```sql
-- Check database size regularly
SELECT 
    pg_size_pretty(pg_database_size('meroghar_dev')) AS size;

-- Check for bloat
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 5. Use Explain for Query Optimization

```sql
-- Before running expensive query, check plan
EXPLAIN ANALYZE
SELECT * FROM payments 
JOIN tenants ON payments.tenant_id = tenants.id
WHERE payment_date > '2025-01-01';
```

---

## Troubleshooting

### Issue: Cannot Connect to pgAdmin

**Check if pgAdmin is running:**
```bash
docker-compose ps pgadmin
```

**Check logs:**
```bash
docker-compose logs pgadmin
```

**Restart pgAdmin:**
```bash
docker-compose restart pgadmin
```

### Issue: Cannot Connect to Database

**Verify PostgreSQL is running:**
```bash
docker-compose ps postgres
```

**Check connection details:**
- Host should be `postgres` (container name), NOT `localhost`
- Port: `5432`
- Username: `meroghar`
- Password: `meroghar_dev_password`

**Test connection from terminal:**
```bash
docker-compose exec postgres psql -U meroghar -d meroghar_dev -c "SELECT version();"
```

### Issue: Login Failed

**Reset pgAdmin password:**

1. Stop pgAdmin:
```bash
docker-compose stop pgadmin
```

2. Remove pgAdmin data:
```bash
docker volume rm meroghar_pgadmin_data
```

3. Start pgAdmin (will recreate with fresh credentials):
```bash
docker-compose up -d pgadmin
```

4. Login with credentials from `.env` file

### Issue: "Server not found"

**Cause**: Server configuration was deleted or corrupted.

**Solution**: Re-add server using [First-Time Setup](#first-time-setup) steps.

### Issue: Slow Queries

**Check active connections:**
```sql
SELECT pid, usename, application_name, state, query
FROM pg_stat_activity
WHERE datname = 'meroghar_dev';
```

**Kill long-running query:**
```sql
-- Get PID from above query
SELECT pg_terminate_backend(12345);  -- Replace with actual PID
```

### Issue: Port 5050 Already in Use

**Option 1: Change pgAdmin Port**

Edit `docker-compose.yml`:
```yaml
pgadmin:
  ports:
    - "5051:80"  # Use port 5051 instead
```

Then access at: http://localhost:5051

**Option 2: Stop Conflicting Service**
```bash
# Find what's using port 5050
netstat -ano | findstr :5050  # Windows
lsof -i :5050                 # macOS/Linux

# Kill the process
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # macOS/Linux
```

---

## Security Notes

### Production Deployment

**1. Change Default Credentials**

Never use default credentials in production! Update `.env`:
```bash
PGADMIN_DEFAULT_EMAIL=secure_admin@yourcompany.com
PGADMIN_DEFAULT_PASSWORD=very_secure_random_password_here
```

**2. Enable HTTPS**

Configure Nginx reverse proxy with SSL:
```nginx
server {
    listen 443 ssl;
    server_name pgadmin.yourcompany.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**3. Use VPN or IP Whitelisting**

Restrict access to pgAdmin:
- Deploy behind VPN
- Use firewall rules to whitelist IPs
- Use authentication proxy

**4. Regular Security Updates**

Update pgAdmin regularly:
```bash
docker-compose pull pgadmin
docker-compose up -d pgadmin
```

---

## Additional Resources

### Official Documentation
- **pgAdmin Docs**: https://www.pgadmin.org/docs/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

### Keyboard Shortcuts
- **Execute Query**: F5
- **Open Query Tool**: Ctrl+Shift+Q
- **Save**: Ctrl+S
- **Find**: Ctrl+F
- **Comment Line**: Ctrl+/

### Alternatives

If pgAdmin doesn't meet your needs:
- **TablePlus**: https://tableplus.com/ (macOS/Windows/Linux)
- **DBeaver**: https://dbeaver.io/ (cross-platform, free)
- **DataGrip**: https://www.jetbrains.com/datagrip/ (JetBrains, paid)
- **psql**: PostgreSQL command-line interface (included)

---

## Support

### Internal Support
- **Documentation**: `/backend/docs/`
- **GitHub Issues**: https://github.com/meroghar/meroghar/issues
- **Team Slack**: #meroghar-database channel

### External Resources
- **pgAdmin Forum**: https://www.postgresql.org/list/pgadmin-support/
- **Stack Overflow**: Tag `pgadmin` + `postgresql`

---

**Last Updated**: 2025-01-26  
**Version**: 1.0  
**Maintained By**: MeroGhar DevOps Team
