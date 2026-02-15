# Production Upgrade Guide - Organization Migration

**Date:** November 21, 2025
**Migration:** `cb97872b8def` - Remove organizations table
**Target:** Production customers running older database versions

---

## ⚠️ CRITICAL: What Changed

The `organizations` table is being removed in favor of the `setting` table for storing organization information. The migration **automatically handles data migration**, but you should verify the process.

### What the Migration Does:

1. **Checks** if `ORG_NAME` exists in Settings table
2. **If missing**, attempts to migrate from `organizations` table:
   - Migrates `organizations.name` → Settings `ORG_NAME`
   - Migrates `organizations.mail_username` → Settings `MAIL_USERNAME` (if not set)
3. **If no organization data**, creates default settings:
   - `ORG_NAME = "Fondation LHGI"`
   - `ORG_ADDRESS = "821 rue des Sables, Rimouski, QC G5L 6Y7"`
4. **Then** drops `organizations` table and foreign keys

---

## Pre-Upgrade Checklist (MANDATORY)

### 1. Backup Database

```bash
# Stop the application
docker stop minipass_customer_name

# Backup database
cp /path/to/customer/instance/minipass.db \
   /path/to/backups/minipass_backup_$(date +%Y%m%d_%H%M%S).db

# Verify backup
ls -lh /path/to/backups/
```

### 2. Check Current Organization Settings

```bash
# Check if organization exists
sqlite3 /path/to/customer/instance/minipass.db \
  "SELECT id, name, mail_username FROM organizations;"

# Check if ORG_NAME already in settings
sqlite3 /path/to/customer/instance/minipass.db \
  "SELECT key, value FROM setting WHERE key IN ('ORG_NAME', 'ORG_ADDRESS', 'MAIL_USERNAME');"
```

**Expected Results:**
- **If organization exists:** You'll see organization name and email
- **If ORG_NAME exists:** Migration will skip data migration
- **If both missing:** Migration will create defaults

### 3. Document Current Settings (IMPORTANT!)

Save the output from step 2 in case you need to manually set organization name.

---

## Upgrade Procedure

### Option A: Docker Deployment (Recommended)

```bash
# 1. Pull latest image
docker pull minipass:latest

# 2. Stop current container
docker stop minipass_customer_name

# 3. Run database migrations
docker run --rm \
  -v /path/to/customer/instance:/app/instance \
  minipass:latest \
  flask db upgrade

# Expected output:
# 🔍 ORG_NAME not found in settings, checking organizations table...
# ✅ Found organization: Customer Name
#    Migrating to Settings table...
#    ✅ Created ORG_NAME = 'Customer Name'
# 🎯 Data migration complete - proceeding with table removal...
# ✅ Organizations table dropped
# ===================================================
# ✅ MIGRATION COMPLETE
# ===================================================

# 4. Restart with new image
docker start minipass_customer_name
```

### Option B: Manual Deployment

```bash
# 1. Navigate to app directory
cd /path/to/minipass/app

# 2. Activate virtual environment
source venv/bin/activate

# 3. Pull latest code
git pull origin main

# 4. Run migrations
flask db upgrade

# 5. Restart Flask
sudo systemctl restart minipass
```

---

## Post-Upgrade Verification

### 1. Verify Settings Created

```bash
sqlite3 /path/to/customer/instance/minipass.db \
  "SELECT key, value FROM setting WHERE key IN ('ORG_NAME', 'ORG_ADDRESS');"
```

**Expected:**
```
ORG_NAME|Customer Organization Name
ORG_ADDRESS|821 rue des Sables, Rimouski, QC G5L 6Y7
```

### 2. Verify Organizations Table Removed

```bash
sqlite3 /path/to/customer/instance/minipass.db \
  "SELECT name FROM sqlite_master WHERE type='table' AND name='organizations';"
```

**Expected:** Empty (no results)

### 3. Verify Application Works

```bash
# Check logs for errors
docker logs minipass_customer_name --tail 50

# Or for manual deployment:
tail -f /var/log/minipass/flask.log

# Test critical endpoints
curl -I http://localhost:5000/login
# Should return: HTTP/1.1 200 OK
```

