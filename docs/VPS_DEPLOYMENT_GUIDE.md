# VPS Deployment Guide - Minipass Customer Containers

**Purpose:** Deploy bug fixes and feature updates to production customer containers on VPS without losing customer data.

**Last Updated:** November 2, 2025

---

## 🔑 First Time? Set Up .env File

**If you haven't set up the .env file yet** (contains Google Maps, Groq, Unsplash API keys):

👉 **Follow this guide first:** [ENV_SETUP.md](ENV_SETUP.md) (3 simple steps, 5 minutes)

After that's done once, come back here for regular deployments.

---

## Quick Reference

**📋 TL;DR:** See [QUICK_DEPLOY_LHGI.md](QUICK_DEPLOY_LHGI.md) for a 5-step cheat sheet

**Deployment Time:** ~5-7 minutes
**Downtime:** ~30 seconds (container restart)
**Safety:** Automatic database backup + rollback on failure + safe database migrations
**Git Branch:** `main` (production branch)

---

## 🔒 Database Safety Guarantee

**YOUR CUSTOMER DATA IS ALWAYS SAFE:**

✅ **Database is in `.gitignore`** - Git operations CANNOT touch the database file
- Lines 24-25 in `.gitignore`: `*.db` and `instance/*.db`
- `git reset --hard` only affects tracked files (database is NOT tracked)
- Customer data survives all git operations

✅ **Database upgrades use transactions** - All-or-nothing approach
- 8 upgrade tasks run in a single transaction
- If ANY task fails, ALL changes are rolled back automatically
- Database is never left in a broken state

✅ **Automatic backups before deployment**
- Deploy script creates backup: `instance/minipass_backup_YYYYMMDD_HHMMSS.db`
- You can restore from backup at any time
- Keep at least 5 most recent backups

✅ **Idempotent upgrade script**
- Safe to run multiple times
- Skips tasks that are already completed
- No risk of double-applying changes

**Bottom line:** You cannot accidentally delete customer data through this deployment process.

---

## Prerequisites

Before deploying, ensure:

- ✅ All code changes committed and pushed to git `main` branch
- ✅ Local testing completed successfully
- ✅ Database migrations tested locally (if any schema changes)
- ✅ No critical activities scheduled during deployment (e.g., hockey game in progress)
- ✅ SSH access to VPS configured

**IMPORTANT:** The database (`instance/minipass.db`) is in `.gitignore` and will NOT be overwritten by git pull. Customer data is always preserved.

---

## Deployment Process

### Step 1: Push Your Changes (Local Machine)

```bash
# On your local development machine
cd /home/kdresdell/Documents/DEV/minipass_env/app

# Verify your changes
git status

# Commit your changes (database is NOT committed - it's in .gitignore)
git add -A
git commit -m "Fix [describe your fixes] - includes updated features"

# Push to main branch (production branch)
git push origin main
```

**Important:**
- The `main` branch is the production branch. All customer containers pull from this branch.
- The database (`instance/minipass.db`) is automatically excluded from git via `.gitignore`
- Customer databases are NEVER overwritten by git operations

---

### Step 2: Deploy on VPS

#### 2.1 Connect to VPS

```bash
# SSH to your VPS
ssh your-vps-user@your-vps-host
# Example: ssh -p 2222 kdresdell@minipass.me

# Navigate to deployment directory
cd /home/kdresdell/minipass_env
```

#### 2.2 Pull Latest Code (Force Update)

```bash
# Navigate to app directory
cd /home/kdresdell/minipass_env/app

# Force pull latest changes (handles any conflicts)
git fetch origin main
git reset --hard origin/main

# Return to deployment directory
cd ..
```

**Why `git reset --hard`?**
This ensures the VPS matches your git repository exactly, overwriting any local code changes. The production database is safe because:
1. `instance/minipass.db` is in `.gitignore` (never tracked in git)
2. Git operations cannot touch files that are not tracked
3. Customer data is preserved across all deployments

#### 2.3 Upgrade Customer Database (CRITICAL STEP)

**⚠️ IMPORTANT:** This step MUST be done BEFORE deploying the container if there are database schema changes.

