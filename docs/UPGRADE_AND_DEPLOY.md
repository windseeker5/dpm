# Minipass Upgrade Guide

**Simple guide for upgrading LHGI and customer containers without losing data**

Time Required: 5-7 minutes per deployment

---

## Quick Start - Choose Your Path

- **Path 1**: [LHGI Upgrade](#lhgi-deployment-prototype) - 10 steps, manual upgrade with database migration
- **Path 2**: [Customer Upgrade (HEQ, etc.)](#customer-upgrade-heq-etc) - 11 steps, backup OUTSIDE app directory, keep all data safe

---

## LHGI Deployment (Prototype)

**Container**: lhgi
**Domain**: lhgi.minipass.me
**Location**: `/home/kdresdell/minipass_env/app/`
**Time**: 5-7 minutes

### Prerequisites
- Code pushed to `main` branch
- SSH access to VPS

### Steps

#### Step 1: Push Code to Main Branch
```bash
# On your local machine
cd /home/kdresdell/Documents/DEV/minipass_env
git add .
git commit -m "Your commit message"
git push origin main
```

#### Step 2: Connect to VPS and Pull Latest Code
```bash
# Connect to VPS
ssh -p 2222 kdresdell@minipass.me

# Navigate to app directory
cd /home/kdresdell/minipass_env/app

# Force pull latest code (safe - database is in .gitignore)
git fetch origin
git reset --hard origin/main
```

#### Step 3: Update .env File (If Needed)
```bash
# On your LOCAL machine, upload the latest .env file
scp -P 2222 /home/kdresdell/Documents/DEV/minipass_env/app/.env kdresdell@minipass.me:/home/kdresdell/minipass_env/.env
```

**Note**: The .env file is shared at the root level (`/home/kdresdell/minipass_env/.env`), not in the app folder.

---

### ⚠️ CRITICAL: Verify Volume Mounts Before Rebuilding

**STOP!** Before stopping the container, verify your docker-compose.yml has the correct volume mounts:

```bash
# On VPS, check your docker-compose.yml
cat /home/kdresdell/minipass_env/docker-compose.yml | grep -A 5 "lhgi:" | grep volumes -A 3
```

**Required volume mounts for LHGI:**
```yaml
volumes:
  - ./app/instance:/app/instance           # Database (CRITICAL)
  - ./app/static/uploads:/app/static/uploads  # User uploads (CRITICAL)
  - /etc/localtime:/etc/localtime:ro       # Timezone
```

**⚠️ IF `static/uploads` IS MISSING**: Container rebuilds will DELETE all user-uploaded images!
- Activity cover photos
- Logo files
- Email attachments
- All uploaded content

**Fix it NOW before proceeding** by adding the missing line to docker-compose.yml.

---

#### Step 4: Stop Container (CRITICAL - Prevents Database Corruption)
```bash
# On VPS, stop the container to prevent active connections during migration
cd /home/kdresdell/minipass_env
docker-compose stop lhgi
```

**Why This is Critical**:
- Prevents users from accessing the system during database schema changes
- Prevents database corruption from active connections
- Prevents application errors from code/schema mismatch
- Ensures clean migration without race conditions

#### Step 5: Upgrade Database (CRITICAL - DO NOT SKIP)
```bash
# On VPS, in the app directory
cd /home/kdresdell/minipass_env/app

# Run the migration script
python3 migrations/upgrade_production_database.py

# Fix migration tracking (the script will tell you which command to run)
# The script will output something like:
#   sqlite3 instance/minipass.db "UPDATE alembic_version SET version_num = '90c766ac9eed';"
# Copy and run that exact command
```

**Note**: The script will tell you the exact sqlite3 command to run. If you have Flask installed, you can use `flask db stamp head` instead, but the sqlite3 command always works.

**What to Expect**:
- Script runs 17 tasks (see [Database Migration Details](#database-migration-details) below)
- Each task shows: ✅ (success), ⏭️ (skipped/already done), or ❌ (error)
- **DO NOT PROCEED if you see any ❌ errors**
- Script creates automatic backup before starting
- Automatic rollback on any failure

#### Step 6: Clear Docker Cache
```bash
# On VPS, clear Docker cache to ensure clean build
cd /home/kdresdell/minipass_env
docker system prune -f
docker builder prune -f
```

**Why This is Important**:
- Prevents old cached layers from causing version mismatches
- Ensures you get a completely fresh build with latest code

#### Step 7: Tag Current Image as Backup
```bash
# On VPS, tag current image for rollback capability
docker tag minipass_env-lhgi:latest minipass_env-lhgi:backup 2>/dev/null || true
```

**Why This is Important**:
- Allows quick rollback if new deployment fails
- Preserves working version

#### Step 8: Build New Container
```bash
# On VPS, build new container with no cache
cd /home/kdresdell/minipass_env
docker-compose build --no-cache --pull lhgi
```

**What to Expect**:
- Build process will download latest Python packages
- Takes 2-5 minutes depending on VPS speed
- Should complete without errors

#### Step 9: Start Container
```bash
# On VPS, start the lhgi container
cd /home/kdresdell/minipass_env
docker-compose up -d lhgi
```

#### Step 10: Verify Deployment
```bash
# Check container is running
docker ps | grep lhgi

# Check logs for errors
docker logs lhgi --tail 50

# Visit the site
# https://lhgi.minipass.me
```

**Success Indicators**:
- Container status shows "Up X minutes"
- No errors in logs
- Website loads correctly
- Database shows correct version

**Note on deploy-lghi-vps.sh**: The old `deploy-lghi-vps.sh` script is **no longer needed**. All deployment steps are now explicitly listed above for clarity and simplicity. You can optionally delete the script or keep it as a backup.

---

## Customer Upgrade (HEQ, etc.)

**Example Container**: minipass_heq
**Example Domain**: heq.minipass.me
**Location**: `/home/kdresdell/minipass_env/deployed/{customer}/`

**⚠️ IMPORTANT**: This is for **UPGRADING existing customers** who already have data. The auto-deploy tool is ONLY for initial deployment of NEW customers!

---

### 🚨 CRITICAL BACKUP WARNING 🚨

**BACKUP TO HOME DIRECTORY, NOT INSIDE `app/`!**

If you backup inside `app/` and then delete `app/`, **YOU LOSE EVERYTHING!**

✅ **CORRECT**: `cp app/instance/minipass.db ~/heq_backup_xxx.db`
❌ **WRONG**: `cp app/instance/minipass.db app/instance/minipass_backup_xxx.db`

**The backup MUST be OUTSIDE the `app/` directory or you will lose customer data!**

---

### Upgrade Steps (Simple & Safe)

#### Step 1: Connect to VPS
```bash
# SSH to VPS
ssh -p 2222 kdresdell@minipass.me

# Navigate to customer directory
cd /home/kdresdell/minipass_env/deployed/heq
```

#### Step 2: Backup Database OUTSIDE App Directory (CRITICAL!)
```bash
# ⚠️ CRITICAL: Backup to HOME directory (NOT inside app/!)
# If you backup inside app/, rm -rf will delete it!

cp app/instance/minipass.db ~/heq_backup_$(date +%Y%m%d_%H%M%S).db

# Verify backup exists OUTSIDE app directory
ls -lh ~/heq_backup_*.db
```

#### Step 3: Backup Uploads OUTSIDE App Directory
```bash
# Backup uploads to HOME directory
cp -r app/static/uploads ~/heq_uploads_backup_$(date +%Y%m%d_%H%M%S)

# Verify backup exists
ls -lh ~/heq_uploads_backup_*
```

#### Step 4: Stop Container
```bash
# Now it's safe to stop container - backups are OUTSIDE app/
docker-compose down
```

#### Step 5: Update Code (Git Reset Method - SAFER)
```bash
# Option A: Git reset (RECOMMENDED - keeps directory structure)
cd app
git fetch origin
git reset --hard origin/main
git clean -fd
cd ..

# Option B: Fresh clone (if git is broken)
# Only use this if Option A fails!
# rm -rf app
# git clone git@github.com:windseeker5/dpm.git app
# cd app
# git checkout main
# cd ..
```

**Why Option A is better:**
- Keeps the `app/` directory structure
- Safer - doesn't delete everything
- Faster - just updates code files

#### Step 6: Restore Database and Uploads
```bash
# Copy database back from HOME directory
cp ~/heq_backup_*.db app/instance/minipass.db

# Copy uploads back from HOME directory
cp -r ~/heq_uploads_backup_*/. app/static/uploads/

# Verify files are restored
ls -lh app/instance/minipass.db
ls -lh app/static/uploads/
```

#### Step 7: Update .env (If Needed)
```bash
# On LOCAL machine, if .env changed:
scp -P 2222 /home/kdresdell/Documents/DEV/minipass_env/app/.env kdresdell@minipass.me:/home/kdresdell/minipass_env/.env
```

**Note**: Customers use shared `.env` at `/home/kdresdell/minipass_env/.env`

#### Step 8: Upgrade Database
```bash
# On VPS, run migration script
cd /home/kdresdell/minipass_env/deployed/heq/app

# Run the upgrade script (upgrades EXISTING database)
python3 migrations/upgrade_production_database.py

# The script will tell you the sqlite3 command to run, like:
# sqlite3 instance/minipass.db "UPDATE alembic_version SET version_num = '90c766ac9eed';"
# Run that command
```

**What to expect:**
- Script runs 17 tasks on existing database
- Shows ✅ for success, ⏭️ for already done, ❌ for errors
- If you see ❌, DO NOT continue - fix the error first
- Database is backed up, so safe to re-run if needed

#### Step 9: Verify docker-compose.yml Volume Mounts
```bash
# On VPS, check volume mounts
cd /home/kdresdell/minipass_env/deployed/heq
cat docker-compose.yml | grep -A 5 "volumes:"
```

**MUST have these three volumes:**
```yaml
volumes:
  - ./app:/app
  - ./app/instance:/app/instance           # Database (CRITICAL)
  - ./app/static/uploads:/app/static/uploads  # Uploads (CRITICAL)
```

**If `static/uploads` is missing**, add it now:
```bash
nano docker-compose.yml
# Add the line: - ./app/static/uploads:/app/static/uploads
```

#### Step 10: Rebuild and Start Container
```bash
# On VPS
cd /home/kdresdell/minipass_env/deployed/heq

# Rebuild container with no cache
docker-compose build --no-cache

# Start container
docker-compose up -d
```

#### Step 11: Verify Upgrade
```bash
# Check container is running
docker ps | grep heq

# Check logs for errors
docker logs minipass_heq --tail 50

# Visit site
# https://heq.minipass.me
```

**Success checklist:**
- ✅ Container shows "Up X minutes"
- ✅ No errors in logs
- ✅ Website loads correctly
- ✅ Activity pictures still display (NOT BLANK!)
- ✅ Customer can log in
- ✅ QR codes work

**Done!** Customer upgraded with all data preserved.

---

## Database Migration Details

### Script Location
`/home/kdresdell/minipass_env/app/migrations/upgrade_production_database.py`

### How to Run
```bash
# On VPS or LOCAL (for testing), in the app/ directory
python3 migrations/upgrade_production_database.py

# The script will tell you the exact command to run, something like:
# sqlite3 instance/minipass.db "UPDATE alembic_version SET version_num = '90c766ac9eed';"
# Copy and run that exact command

# OR if Flask is installed: flask db stamp head
```

### Safety Features
- **Single transaction**: All-or-nothing, no partial updates
- **Automatic rollback**: Any error rolls back ALL changes
- **Automatic backup**: Creates backup before starting (for deploy-lghi-vps.sh)
- **Idempotent**: Safe to run multiple times
- **Detailed logging**: Color-coded status for each task

### The 17 Migration Tasks

The script performs these 17 tasks in order:

1. **Add location fields to Activity table**
   - Adds: location_name, location_address, location_city, location_postal_code, location_province, location_country

2. **Add payment status columns**
   - Adds: income_paid, income_scheduled, expense_paid, expense_scheduled

3. **Backfill financial records**
   - Migrates payment data with created_by='legacy'

4. **Fix redemption CASCADE DELETE**
   - Ensures redemptions are deleted when passport is deleted

5. **Add French survey template**
   - Creates default survey with 8 questions in French

6. **Fix email template Jinja2 variables**
   - Updates {{ variable }} syntax in templates

7. **Verify database schema**
   - Checks all tables and columns exist correctly

8. **Add email_received_date to ebank_payment**
   - Tracks when email was received for payment matching

9. **Fix reminder_log CASCADE DELETE**
   - Migrates pass_id → passport_id with proper foreign key

10. **Fix passport deletion foreign keys**
    - Sets dependent records to NULL when passport deleted

11. **Fix passport_type deletion foreign keys**
    - Sets dependent records to NULL when passport_type deleted

12. **Drop old 'pass' table**
    - Removes deprecated table if empty

13. **Fix survey deletion foreign key**
    - Ensures survey responses are deleted with survey (CASCADE)

14. **Add custom payment instructions flag**
    - Adds: use_custom_payment_instructions (boolean)

15. **Add AI answer column to query_log**
    - Tracks AI-generated responses for chatbot

16. **Remove organizations table**
    - Migrates organizations.name → Settings.ORG_NAME
    - Migrates organizations.mail_username → Settings.MAIL_USERNAME
    - Drops organizations table after migration

17. **Create financial views**
    - monthly_transactions_detail: All transactions by month
    - monthly_financial_summary: Income/expense totals by month

### What Success Looks Like

```
✅ Task 1: Add location fields to Activity table
✅ Task 2: Add payment status columns
⏭️ Task 3: Backfill financial records (already done)
✅ Task 4: Fix redemption CASCADE DELETE
⏭️ Task 5: Add French survey template (already exists)
✅ Task 6: Fix email template Jinja2 variables
✅ Task 7: Verify database schema
✅ Task 8: Add email_received_date to ebank_payment
✅ Task 9: Fix reminder_log CASCADE DELETE
✅ Task 10: Fix passport deletion foreign keys
✅ Task 11: Fix passport_type deletion foreign keys
⏭️ Task 12: Drop old 'pass' table (already dropped)
✅ Task 13: Fix survey deletion foreign key
✅ Task 14: Add custom payment instructions flag
✅ Task 15: Add AI answer column to query_log
✅ Task 16: Remove organizations table
✅ Task 17: Create financial views

All upgrades completed successfully! ✓
```

### If You See Errors

**DO NOT DEPLOY** if you see any ❌ errors.

Example error:
```
❌ Task 5: Add French survey template
Error: duplicate key value violates unique constraint
```

**What to do**:
1. Read the error message carefully
2. Check if the issue is data-related (e.g., duplicate data)
3. Fix the underlying issue
4. Run the script again (it's safe to re-run)
5. If errors persist, contact developer

**Automatic Rollback**:
- If ANY task fails, ALL changes are rolled back automatically
- Database is left in its original state
- No partial updates are possible

---

## Backup Procedures

### Automatic Backups

The deployment script (`deploy-lghi-vps.sh`) automatically creates a backup before deploying:

```bash
# Automatic backup format
instance/minipass_backup_YYYYMMDD_HHMMSS.db
```

### Manual Backups

Always create a manual backup before major operations:

```bash
# Create manual backup with timestamp
cp instance/minipass.db instance/minipass_backup_$(date +%Y%m%d_%H%M%S).db

# Verify backup was created
ls -lh instance/minipass_backup_*.db
```

### Backup Locations

- **LHGI backups**: `/home/kdresdell/minipass_env/app/instance/minipass_backup_*.db`
- **Customer backups**: `/home/kdresdell/minipass_env/deployed/{customer}/app/instance/minipass_backup_*.db`
- **API backups** (full system): `static/backups/` (includes database + uploads + templates + settings)

### Restoring from Backup

```bash
# Stop the container first
docker-compose down

# Restore database from backup
cp instance/minipass_backup_20250123_143022.db instance/minipass.db

# Start container
docker-compose up -d
```

### Backup Retention

**Recommended retention policy**:
- Keep 3 most recent backups
- Delete backups older than 30 days (except critical milestones)

```bash
# List all backups
ls -lht instance/minipass_backup_*.db

# Delete old backups (keep 3 most recent)
ls -t instance/minipass_backup_*.db | tail -n +4 | xargs rm -f
```

---

## Troubleshooting

### Container Won't Start

**Symptom**: Container exits immediately after starting

**Diagnosis**:
```bash
# Check container logs
docker logs lhgi --tail 100

# Check for port conflicts
docker ps | grep 8889
```

**Common causes**:
1. Port already in use → Change port in docker-compose.yml
2. Database file missing → Restore from backup
3. .env file missing → Upload .env file
4. Python dependency error → Rebuild with `--no-cache`

### Database Upgrade Failed

**Symptom**: Migration script shows ❌ errors

**Solution**:
1. Read the error message carefully
2. Script automatically rolls back - database is safe
3. Fix the underlying issue (e.g., data conflict)
4. Run script again (safe to re-run)
5. If persistent errors, restore from backup

### Version Mismatch

**Symptom**: Website shows old version or cached content

**Solution**:
```bash
# Rebuild with aggressive cache clearing
docker-compose down
docker system prune -af
docker-compose build --no-cache
docker-compose up -d
```

### Activity Pictures Missing After Upgrade

**Symptom**: Activity cover photos disappeared after upgrading container, showing blank/gray cards on dashboard

**Root Cause**: `static/uploads/` directory NOT mounted as Docker volume → container rebuild deletes all uploaded files

**Diagnosis**:
```bash
# Step 1: Check if database still has the image reference
ssh -p 2222 kdresdell@minipass.me
docker exec lhgi sqlite3 /app/instance/minipass.db \
  "SELECT id, name, image_filename FROM activity WHERE image_filename IS NOT NULL;"

# Step 2: Check if files exist in container
docker exec lhgi ls -la /app/static/uploads/activity_images/

# Step 3: Check if files exist on host
ls -la ~/minipass_env/app/static/uploads/activity_images/

# Step 4: Verify volume mount
grep -A 3 "volumes:" ~/minipass_env/docker-compose.yml | grep "static/uploads"
```

**What You'll See**:
- Database has `image_filename` value (e.g., "unsplash_xyz123.jpg")
- Container directory is empty or file missing
- Host may or may not have files (depends on when they were uploaded)
- Volume mount likely missing

**Solution**:
1. **Fix docker-compose.yml** (add volume mount):
   ```yaml
   volumes:
     - ./app/instance:/app/instance
     - ./app/static/uploads:/app/static/uploads  # ← ADD THIS
     - /etc/localtime:/etc/localtime:ro
   ```

2. **If files exist on host** (uploaded before last rebuild):
   ```bash
   # Restart container to mount the volume
   cd ~/minipass_env
   docker-compose down
   docker-compose up -d lhgi
   # Pictures should reappear!
   ```

3. **If files don't exist on host** (deleted by previous rebuild):
   - Ask user to re-upload pictures via Edit Activity page
   - OR restore from backup if you have one

**Prevention**: ALWAYS verify volume mounts before rebuilding containers!

### Images Not Displaying (General)

**Symptom**: QR codes or uploaded images show broken links

**Common causes**:
1. Uploads folder not transferred (customer deployments) → Run Step 7 again (scp uploads)
2. Volume mount missing → See "Activity Pictures Missing" above
3. File permissions wrong → Fix permissions:
   ```bash
   chmod -R 755 app/static/uploads
   chown -R www-data:www-data app/static/uploads
   ```

### Port Conflicts

**Symptom**: Container fails to start with "port already in use"

**Solution**:
```bash
# Find what's using the port
sudo lsof -i :8889

# Kill the process or change port in docker-compose.yml
```

### Cannot Connect to Database

**Symptom**: Flask app shows "cannot connect to database"

**Common causes**:
1. Database file missing → Restore from backup
2. Database file corrupted → Restore from backup
3. File permissions wrong → Fix permissions:
   ```bash
   chmod 644 instance/minipass.db
   chown www-data:www-data instance/minipass.db
   ```

---

## Emergency Rollback

### Automatic Rollback

The migration script automatically rolls back on any error. No manual intervention needed.

### Manual Rollback

If you need to manually rollback to a previous version:

#### Step 1: Stop Container
```bash
docker-compose down
```

#### Step 2: Restore Database from Backup
```bash
# List available backups
ls -lht instance/minipass_backup_*.db

# Restore from specific backup
cp instance/minipass_backup_20250123_143022.db instance/minipass.db
```

#### Step 3: Rollback Code (if needed)
```bash
# For LHGI (git-based)
git reset --hard HEAD~1

# For customers (re-clone previous version)
git checkout {previous_commit_hash}
```

#### Step 4: Rebuild and Start
```bash
docker-compose build --no-cache
docker-compose up -d
```

#### Step 5: Verify
```bash
docker logs lhgi --tail 50
# Visit website and verify it's working
```

---

## Architecture Reference

### Directory Structure

```
minipass_env/
├── .env                           # Shared .env file (Stripe, API keys)
├── docker-compose.yml             # Main services (nginx, mail, lhgi)
├── deploy-lghi-vps.sh            # LHGI deployment script
├── app/                          # LHGI application
│   ├── instance/
│   │   └── minipass.db           # LHGI database
│   ├── migrations/
│   │   └── upgrade_production_database.py
│   └── static/
│       └── uploads/              # LHGI uploads
└── deployed/                     # Customer deployments
    └── {customer}/               # e.g., heq/
        ├── docker-compose.yml    # Customer-specific compose
        └── app/                  # Customer app (git clone)
            ├── instance/
            │   └── minipass.db   # Customer database
            └── static/
                └── uploads/      # Customer uploads
```

### Container Setup

#### LHGI Container
```yaml
lhgi:
  container_name: lhgi
  build:
    context: ./app
  restart: always
  env_file:
    - .env                        # Shared .env at root level
  environment:
    - FLASK_ENV=prod
    - VIRTUAL_HOST=lhgi.minipass.me
    - VIRTUAL_PORT=8889
  volumes:
    - ./app/instance:/app/instance                 # Database (CRITICAL)
    - ./app/static/uploads:/app/static/uploads     # User uploads (CRITICAL)
    - /etc/localtime:/etc/localtime:ro             # Timezone
```

**⚠️ CRITICAL**: Both `instance` and `static/uploads` MUST be mounted as volumes!
- Missing `instance` mount → Database gets deleted on rebuild
- Missing `static/uploads` mount → All uploaded images get deleted on rebuild

#### Customer Container (HEQ example)
```yaml
services:
  flask-app:
    container_name: minipass_heq
    build:
      context: ./app
    env_file:
      - ../../.env                # Shared .env at root level
    environment:
      - FLASK_ENV=dev
      - ADMIN_EMAIL=customer@example.com
      - ADMIN_PASSWORD=their_password
      - ORG_NAME=Customer Organization
      - VIRTUAL_HOST=heq.minipass.me
    volumes:
      - ./app/instance:/app/instance                 # Database (CRITICAL)
      - ./app/static/uploads:/app/static/uploads     # User uploads (CRITICAL)
```

**Note**: Future customer deployments will automatically include the `static/uploads` mount (deploy_helpers.py has been updated). Existing customers may need manual docker-compose.yml updates.

### Git Strategy

**LHGI (Prototype)**:
- Git pull in place
- Force reset to main branch: `git reset --hard origin/main`
- Database in .gitignore (safe from git operations)

**Customers (Production)**:
- Fresh git clone each deployment: `rm -rf app && git clone`
- Database transferred via SCP (tested locally first)
- Uploads transferred via SCP

### .env Configuration

**Location**: `/home/kdresdell/minipass_env/.env` (shared by all containers)

**Key Variables**:
```bash
# Stripe Configuration (NEW)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_CUSTOMER_ID=cus_...
STRIPE_SUBSCRIPTION_ID=sub_...
PAYMENT_AMOUNT=72000
SUBSCRIPTION_RENEWAL_DATE=2026-11-22T19:36:23.270580

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key
FLASK_ENV=prod

# Tier Configuration
MINIPASS_TIER=3
BILLING_FREQUENCY=annual

# API Keys
GOOGLE_MAPS_API_KEY=...
GOOGLE_AI_API_KEY=...
GROQ_API_KEY=...
UNSPLASH_ACCESS_KEY=...

# Chatbot Configuration
CHATBOT_ENABLE_GEMINI=true
CHATBOT_ENABLE_GROQ=true
CHATBOT_ENABLE_OLLAMA=false
CHATBOT_DAILY_BUDGET_CENTS=1000
CHATBOT_MONTHLY_BUDGET_CENTS=10000
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Code pushed to main branch
- [ ] Code tested locally on localhost:5000
- [ ] Database migration tested locally (for customers)
- [ ] .env file updated with latest variables
- [ ] All tests passing
- [ ] No uncommitted changes

### During Deployment

**For LHGI**:
- [ ] Connected to VPS via SSH
- [ ] Pulled latest code (git reset --hard)
- [ ] Updated .env file (if needed)
- [ ] Container stopped (docker-compose stop lhgi)
- [ ] Ran database migration (all 17 tasks ✅)
- [ ] Cleared Docker cache (docker system prune)
- [ ] Tagged backup image
- [ ] Built new container (--no-cache)
- [ ] Started container (docker-compose up -d)
- [ ] Container verified running

**For Customer Upgrade (HEQ, etc.)**:
- [ ] Connected to VPS via SSH
- [ ] Navigated to customer directory
- [ ] Backed up database to HOME directory (~/heq_backup_*.db)
- [ ] Backed up uploads to HOME directory (~/heq_uploads_backup_*)
- [ ] Stopped container (docker-compose down)
- [ ] Updated code (git reset --hard origin/main)
- [ ] Restored database from HOME directory
- [ ] Restored uploads from HOME directory
- [ ] Updated .env file (if needed)
- [ ] Ran database migration script (17 tasks ✅)
- [ ] Verified docker-compose.yml volume mounts
- [ ] Rebuilt container (--no-cache)
- [ ] Started container (docker-compose up -d)
- [ ] Verified activity pictures still display

### Post-Deployment

- [ ] Container shows "Up X minutes" in docker ps
- [ ] No errors in container logs
- [ ] Website loads correctly
- [ ] Login works correctly
- [ ] QR codes display correctly
- [ ] Images/uploads display correctly
- [ ] Payment processing works (if applicable)
- [ ] Email sending works (if applicable)
- [ ] Notified customer of deployment (for customers)

### If Something Goes Wrong

- [ ] Check container logs: `docker logs {container} --tail 100`
- [ ] Check database migration output for ❌ errors
- [ ] Restore from automatic backup if needed
- [ ] Contact developer if persistent issues

---

## Quick Reference Commands

### Container Management
```bash
# Check running containers
docker ps

# Check all containers (including stopped)
docker ps -a

# View container logs
docker logs lhgi --tail 50
docker logs lhgi -f          # Follow logs in real-time

# Restart container
docker restart lhgi

# Stop container
docker-compose down

# Start container
docker-compose up -d

# Rebuild container
docker-compose build --no-cache
docker-compose up -d
```

### Database Operations
```bash
# Run migration script
python3 migrations/upgrade_production_database.py
# Then run the sqlite3 command the script tells you
# OR if Flask is installed: flask db stamp head

# Create manual backup
cp instance/minipass.db instance/minipass_backup_$(date +%Y%m%d_%H%M%S).db

# List backups
ls -lht instance/minipass_backup_*.db

# Restore from backup
cp instance/minipass_backup_20250123_143022.db instance/minipass.db
```

### File Transfers
```bash
# Upload .env file to VPS
scp -P 2222 /home/kdresdell/Documents/DEV/minipass_env/app/.env kdresdell@minipass.me:/home/kdresdell/minipass_env/.env

# Upload database to VPS (customer deployment)
scp -P 2222 /home/kdresdell/Documents/DEV/minipass_env/app/instance/minipass.db kdresdell@minipass.me:/home/kdresdell/minipass_env/deployed/heq/app/instance/

# Upload uploads folder to VPS (customer deployment)
scp -r -P 2222 /home/kdresdell/Documents/DEV/minipass_env/app/static/uploads/* kdresdell@minipass.me:/home/kdresdell/minipass_env/deployed/heq/app/static/uploads/
```

### Git Operations
```bash
# Update LHGI code
git fetch origin
git reset --hard origin/main

# Clone fresh code (customer deployment)
rm -rf app
git clone https://github.com/kdresdell/minipass.git app
cd app
git checkout main
```

---

## Support

If you encounter issues not covered in this guide:

1. Check the troubleshooting section above
2. Review container logs for detailed error messages
3. Ensure all prerequisites are met
4. Contact developer with specific error messages and steps to reproduce

---

**Last Updated**: January 2025
**Replaces**: QUICK_DEPLOY_LHGI.md, AUTO_DEPLOY_CUSTOMER.md, VPS_DEPLOYMENT_GUIDE.md
**Archived**: PRODUCTION_UPGRADE_GUIDE.md (specific one-time migration)