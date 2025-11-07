# Auto-Deploy Customer Guide

**⏱️ Time: 5-7 minutes | 📋 For auto-deployed customers like HEQ**

---

## 🎯 Prerequisites

This guide assumes you have already:
- Downloaded the customer's live database backup to your local dev environment
- Imported and tested the database locally at `/home/kdresdell/Documents/DEV/minipass_env/app/instance/minipass.db`
- Run database upgrades locally and verified everything works
- Tested the application with the customer's data on `localhost:5000`
- Verified the upload folder is in sync at `/home/kdresdell/Documents/DEV/minipass_env/app/static/upload/`

**If you haven't done local testing yet, STOP and do that first!**

---

## 🚀 Git-Based Customer Deployment (7 Steps)

### 1️⃣ Connect to VPS & Navigate to Customer
```bash
ssh kdresdell@minipass.me -p 2222
cd /home/kdresdell/minipass_env/deployed/{CUSTOMER_NAME}

# Example for HEQ:
cd /home/kdresdell/minipass_env/deployed/heq
```

### 2️⃣ Stop Container (SAFETY FIRST!)
```bash
docker-compose down
```

**Expected Output:** 🛑 Container stopped gracefully

### 3️⃣ Backup Current Database
```bash
# Backup customer's current database (safety net)
cp app/instance/minipass.db app/instance/minipass_backup_$(date +%Y%m%d_%H%M%S).db

# Verify backup was created
ls -lh app/instance/minipass_backup_*.db | tail -1
```

**Expected Output:** Database backup created with timestamp

### 4️⃣ Clone Fresh Code from Git
```bash
# Remove old app code completely
rm -rf app_old 2>/dev/null || true
rm -rf app

# Clone fresh from main branch (using VPS git repo as source)
git clone /home/kdresdell/minipass_env/app ./app

# Navigate into app directory
cd app
```

**Expected Output:**
- Old app folder removed
- Fresh code cloned from Git main branch

### 5️⃣ SCP Database from Local Dev
```bash
# Exit from app/ directory back to customer root
cd ..

# On your LOCAL machine (in a new terminal):
# SCP upgraded database from local dev to VPS
scp -P 2222 /home/kdresdell/Documents/DEV/minipass_env/app/instance/minipass.db \
    kdresdell@minipass.me:/home/kdresdell/minipass_env/deployed/{CUSTOMER_NAME}/app/instance/minipass.db

# Example for HEQ:
scp -P 2222 /home/kdresdell/Documents/DEV/minipass_env/app/instance/minipass.db \
    kdresdell@minipass.me:/home/kdresdell/minipass_env/deployed/heq/app/instance/minipass.db
```

**Expected Output:** Database transferred successfully

### 6️⃣ SCP Upload Folder from Local Dev
```bash
# Still on LOCAL machine:
# SCP upload folder from local dev to VPS (complete replacement)
scp -P 2222 -r /home/kdresdell/Documents/DEV/minipass_env/app/static/upload \
    kdresdell@minipass.me:/home/kdresdell/minipass_env/deployed/{CUSTOMER_NAME}/app/static/

# Example for HEQ:
scp -P 2222 -r /home/kdresdell/Documents/DEV/minipass_env/app/static/upload \
    kdresdell@minipass.me:/home/kdresdell/minipass_env/deployed/heq/app/static/
```

**Expected Output:** Upload folder transferred successfully

**Now return to your VPS SSH session**

### 7️⃣ Rebuild and Start Container
```bash
# Back on VPS in the customer directory
# Rebuild with new code (no cache to ensure fresh build)
docker-compose build --no-cache
docker-compose up -d
```

**Expected Output:**
- 🔨 Building new image (may take 1-2 minutes)
- 🚀 Container started successfully

---

## 🔍 Verify Success

### Check Container Status
```bash
# Check if container is running
docker-compose ps

# Check container logs (look for Flask startup messages)
docker-compose logs -f --tail 50

# Should see: "Running on http://0.0.0.0:5000"
```

### Test in Browser
```bash
# Test customer site
curl -I https://{CUSTOMER_NAME}.minipass.me

# Example: https://heq.minipass.me
# Expected: HTTP/1.1 200 OK or 302 redirect
```

**Manual verification**: Open browser and test key functionality:
- Login page loads
- Dashboard displays correctly
- Customer data appears as expected

---

## 🆘 If Something Goes Wrong

### Container won't start?
```bash
# Check logs for errors
docker-compose logs --tail 100

# Common issues:
# - Python dependencies missing (check requirements.txt)
# - Database connection issues (check instance/ folder)
# - Port conflicts (check docker-compose.yml)
```

### Database issues?
```bash
# Restore from timestamped backup
cp app/instance/minipass_backup_YYYYMMDD_HHMMSS.db app/instance/minipass.db
docker-compose down && docker-compose up -d
```

