# Quick Deploy Reference - LHGI Container

**⏱️ Time: 5-7 minutes | 📖 Full Guide: VPS_DEPLOYMENT_GUIDE.md**

---

## 🚀 Standard LHGI Deployment (5 Steps)

### 1️⃣ Push Code (Local Machine)
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app
git add -A
git commit -m "Your changes description"
git push origin main
```

### 2️⃣ Connect to VPS & Pull Code
```bash
ssh kdresdell@minipass.me -p 2222
cd /home/kdresdell/minipass_env/app
git fetch origin main && git reset --hard origin/main
```

### 3️⃣ Upgrade Database (CRITICAL!)
```bash
# Still in app/ directory
python3 migrations/upgrade_production_database.py
flask db stamp head
cd ..
```

**Expected Output:** 8 tasks with ✅ checkmarks (or ⏭️ if already done)

### 4️⃣ Deploy Container
```bash
# Now in minipass_env/ directory
./deploy-lghi-vps.sh
```

**Expected Output:**
- 💾 Database backup created
- 🔨 Building new image
- 🚀 Starting container
- ✅ Container is running

### 5️⃣ Verify Success
```bash
# Check status
docker ps | grep lhgi

# Check logs (optional)
docker logs lhgi --tail 50

# Test in browser
# https://lhgi.minipass.me
```

---

## 🆘 If Something Goes Wrong

**Container won't start?**
```bash
docker logs lhgi
# Look for Python errors or missing dependencies
```

**Database upgrade failed?**
```bash
# Don't worry - automatic rollback happened
# Database is unchanged (safe)
# Check error message and fix issue
```

**Need to rollback?**
```bash
# Script does this automatically
# If manual rollback needed, see VPS_DEPLOYMENT_GUIDE.md section "Rollback Procedure"
```

---

## 📝 Notes

- ✅ Database is SAFE - it's in .gitignore (git cannot touch it)
- ✅ Automatic backup created before each deploy
- ✅ Idempotent upgrade script (safe to run multiple times)
- ✅ Automatic rollback on failure
- ⚠️ MUST run database upgrade BEFORE deploying container

---

## 🔗 Related Documents

- **VPS_DEPLOYMENT_GUIDE.md** - Full deployment guide with troubleshooting
- **DEPLOYMENT.md** - First-time VPS setup (not for updates)
- **ENV_SETUP.md** - API keys setup (one-time only)