```bash
# Still in /home/kdresdell/minipass_env directory
cd app

# Activate virtual environment (if available on VPS)
source venv/bin/activate 2>/dev/null || true

# Run the production database upgrade script
python3 migrations/upgrade_production_database.py

# Mark Flask migrations as complete
flask db stamp head

# Return to deployment directory
cd ..
```

**What This Upgrade Script Does (8 Tasks):**
1. ✅ Adds location fields to Activity table (location_address_raw, location_address_formatted, location_coordinates)
2. ✅ Backfills financial records (sets created_by='legacy' for old records)
3. ✅ Fixes redemption table CASCADE DELETE (prevents orphaned records)
4. ✅ Adds/updates French survey template (8 questions, always latest version)
5. ✅ Fixes email template Jinja2 variables ({{ activity_name }}, {{ question_count }})
6. ✅ Adds email_received_date to ebank_payment table
7. ✅ Fixes reminder_log CASCADE DELETE
8. ✅ Verifies all schema changes applied correctly

**Safety Features:**
- ✅ **Single Transaction:** All changes in one transaction - rolls back entirely if ANY task fails
- ✅ **Idempotent:** Safe to run multiple times - skips what's already done
- ✅ **Detailed Logging:** Color-coded output shows exactly what's happening
- ✅ **No Partial Updates:** Database is never left in a broken state

**Expected Output:**
```
======================================================================
🚀 MASTER PRODUCTION DATABASE UPGRADE
======================================================================
📁 Database: instance/minipass.db
🕐 Started: 2025-11-02 14:30:22
======================================================================
🔄 Transaction started

📍 TASK 1: Adding location fields to Activity table
✅   Added column 'location_address_raw'
✅   Added column 'location_address_formatted'
✅   Added column 'location_coordinates'
📊   Summary: 3 added, 0 already existed

💰 TASK 2: Backfilling financial records
✅   Updated 0 income record(s)
✅   Updated 0 expense record(s)

🔗 TASK 3: Fixing redemption CASCADE DELETE
✅   Redemption table recreated with CASCADE DELETE (142 rows preserved)

📋 TASK 4: Adding French survey template
✅   French survey template UPDATED to new version (ID: 6, 8 questions)

✉️  TASK 5: Fixing email template Jinja2 variables
✅   Updated 3 email template(s), skipped 0

📅 TASK 6: Adding email_received_date to ebank_payment table
✅   Added column 'email_received_date'

🔗 TASK 7: Fixing reminder_log CASCADE DELETE
✅   reminder_log table recreated with CASCADE DELETE (23 rows preserved)

🔍 TASK 8: Verifying database schema
✅   All checks passed

✅ Transaction committed successfully
======================================================================
🎉 UPGRADE COMPLETED SUCCESSFULLY!
======================================================================
📊 Tasks completed: 8/8
🕐 Finished: 2025-11-02 14:30:23
======================================================================
```

**If Upgrade Fails:**
- ❌ Script will rollback ALL changes automatically
- ❌ Database remains unchanged (safe)
- ❌ Error message will explain what failed
- ❌ DO NOT proceed to deploy container until issue is resolved

---

#### 2.4 Run Deployment Script

```bash
# Execute the automated deployment script
./deploy-lghi-vps.sh
```

**What This Script Does:**
1. ✅ Creates automatic database backup (`instance/minipass_backup_YYYYMMDD_HHMMSS.db`)
2. ✅ Clears Docker cache to prevent stale builds
3. ✅ Tags current image as `:backup` for rollback
4. ✅ Stops the `lhgi` container
5. ✅ Builds new image with `--no-cache` flag
6. ✅ Starts new container
7. ✅ Verifies deployment via health check
8. ✅ Rolls back automatically if health check fails

**Note:** The deploy script does NOT run database migrations. You MUST run the database upgrade script manually in step 2.3 before deploying.

#### 2.5 Verify Deployment Success

The script will output:

```
🚀 Deploying Minipass LHGI container...
💾 Database backup created
🔄 Pulling latest code while preserving local database...
🧹 Aggressive Docker cache clearing to prevent cache issues...
💾 Tagging current image as backup...
🛑 Stopping container...
🔨 Building new image with no cache...
🚀 Starting new container...
⏳ Testing new deployment...
✅ Container is running
🔍 Verifying deployed version...
✅ Version verified! Deployed: abc12345
🗑️ Cleaning up old backup...
🌐 App running at: https://lhgi.minipass.me
🔒 Production database preserved and secure!
```

