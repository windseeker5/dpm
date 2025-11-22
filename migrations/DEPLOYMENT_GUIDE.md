# Database Upgrade Deployment Guide

## Overview

This guide explains how to upgrade production customer databases from any previous version to the current schema (migration version `90c766ac9eed`).

The `upgrade_production_database.py` script handles all database schema changes from the 8 Flask migrations created during development.

---

## What This Upgrade Includes

### Critical Migrations Covered

The upgrade script now handles **17 tasks** covering all 8 Flask migrations:

#### Migration 1: f4c10e5088aa - Initial Schema (Nov 14, 2025)
- Base database schema (already in production)

#### Migration 2: 0307966a5581 - Payment Tracking (Nov 16, 2025)
- ✅ **Task 13**: Adds payment status tracking columns
  - `expense` table: payment_status, payment_date, due_date, payment_method
  - `income` table: payment_status, payment_date, payment_method

#### Migration 3: af5045ed1c22 - Custom Payment Instructions (Nov 18, 2025)
- ✅ **Task 14**: Adds `use_custom_payment_instructions` flag to passport_type table

#### Migration 4: a9e8d26b87b3 - Financial Views (Nov 19, 2025)
- ✅ **Task 15**: Creates SQL views for financial reporting
  - `monthly_transactions_detail` - Detailed transaction view
  - `monthly_financial_summary` - Summary view with AR/AP tracking

#### Migration 5: 937a43599a19 - AI Chatbot Column (Nov 20, 2025)
- ✅ **Task 16**: Adds `ai_answer` column to query_log table

#### Migration 6: adf18285427e - Cleanup Old Chatbot Tables (Nov 20, 2025)
- Handled automatically (drops unused tables if they exist)

#### Migration 7: cb97872b8def - Remove Organizations (Nov 20, 2025)
- ✅ **Task 17**: Migrates organization data and removes table
  - Migrates organization data to Settings table (ORG_NAME, ORG_ADDRESS, MAIL_USERNAME)
  - Removes `organization_id` from user and activity tables
  - Drops organizations table

#### Migration 8: 90c766ac9eed - Fix Financial Views (Nov 21, 2025)
- ✅ **Task 15**: Creates FIXED version of financial views
  - Fixes bug where months with only expenses were missing from reports

### Existing Tasks (1-12)
- Location fields, financial backfills, foreign key fixes, survey templates, and more

---

## Script Features