### Need to rollback completely?
```bash
# Re-clone and restore old database
rm -rf app
git clone /home/kdresdell/minipass_env/app ./app
cp app/instance/minipass_backup_YYYYMMDD_HHMMSS.db app/instance/minipass.db
docker-compose build --no-cache
docker-compose up -d
```

### SCP transfer failed?
```bash
# Verify SSH connection
ssh kdresdell@minipass.me -p 2222

# Check local file exists
ls -lh /home/kdresdell/Documents/DEV/minipass_env/app/instance/minipass.db

# Check remote directory exists
ssh kdresdell@minipass.me -p 2222 "ls -la /home/kdresdell/minipass_env/deployed/{CUSTOMER}/app/instance/"
```

---

## 📝 Customer Directory Structure

```
/deployed/{CUSTOMER_NAME}/
├── docker-compose.yml     # Customer-specific compose file
├── app/                   # Customer's app code (CLONED from Git, fresh each deploy)
│   ├── instance/
│   │   ├── minipass.db                        # Customer's database (transferred from local)
│   │   └── minipass_backup_YYYYMMDD_*.db      # Timestamped backups
│   ├── static/
│   │   └── upload/        # Customer uploads (transferred from local)
│   ├── dockerfile         # Customer's Dockerfile
│   └── [rest of app files from Git]
```

---

## 🔄 Deployment Comparison

| Type | Location | Deployment Method | Git Source |
|------|----------|------------------|------------|
| **LHGI (Prototype)** | `/home/kdresdell/minipass_env/app` | `./deploy-lghi-vps.sh` | Git pull in place |
| **Customers (HEQ, etc)** | `/deployed/{customer}/` | This guide (Auto-deploy) | Fresh git clone |
| **Local Dev** | `/home/kdresdell/Documents/DEV/minipass_env/app` | Manual testing | Git development |

---

## ⚠️ Important Notes

### Safety Features
- ✅ Database tested locally BEFORE deployment
- ✅ Automatic timestamped backup on VPS before changes
- ✅ Fresh git clone ensures clean code (no corruption)
- ✅ No-cache build prevents Docker caching issues
- ✅ Customer data preserved in docker-compose.yml

### Git-Based Workflow
- ✅ Each deployment gets fresh code from Git main branch
- ✅ No manual copying - Git guarantees code consistency
- ✅ Source is `/home/kdresdell/minipass_env/app` (VPS git repo)
- ✅ Database and uploads come from tested local dev environment

### Database Safety
- ✅ Database upgraded and tested locally first
- ✅ SCP transfers verified database to VPS
- ✅ Upload folder synchronized from local dev
- ✅ Git never touches instance/ or static/upload/ (in .gitignore)

### Container Management
- ⚠️ MUST test database locally before deploying
- ⚠️ MUST stop container before replacing app folder
- ⚠️ MUST use --no-cache to prevent stale Docker layers
- ⚠️ Each customer is independent - deploy one at a time

---

## 🎯 Current Deployed Customers

### HEQ (Hockey Est du Quebec)
- **URL**: https://heq.minipass.me
- **Location**: `/home/kdresdell/minipass_env/deployed/heq/`
- **Container**: `minipass_heq`

---

## 🔗 Quick Reference Commands

### Check Main Git Repo Status
```bash
# On VPS - check source git repo version
cd /home/kdresdell/minipass_env/app
git log -1 --oneline
git status

# Pull latest changes to VPS git repo (do this before customer deployments)
git fetch origin main && git reset --hard origin/main
```

### List All Customers
```bash
# List deployed customer directories
ls -la /home/kdresdell/minipass_env/deployed/

# Check all customer containers
docker ps | grep minipass_

# Check specific customer logs
cd /home/kdresdell/minipass_env/deployed/{CUSTOMER}
docker-compose logs -f --tail 50
```

### Local Dev Testing Commands
```bash
# On LOCAL machine - verify database before SCP
cd /home/kdresdell/Documents/DEV/minipass_env/app
source venv/bin/activate
python migrations/upgrade_production_database.py
flask db stamp head

# Test on localhost:5000 (Flask already running in debug mode)
curl http://localhost:5000/

# Check upload folder exists
ls -la static/upload/
```

---

## 🚨 Emergency Contacts

- **Developer**: Ken Dresdell (kdresdell@gmail.com)
- **VPS Access**: `ssh kdresdell@minipass.me -p 2222`
- **Git Repository**: `/home/kdresdell/minipass_env/app` (VPS) and GitHub
- **Infrastructure**: Nginx proxy + Let's Encrypt + Mail server

---

## 📚 Related Documents

- **QUICK_DEPLOY_LHGI.md** - LHGI prototype deployment (different workflow)
- **VPS_DEPLOYMENT_GUIDE.md** - Full VPS infrastructure guide
- **DEPLOYMENT.md** - First-time customer container setup
- **ENV_SETUP.md** - API keys and environment variables