**Success Indicators:**
- ✅ "Container is running" message appears
- ✅ Version verified matches expected git commit
- ✅ No error messages in output
- ✅ App accessible at https://lhgi.minipass.me

---

## Database Migrations

**⚠️ CRITICAL:** Database upgrades are NOT automatic. You MUST manually run the upgrade script BEFORE deploying the container (see Step 2.3).

**Why Manual Database Upgrades?**
- Ensures you have full control over when migrations run
- Allows you to verify upgrade success before container restart
- Prevents automatic migrations from breaking running containers
- Gives you time to create manual backups if needed

**Migration Script Location:**
`/home/kdresdell/minipass_env/app/migrations/upgrade_production_database.py`

**Current Migration Tasks (as of Nov 2025):**
1. Add location fields to Activity table (location_address_raw, formatted, coordinates)
2. Backfill financial records (created_by='legacy' for old records)
3. Fix redemption CASCADE DELETE (prevents orphaned records when passports deleted)
4. Add/update French survey template (8 questions, always latest version)
5. Fix email template Jinja2 variables ({{ activity_name }}, {{ question_count }})
6. Add email_received_date to ebank_payment table
7. Fix reminder_log CASCADE DELETE (prevents orphaned logs)
8. Mark Flask migrations complete (flask db stamp head)

**How to Run Database Upgrade:**
```bash
# SSH to VPS
ssh your-vps-user@your-vps-host

# Navigate to app directory
cd /home/kdresdell/minipass_env/app

# Run upgrade script
python3 migrations/upgrade_production_database.py

# Mark Flask migrations as complete
flask db stamp head
```

**Safety Features:**
- ✅ **Single Transaction:** All 8 tasks in one transaction - rolls back entirely if ANY task fails
- ✅ **Idempotent:** Safe to run multiple times - skips what's already done
- ✅ **Detailed Logging:** Color-coded output with timestamps shows exactly what's happening
- ✅ **Verification Step:** Task 8 verifies all schema changes applied correctly
- ✅ **No Partial Updates:** Database is never left in a broken state
- ✅ **Automatic Rollback:** If ANY task fails, ALL changes are rolled back

**When to Run Database Upgrades:**
- ✅ When upgrading customer containers with schema changes
- ✅ After pulling latest code from git
- ✅ BEFORE restarting the container
- ❌ NOT while container is actively handling traffic (stop container first if unsure)

---

## Verification Checklist

After deployment, verify the following:

### Critical Functionality
- [ ] **App Loads:** Visit https://lhgi.minipass.me (should load without errors)
- [ ] **Login Works:** Test admin login
- [ ] **Dashboard Shows Data:** KPI cards display correct numbers
- [ ] **Images Display:** Activity images, hero images, receipts visible
- [ ] **Passport Scanning:** QR code scanning works (critical for active events)

### Check Logs
```bash
# SSH into VPS (if not already connected)
ssh your-vps-user@your-vps-host

# View container logs
cd /home/kdresdell/minipass_env
docker-compose logs -f lhgi

# Look for:
# - No error messages
# - "Migration completed successfully" (if migrations ran)
# - Gunicorn started with 2 workers
```

### Quick Health Check
```bash
# Check container status
docker ps | grep lhgi

# Should show:
# - Container status: "Up X minutes"
# - Port: 8889/tcp
```

---

## Rollback Procedure

**If deployment fails, the script automatically rolls back.**

However, if you need to manually rollback:

### Automatic Rollback (Built into Script)

The deploy script automatically rolls back if:
- Container fails to start
- Health check fails
- Version mismatch detected

You'll see:
```
❌ Container failed to start! Rolling back...
🔄 Rollback complete
```

### Manual Rollback (If Needed)

```bash
# SSH to VPS
ssh your-vps-user@your-vps-host
cd /home/kdresdell/minipass_env

# Stop current container
docker stop lhgi

# Restore previous image
docker tag minipass_env-lhgi:backup minipass_env-lhgi:latest

# Start container with previous version
docker-compose up -d lhgi

# Verify rollback
docker ps | grep lhgi
curl -s http://localhost:8889/health
```