### Safety Features
- ✅ **Idempotent**: Safe to run multiple times (checks what's already done, skips completed tasks)
- ✅ **Transactional**: Automatically rolls back entire upgrade on any error
- ✅ **Data Preservation**: All existing data is preserved during table recreations
- ✅ **Comprehensive Logging**: Color-coded output shows exactly what's happening

### What Gets Applied
After running the upgrade script, production databases will have:
- ✅ Payment tracking system with status and dates
- ✅ Financial reporting SQL views (transactions + summary)
- ✅ AI chatbot answer storage capability
- ✅ Organization data properly migrated to Settings
- ✅ All foreign key constraints fixed (CASCADE/SET NULL)
- ✅ Database schema matching current development version

---

## Deployment Instructions

### Prerequisites
- SSH access to production VPS
- Docker container running with customer application
- Backup storage available

### Step 1: Identify Customer Details

For each production customer, identify:
- VPS hostname/IP
- SSH credentials
- Container name (e.g., `lhgi`)
- Database path (typically `/app/instance/minipass.db`)

### Step 2: SSH into Customer VPS

```bash
# Connect to customer VPS
ssh user@customer-vps-hostname

# Navigate to Minipass environment
cd /path/to/minipass_env/app
```

### Step 3: Create Database Backup

**CRITICAL: Always create a backup before upgrading!**

```bash
# Create timestamped backup
cp instance/minipass.db instance/minipass.db.backup_$(date +%Y%m%d_%H%M%S)

# Verify backup exists
ls -lh instance/minipass.db*
```

### Step 4: Check Current Migration Version (Optional)

```bash
# Check what version the database is currently at
FLASK_APP=app.py flask db current

# You might see an older version or "head" if migrations haven't been run
```

### Step 5: Run the Upgrade Script

```bash
# Navigate to migrations directory
cd migrations

# Run the upgrade script
python upgrade_production_database.py
```

### Expected Output

You should see color-coded output like this:

```
======================================================================
🚀 [2025-11-22 14:30:00] MASTER PRODUCTION DATABASE UPGRADE
======================================================================
📁 [2025-11-22 14:30:00] Database: /app/instance/minipass.db
🕐 [2025-11-22 14:30:00] Started: 2025-11-22 14:30:00
======================================================================
🔄 [2025-11-22 14:30:00] Transaction started

📍 [2025-11-22 14:30:00] TASK 1: Adding location fields to Activity table
⏭️  [2025-11-22 14:30:00]   Column 'location_address_raw' already exists
⏭️  [2025-11-22 14:30:00]   Column 'location_address_formatted' already exists
⏭️  [2025-11-22 14:30:00]   Column 'location_coordinates' already exists
📊 [2025-11-22 14:30:00]   Summary: 0 added, 3 already existed

💳 [2025-11-22 14:30:01] TASK 13: Adding payment status columns
✅ [2025-11-22 14:30:01]   Added expense.payment_status
✅ [2025-11-22 14:30:01]   Added expense.payment_date
✅ [2025-11-22 14:30:01]   Added expense.due_date
✅ [2025-11-22 14:30:01]   Added expense.payment_method
✅ [2025-11-22 14:30:01]   Added income.payment_status
✅ [2025-11-22 14:30:01]   Added income.payment_date
✅ [2025-11-22 14:30:01]   Added income.payment_method
📊 [2025-11-22 14:30:01]   Summary: 7 columns added, 0 already existed

[... more tasks ...]

📊 [2025-11-22 14:30:05] TASK 15: Creating financial views
🔄 [2025-11-22 14:30:05]   Dropped old views if they existed
✅ [2025-11-22 14:30:05]   Created monthly_transactions_detail view
✅ [2025-11-22 14:30:05]   Created monthly_financial_summary view (FIXED VERSION)

✅ [2025-11-22 14:30:06] Transaction committed successfully

🏷️  [2025-11-22 14:30:06] Marking Flask migrations as complete
✅ [2025-11-22 14:30:06]   Flask migrations marked as complete (flask db stamp head)

======================================================================
🎉 [2025-11-22 14:30:06] UPGRADE COMPLETED SUCCESSFULLY!
======================================================================
📊 [2025-11-22 14:30:06] Database tasks: 17/17 completed
📊 [2025-11-22 14:30:06] Total tasks: 18/18 completed (including Flask stamp)
🕐 [2025-11-22 14:30:06] Finished: 2025-11-22 14:30:06
======================================================================
```

### Step 6: Fix Migration Tracking

**IMPORTANT**: Production databases have old migration IDs that no longer exist in current migration files. After the upgrade script completes, you must manually update the migration tracking:

```bash
# Go back to app directory
cd ..

# Fix migration tracking (required for production databases)
sqlite3 instance/minipass.db "UPDATE alembic_version SET version_num = '90c766ac9eed';"

# Verify migration version (should show: 90c766ac9eed)
FLASK_APP=app.py flask db current
```

Expected output:
```
90c766ac9eed (head)
```

**Why is this needed?** Production databases were created with older migration files that have since been consolidated. The upgrade script applies all schema changes correctly, but the migration tracking metadata needs manual updating.

### Step 7: Restart Application Container

```bash
# Navigate to docker-compose directory
cd /path/to/minipass_env

# Restart the customer's container
docker-compose restart lhgi  # or customer container name

# Verify container is running
docker-compose ps
```

### Step 8: Verify Application Functionality

- Access the customer's website
- Test login
- Check financial reports (should have new views)
- Test creating/deleting passports
- Verify no errors in logs

```bash
# Check container logs for errors
docker-compose logs -f lhgi --tail=50
```

---

## Deployment to Multiple Customers

### Option 1: Manual Sequential Deployment

Run Steps 2-8 for each customer, one at a time.

**Recommended for:**
- First-time running this upgrade
- Different customers on different VPS servers
- When you want to verify each customer individually

### Option 2: Automated Batch Script

Create a deployment script for multiple customers:

```bash
#!/bin/bash
# deploy_db_upgrade_all_customers.sh

# Customer configurations
declare -A CUSTOMERS=(
    ["lhgi"]="user@lhgi-vps-hostname:/path/to/minipass_env"
    ["customer2"]="user@customer2-vps:/path/to/minipass_env"
)

for customer in "${!CUSTOMERS[@]}"; do
    echo "======================================"
    echo "Upgrading customer: $customer"
    echo "======================================"

    IFS=':' read -r ssh_target remote_path <<< "${CUSTOMERS[$customer]}"

    # SSH and run upgrade
    ssh "$ssh_target" << EOF
        cd "$remote_path/app"

        # Backup
        cp instance/minipass.db instance/minipass.db.backup_\$(date +%Y%m%d_%H%M%S)

        # Run upgrade
        cd migrations
        python upgrade_production_database.py

        # Fix migration tracking (required for production databases)
        cd ..
        sqlite3 instance/minipass.db "UPDATE alembic_version SET version_num = '90c766ac9eed';"

        # Verify
        FLASK_APP=app.py flask db current

        # Restart
        cd ..
        docker-compose restart $customer
EOF

    echo "✅ $customer upgrade complete!"
    echo ""
done

echo "🎉 All customers upgraded!"
```

**Usage:**
```bash
chmod +x deploy_db_upgrade_all_customers.sh
./deploy_db_upgrade_all_customers.sh
```

---

## Rollback Procedure

If the upgrade fails or causes issues:

### Automatic Rollback

The script uses transactions, so if it fails mid-upgrade:
- ✅ Database automatically rolls back to pre-upgrade state
- ✅ No partial changes applied
- ✅ Database remains in consistent state

### Manual Rollback (If Needed)

If you need to revert after a successful upgrade:

```bash
# Stop the application
docker-compose stop lhgi

# Restore from backup
cd /path/to/minipass_env/app/instance
cp minipass.db.backup_YYYYMMDD_HHMMSS minipass.db

# Restart application
cd ../..
docker-compose start lhgi

# Verify rollback
docker-compose logs -f lhgi
```

---

## Troubleshooting

### Script Reports Errors

**Problem**: Upgrade script shows red error messages

**Solution**:
1. Read the error message carefully
2. Database will auto-rollback (transaction-based)
3. Check that Flask and all dependencies are installed
4. Verify database file permissions
5. Restore from backup if needed

### Application Shows Errors After Upgrade

**Problem**: Application throws errors after successful upgrade

**Solution**:
1. Check error logs: `docker-compose logs -f lhgi --tail=100`
2. Verify all new columns exist: `sqlite3 instance/minipass.db ".schema expense"`
3. Restart container: `docker-compose restart lhgi`
4. If persists, rollback and investigate

### Views Not Created

**Problem**: Financial views missing after upgrade

**Solution**:
```bash
# Manually re-run Task 15
cd /path/to/minipass_env/app
python -c "
import sqlite3
conn = sqlite3.connect('instance/minipass.db')
cursor = conn.cursor()

# Import and run task15
import sys
sys.path.append('migrations')
from upgrade_production_database import task15_create_financial_views
task15_create_financial_views(cursor)

conn.commit()
conn.close()
print('Views created!')
"
```

---

## Verification Checklist

After upgrading each customer, verify:

- [ ] Database backup created with timestamp
- [ ] Upgrade script completed with "UPGRADE COMPLETED SUCCESSFULLY!" message
- [ ] `flask db current` shows `90c766ac9eed (head)`
- [ ] Application container restarted successfully
- [ ] Website loads without errors
- [ ] Admin can log in
- [ ] Financial reports page loads (uses new views)
- [ ] Can create/edit/delete passports
- [ ] No errors in container logs

---

## Migration Version Tracking

Keep track of which customers have been upgraded:

| Customer | VPS Host | Upgraded Date | Migration Version | Verified By |
|----------|----------|---------------|-------------------|-------------|
| LHGI | lhgi-vps.example.com | 2025-11-22 | 90c766ac9eed | User |
| Customer 2 | customer2-vps.example.com | - | - | - |

---

## Important Notes

1. **Safe to Run Multiple Times**: The script checks what's already done and skips completed tasks
2. **No Downtime Required**: Upgrade takes ~5-10 seconds, minimal interruption
3. **Transaction-Based**: All-or-nothing upgrade, no partial changes
4. **Preserves All Data**: Table recreations copy all existing rows
5. **No Manual SQL Required**: Script handles everything automatically

---

## Support & Questions

If you encounter issues during deployment:

1. **Check the Script Output**: Error messages are detailed and color-coded
2. **Review This Guide**: Most common issues have solutions listed above
3. **Database Auto-Rollback**: Script uses transactions, so failures auto-rollback
4. **Backup is Safe**: You always have a timestamped backup to restore from
5. **Test on Dev First**: Run the script on your local dev database before production

---

## Summary

The `upgrade_production_database.py` script provides a safe, automated way to upgrade production customer databases from any previous version to the current schema (90c766ac9eed).

**Key Benefits:**
- ✅ Covers all 8 Flask migrations (17 database tasks)
- ✅ Idempotent and transaction-based
- ✅ No data loss, comprehensive logging
- ✅ Ready for immediate deployment

**Deployment Steps:**
1. SSH into customer VPS
2. Backup database
3. Run `python migrations/upgrade_production_database.py`
4. **Fix migration tracking** (required): `sqlite3 instance/minipass.db "UPDATE alembic_version SET version_num = '90c766ac9eed';"`
5. Restart application
6. Test functionality

You're ready to upgrade your production customers! 🚀
