# Simple Local Testing Plan - LHGI Production Upgrade

**Goal:** Test upgrading LHGI production database locally before deploying to live container.

**Date:** October 30, 2025
**Context:** Testing 120+ improvements + 2-3 database migrations before production deployment

---

## Step 1: Download Production Backup (5 minutes)

1. Go to LHGI production web UI
2. Navigate to: **Settings → Backup & Restore → Create Backup**
3. Click **"Create Backup"** button
4. **Download the ZIP file** to `~/Downloads/`

---

## Step 2: Replace Your Local Database (2 minutes)

```bash
cd ~/Documents/DEV/minipass_env/app

# Backup your current dev database (just in case)
cp instance/minipass.db instance/minipass.db.backup_before_test

# Extract production backup
cd ~/Downloads
unzip minipass_backup_full_*.zip

# Copy production database to your app
cp database/minipass.db ~/Documents/DEV/minipass_env/app/instance/minipass.db

# Copy production images/uploads (receipts, hero images, activity pictures)
cp -r static/uploads/* ~/Documents/DEV/minipass_env/app/static/uploads/
```

---

## Step 3: Upgrade Database - TWO SIMPLE COMMANDS (2 minutes)

**PROBLEM:** Production database has some columns added manually (not via migrations), so `flask db upgrade` will fail with duplicate column errors.

**SOLUTION:** Run TWO simple commands - that's it!

```bash
cd ~/Documents/DEV/minipass_env/app
source venv/bin/activate

# Command 1: Run the master upgrade script (does all database changes)
python migrations/upgrade_production_database.py

# Command 2: Mark Flask migrations as complete
flask db stamp head
```

**That's it! Database is upgraded!**

**What this script does (all in one transaction):**
1. ✅ **Task 1:** Adds location fields to Activity table
2. ✅ **Task 2:** Backfills created_by for financial records
3. ✅ **Task 3:** Fixes redemption CASCADE DELETE
4. ✅ **Task 4:** Adds/UPDATES French survey template (8 questions - always uses latest version)
5. ✅ **Task 5:** Fixes email templates with Jinja2 variables
6. ✅ **Task 6:** Verifies all changes applied correctly

**You should see beautiful output like:**
```
======================================================================
🚀 MASTER PRODUCTION DATABASE UPGRADE
======================================================================
📁 Database: instance/minipass.db
🕐 Started: 2025-11-01 12:48:39
======================================================================
🔄 Transaction started

📍 TASK 1: Adding location fields to Activity table
✅   Added column 'location_address_raw'
📊   Summary: 3 added, 0 already existed

💰 TASK 2: Backfilling financial records
✅   Updated 0 income record(s)
✅   Updated 0 expense record(s)

🔗 TASK 3: Fixing redemption CASCADE DELETE
✅   Redemption table recreated with CASCADE DELETE (142 rows preserved)

📋 TASK 4: Adding French survey template
✅   French survey template UPDATED to new version (ID: 6, 8 questions)
     (or "CREATED" if it didn't exist)

✉️  TASK 5: Fixing email template Jinja2 variables
✅   Updated 3 email template(s), skipped 0

🔍 TASK 6: Verifying database schema
✅   All checks passed

✅ Transaction committed successfully
======================================================================
🎉 UPGRADE COMPLETED SUCCESSFULLY!
======================================================================
📊 Tasks completed: 6/6
🕐 Finished: 2025-11-01 12:48:39
======================================================================
```

**Then run ONE more command:**
```bash
# Mark Flask migrations as complete
flask db stamp head
```