### Restore Database from Backup (If Needed)

```bash
# SSH to VPS
ssh your-vps-user@your-vps-host

# Navigate to database directory
cd /home/kdresdell/minipass_env/app/instance

# List available backups
ls -lh minipass_backup_*.db

# Restore from backup (example timestamp)
cp minipass_backup_20251102_143022.db minipass.db

# Restart container
cd /home/kdresdell/minipass_env
docker-compose restart lhgi
```

---

## Troubleshooting

### Problem: "Container fails to start"

**Symptoms:**
```
❌ Container failed to start! Rolling back...
```

**Solutions:**
1. Check Docker logs:
   ```bash
   docker-compose logs lhgi
   ```
2. Look for Python errors (syntax errors, missing dependencies)
3. Verify `requirements.txt` is complete
4. Check if port 8889 is already in use

---

### Problem: "Version mismatch detected"

**Symptoms:**
```
❌ Version mismatch! Expected: abc12345, Got: xyz67890
🔄 This indicates a cache issue - rolling back...
```

**Cause:** Docker cached an old image layer

**Solution:**
The script automatically handles this by:
1. Running `docker system prune -f`
2. Running `docker builder prune -f`
3. Building with `--no-cache` flag

If this persists, manually clear Docker cache:
```bash
docker system prune -a -f
docker builder prune -a -f
```

---

### Problem: "Health check failed"

**Symptoms:**
```
⚠️  Could not verify version (health check failed), but container is running
```

**Cause:** Flask app not responding on port 8889

**Solutions:**
1. Check if Flask started:
   ```bash
   docker exec lhgi ps aux | grep gunicorn
   ```
2. Check Flask logs:
   ```bash
   docker logs lhgi
   ```
3. Verify database is accessible:
   ```bash
   docker exec lhgi ls -lh instance/minipass.db
   ```

---

### Problem: "Database upgrade script fails"

**Symptoms:**
```
❌ Task 'Schema Changes' failed: ...
↩️  Transaction rolled back - database unchanged
💡 Database is safe - no partial changes applied
```

**Cause:** Schema change failed, data integrity issue, or Python error

**Solutions:**
1. **Good news:** Database was NOT changed (automatic rollback)
2. Check what failed:
   ```bash
   # The error message will tell you which task failed and why
   # Example: "Task 'Schema Changes' failed: column already exists"
   ```
3. Common issues:
   - **Column already exists:** Script is idempotent, this is usually OK. Re-run script.
   - **Python module missing:** Install dependencies (`pip install -r requirements.txt`)
   - **Database locked:** Container is running. Stop container first.

4. If script says "already done" for all tasks:
   ```bash
   # This is SAFE - database is already upgraded
   # Proceed to deploy container
   ```

5. If genuine failure:
   ```bash
   # Restore from backup
   cd /home/kdresdell/minipass_env/app/instance
   cp minipass_backup_YYYYMMDD_HHMMSS.db minipass.db

   # Contact developer for assistance
   ```

**When to Skip Database Upgrade:**
- ✅ If all tasks show "⏭️  already exists" or "⏭️  skipped" (already upgraded)
- ✅ If this is a code-only change with no schema changes
- ❌ If ANY task shows ❌ error (must fix before proceeding)

---

### Problem: "Images/uploads not displaying"

**Cause:** Volume mount issue or file permissions

**Solution:**
```bash
# Check volume mount
docker inspect lhgi | grep Mounts -A 10

# Should show:
# "Source": "/home/kdresdell/minipass_env/app/instance"
# "Destination": "/app/instance"

# Check file permissions
docker exec lhgi ls -lh instance/
docker exec lhgi ls -lh static/uploads/
```

---

## Architecture Notes

### Container Setup
- **Base Image:** `python:3.9`
- **WSGI Server:** Gunicorn (2 workers, 4 threads)
- **Port:** 8889 (internal), 443 (external via nginx-proxy)
- **Domain:** https://lhgi.minipass.me
- **Database:** SQLite mounted as volume (`./app/instance:/app/instance`)

