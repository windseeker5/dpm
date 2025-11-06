# Database Upgrade Deployment Guide

## What Changed in This Update

### Schema Changes
- **3 Foreign Key Constraints** modified to support passport deletion:
  - `signup.passport_id` → ON DELETE SET NULL
  - `ebank_payment.matched_pass_id` → ON DELETE SET NULL
  - `survey_response.passport_id` → ON DELETE SET NULL

### What This Fixes
- **Before**: Deleting a passport would fail with "FOREIGN KEY constraint failed"
- **After**: Deleting a passport sets related passport_id fields to NULL (preserves records)

### Data Impact
- ✅ **No data loss** - all records are preserved
- ✅ **No columns added/removed** - only FK constraint behavior changed
- ✅ **Backwards compatible** - existing data works fine

---

## Deployment to Production (VPS/Docker)

### Step 1: Backup Customer Database
```bash
# Always backup first!
docker exec <container_name> cp /app/instance/minipass.db /app/instance/minipass.db.backup_$(date +%Y%m%d_%H%M%S)
```

### Step 2: Copy Upgrade Script to Container
```bash
# Copy the upgrade script
docker cp migrations/upgrade_production_database.py <container_name>:/app/migrations/
```

### Step 3: Run the Upgrade
```bash
# Execute the upgrade script
docker exec <container_name> python3 /app/migrations/upgrade_production_database.py
```

### Step 4: Verify
```bash
# Check the application still works
docker exec <container_name> curl http://localhost:5000/
```

---

## What the Script Does

The `upgrade_production_database.py` script:

1. ✅ **Checks** if each change is already applied (safe to run multiple times)
2. ✅ **Creates backup** table structure before changes
3. ✅ **Preserves all data** during table recreation
4. ✅ **Uses transactions** - rolls back on any error
5. ✅ **Recreates indexes** after table changes
6. ✅ **Logs everything** with color-coded output

### Task 9 Details
```
TASK 9: Fixing passport deletion FK constraints (SET NULL)
  - Recreates signup table with ON DELETE SET NULL for passport_id
  - Recreates ebank_payment table with ON DELETE SET NULL for matched_pass_id
  - Recreates survey_response table with ON DELETE SET NULL for passport_id
  - Preserves all existing data
  - Recreates all indexes
```

### Task 10 Details
```
TASK 10: Fixing passport_type deletion FK constraints (SET NULL)
  - Recreates signup table with ON DELETE SET NULL for passport_type_id
  - Recreates passport table with ON DELETE SET NULL for passport_type_id
  - Recreates survey table with ON DELETE SET NULL for passport_type_id
  - Preserves all existing data
  - Recreates all indexes
```

### Task 11 Details (New)
```
TASK 11: Fixing survey deletion FK constraint (CASCADE)
  - Recreates survey_response table with ON DELETE CASCADE for survey_id
  - When a survey is deleted, all its responses are automatically deleted
  - Preserves all existing data
  - Recreates all indexes
```

---

## Testing Before Full Deployment

### Test on Dev Database First
```bash
# In your dev environment
cd /home/kdresdell/Documents/DEV/minipass_env/app
source venv/bin/activate
python3 migrations/upgrade_production_database.py
```

### Verify Passport Deletion Works
1. Navigate to passports page
2. Select a test passport
3. Click "Delete"
4. Should complete without errors
5. Related records (signups, payments) should have passport_id = NULL

---

## Rollback Plan

If something goes wrong:

```bash
# Restore from backup
docker exec <container_name> cp /app/instance/minipass.db.backup_YYYYMMDD_HHMMSS /app/instance/minipass.db

# Restart container
docker restart <container_name>
```

---

## For Multiple Customers

Create a deployment script:

```bash
#!/bin/bash
# deploy_db_upgrade.sh

CONTAINERS=("customer1_container" "customer2_container" "customer3_container")

for container in "${CONTAINERS[@]}"; do
    echo "Upgrading $container..."

    # Backup
    docker exec $container cp /app/instance/minipass.db /app/instance/minipass.db.backup_$(date +%Y%m%d_%H%M%S)

    # Copy script
    docker cp migrations/upgrade_production_database.py $container:/app/migrations/

    # Run upgrade
    docker exec $container python3 /app/migrations/upgrade_production_database.py

    echo "$container upgraded!"
    echo "---"
done
```

---

## Important Notes

1. **Safe to run multiple times** - script checks what's already done
2. **No Flask required on host** - pure Python 3 script
3. **Transaction-based** - all-or-nothing, no partial changes
4. **Preserves data** - table recreation copies all rows
5. **Idempotent** - running twice has same effect as running once

---

## Support

If the upgrade fails:
1. Check the error message in script output
2. Database will be rolled back automatically
3. Restore from backup if needed
4. Contact support with full error log