**Why this is SUPER SAFE:**
- ✅ **Single transaction** - if ANY task fails, EVERYTHING rolls back
- ✅ **Idempotent** - safe to run multiple times (skips what's already done)
- ✅ **Detailed logging** - see exactly what's happening with colors and timestamps
- ✅ **Error handling** - tells you exactly what failed and why
- ✅ **Verification** - checks that all changes were applied correctly
- ✅ **No partial updates** - database is never left in a broken state

---

## Step 4: Start Flask and Test (10 minutes)

```bash
# Flask is already running on localhost:5000
# Just refresh your browser at http://localhost:5000
```

### Testing Checklist:

**Critical Tests (Must Pass):**
- [ ] **Passport Scanning** - Can you scan QR codes for tomorrow's hockey game?
- [ ] **Activity Images** - Do all activity pictures show up?
- [ ] **Hero Images** - Do customized email template hero images display?
- [ ] **Owner Logos** - Do email template logos display correctly?
- [ ] **Receipts** - Are income/expense receipts accessible?

**New Features Tests:**
- [ ] **Create New Activity** - Do the new beautiful templates appear?
- [ ] **Email Template Reset** - Reset templates and verify new templates load
- [ ] **Dashboard KPIs** - Does production data show correctly?
- [ ] **Mobile View** - Check mobile responsiveness improvements
- [ ] **Desktop View** - Check desktop UI improvements

**Data Integrity:**
- [ ] All passports from production are visible
- [ ] All signups from production are visible
- [ ] All users from production are visible
- [ ] Financial records (income/expense) are intact

---

## Step 5: Deploy to Production (When Ready)

### Before Deploying:
- [ ] All tests passed locally
- [ ] Passport scanning works
- [ ] Images and uploads display correctly
- [ ] Hockey game timing confirmed (deploy AFTER game or well before)

### Production Deployment Steps:

**Option A: Deploy AFTER Tomorrow's Hockey Game (Safest)**
- Wait until after the game
- Users won't be affected during active use

**Option B: Deploy Before Game (If Confident)**
- Deploy at least 4-6 hours before game time
- Test passport scanning on production immediately after deployment

### 🚀 PRODUCTION DEPLOYMENT - SIMPLE RECIPE

**FOR EACH CUSTOMER (LHGI, other customer):**

```bash
# STEP 1: SSH into production container
ssh user@production-server
cd /path/to/app

# STEP 2: Create backup FIRST (CRITICAL!)
# Option A: Use web UI - Settings → Backup & Restore → Create Backup → Download
# Option B: Make database copy manually:
cp instance/minipass.db instance/minipass.db.backup_before_upgrade_$(date +%Y%m%d)

# STEP 3: Pull latest code
git status  # Check nothing uncommitted
git pull origin main

# STEP 4: Activate virtual environment
source venv/bin/activate

# STEP 5: Run the TWO upgrade commands (SAME AS LOCAL TESTING!)
python migrations/upgrade_production_database.py
flask db stamp head

# STEP 6: Restart Flask application
# (Method depends on your deployment - choose one):
sudo systemctl restart minipass
# OR
pkill -f "flask run" && nohup flask run --host=0.0.0.0 --port=5000 &

# STEP 7: Test immediately
# 1. Open app in browser - check it loads
# 2. Test passport scanning
# 3. Check dashboard shows data
# 4. Verify images display
```

**DONE! Customer upgraded!**

---

## Rollback Plan (If Something Goes Wrong)

```bash
# Option 1: Restore from backup via Web UI
1. Settings → Backup & Restore
2. Upload the backup ZIP created before deployment
3. Click "Restore"

# Option 2: Manual rollback (if web UI broken)
ssh [production-server]
cd /path/to/app
cp instance/minipass.db.backup_[timestamp] instance/minipass.db
sudo systemctl restart minipass
```

---

## Notes

- Your local app already has latest code (120+ improvements)
- Your local database was already migrated during development
- Production database is OLD and needs these migrations applied
- The `flask db upgrade` command will apply ONLY the missing migrations to the old database
- All uploaded files (images, receipts, hero images) come from the backup ZIP

---

## Success Criteria

✅ **Ready to deploy when:**
- Migrations applied successfully with no errors
- Passport scanning works with production data
- All images/uploads display correctly
- Email templates show customized hero images and logos
- Dashboard shows production KPIs correctly
- No database errors in Flask logs

---

## Important Reminders

1. **ALWAYS create backup before touching production**
2. **Test passport scanning specifically** (critical for hockey game)
3. **Keep backup ZIP file** until deployment is confirmed stable
4. **Restore your dev database after testing:**
   ```bash
   cp instance/minipass.db.backup_before_test instance/minipass.db
   ```