### 4. Test Email Functionality

1. Log in to application
2. Create a test passport
3. Verify email is sent with correct organization name
4. Check footer shows correct organization name and address

---

## Troubleshooting

### Issue: Migration Shows "No organization data found"

**Cause:** Organizations table was empty
**Impact:** Default settings created
**Action:** Update settings manually

```bash
# Update organization name
sqlite3 /path/to/customer/instance/minipass.db \
  "UPDATE setting SET value = 'Actual Customer Name' WHERE key = 'ORG_NAME';"

# Update organization address
sqlite3 /path/to/customer/instance/minipass.db \
  "UPDATE setting SET value = 'Customer Address Here' WHERE key = 'ORG_ADDRESS';"

# Restart application
docker restart minipass_customer_name
```

### Issue: "AttributeError: 'Activity' object has no attribute 'organization'"

**Cause:** Old code running with new database
**Action:** Ensure application restarted with latest code

```bash
# Pull latest code
git pull origin main

# Restart
docker restart minipass_customer_name
# OR
sudo systemctl restart minipass
```

### Issue: Migration Failed Midway

**Cause:** Database locked or permissions issue
**Action:** Restore backup and retry

```bash
# Stop application
docker stop minipass_customer_name

# Restore backup
cp /path/to/backups/minipass_backup_YYYYMMDD_HHMMSS.db \
   /path/to/customer/instance/minipass.db

# Check permissions
chown www-data:www-data /path/to/customer/instance/minipass.db
chmod 664 /path/to/customer/instance/minipass.db

# Retry migration
docker run --rm \
  -v /path/to/customer/instance:/app/instance \
  minipass:latest \
  flask db upgrade

# Restart
docker start minipass_customer_name
```

---

## Rollback Procedure (Emergency Only)

**WARNING:** Rollback is NOT supported by the migration itself. You must restore from backup.

```bash
# 1. Stop application
docker stop minipass_customer_name

# 2. Restore backup database
cp /path/to/backups/minipass_backup_YYYYMMDD_HHMMSS.db \
   /path/to/customer/instance/minipass.db

# 3. Deploy previous application version
docker run -d \
  --name minipass_customer_name \
  -v /path/to/customer/instance:/app/instance \
  minipass:previous_tag

# 4. Verify old version works
curl -I http://localhost:5000/login
```

**IMPORTANT:** After rollback, do NOT attempt to upgrade again until you've identified and fixed the issue.

---

## Customer Communication Template

```
Subject: Minipass System Upgrade - November 2025

Dear [Customer Name],

We're upgrading your Minipass system to improve performance and simplify
database structure. This upgrade will:

1. Migrate your organization settings to a more efficient storage system
2. Remove unused database tables
3. Improve application performance

Downtime: ~2-3 minutes during migration
Scheduled: [Date/Time]

What you'll notice:
- No visible changes to the interface
- Email footer will continue showing your organization name
- All data preserved and functional

Backup: We will create a full database backup before upgrading.

If you have any questions, please contact support.

Best regards,
Minipass Support Team
```

---

## Migration Details

**File:** `migrations/versions/cb97872b8def_remove_unused_organizations_table_and_.py`

**Changes:**
- Drops `organizations` table
- Drops `organization_id` from `user` table
- Drops `organization_id` from `activity` table
- Migrates organization name to Settings table
- Recreates financial views

**Data Migration Logic:**
1. Check if `ORG_NAME` exists → Skip if present
2. Check organizations table for data → Migrate if found
3. Create defaults if no data → Ensures application works

**Safety Features:**
- Idempotent (can run multiple times safely)
- Automatic data preservation
- Fallback to defaults
- Clear logging of all actions

---

## Support Contacts

**For Migration Issues:**
- Email: support@minipass.me
- Phone: [Support Phone]
- Emergency: [Emergency Contact]

**For Technical Questions:**
- Documentation: /docs
- Migration logs: Check Flask application logs
- Database help: SQLite query examples provided above

---

**Last Updated:** November 21, 2025
**Version:** 1.0
**Status:** Production Ready