### Git Strategy
- **Branch:** `main` (production branch)
- **Approach:** Force overwrite (`git reset --hard origin/main`)
- **Database:** NOT in git - in `.gitignore` (line 24-25: `*.db` and `instance/*.db`)
- **Uploads:** NOT in git - in `.gitignore` (line 40: `static/uploads/`)
- **Database Safety:** Git operations CANNOT affect database because it's not tracked

### Docker Compose Service
```yaml
lhgi:
  build:
    context: ./app
  container_name: lhgi
  restart: always
  environment:
    - FLASK_ENV=prod
    - VIRTUAL_HOST=lhgi.minipass.me
    - VIRTUAL_PORT=8889
    - LETSENCRYPT_HOST=lhgi.minipass.me
    - LETSENCRYPT_EMAIL=kdresdell@gmail.com
    - TZ=America/Toronto
  expose:
    - "8889"
  volumes:
    - ./app/instance:/app/instance
    - /etc/localtime:/etc/localtime:ro
  networks:
    - proxy
```

---

## Deployment Checklist Template

Use this checklist before each deployment:

### Pre-Deployment
- [ ] Code changes tested locally
- [ ] All tests passing
- [ ] Database migrations tested locally (if schema changes)
- [ ] Changes committed and pushed to `main` branch
- [ ] Customer notified (if significant changes or downtime expected)
- [ ] No critical activities in progress (e.g., hockey game)
- [ ] VPS SSH access confirmed

### During Deployment
- [ ] SSH to VPS successful
- [ ] Git pull completed (`git reset --hard origin/main`)
- [ ] **Database upgrade script executed successfully** (`python3 migrations/upgrade_production_database.py`)
- [ ] **Flask migrations stamped** (`flask db stamp head`)
- [ ] All 8 database tasks completed with ✅
- [ ] Deploy script executed (`./deploy-lghi-vps.sh`)
- [ ] No error messages in output
- [ ] Health check passed
- [ ] Version verified

### Post-Deployment
- [ ] App loads at https://lhgi.minipass.me
- [ ] Login works
- [ ] Dashboard displays correctly
- [ ] Images/uploads visible
- [ ] Passport scanning tested (if applicable)
- [ ] Logs checked for errors
- [ ] Customer notified of successful deployment

---

## Quick Commands Reference

```bash
# Local - Push changes
cd /home/kdresdell/Documents/DEV/minipass_env/app
git add -A && git commit -m "Your message" && git push origin main

# VPS - Full Deployment (3 steps)
ssh your-vps-user@your-vps-host
# Step 1: Pull code
cd /home/kdresdell/minipass_env/app && git fetch origin main && git reset --hard origin/main
# Step 2: Upgrade database (CRITICAL!)
python3 migrations/upgrade_production_database.py && flask db stamp head
# Step 3: Deploy container
cd .. && ./deploy-lghi-vps.sh

# VPS - Check status
docker ps | grep lhgi
docker logs lhgi --tail 50

# VPS - Check database upgrade logs
cd /home/kdresdell/minipass_env/app
python3 migrations/upgrade_production_database.py

# VPS - Access container shell
docker exec -it lhgi /bin/bash

# VPS - Restart container only (no code/db changes)
docker-compose restart lhgi
```

---

## Related Scripts

- **Deploy Script:** `/home/kdresdell/minipass_env/deploy-lghi-vps.sh`
- **Migration Script:** `/home/kdresdell/minipass_env/app/migrations/upgrade_production_database.py`
- **Docker Compose:** `/home/kdresdell/minipass_env/docker-compose.yml`
- **Dockerfile:** `/home/kdresdell/minipass_env/app/dockerfile`

---

## Support & Questions

**If deployment fails:**
1. Check logs: `docker logs lhgi`
2. Review troubleshooting section above
3. Rollback if necessary (automatic or manual)
4. Contact developer if issue persists

**For database issues:**
- Database backups are automatic before each deployment
- Backups stored in: `/home/kdresdell/minipass_env/app/instance/minipass_backup_*.db`
- Keep at least 5 most recent backups

---

**Total Deployment Time:** ~5 minutes
**Process:** Local push → VPS git pull → Deploy script → Live ✅
