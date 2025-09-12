# How to Deploy Bug Fixes - LHGI Production Deployment

## Simple 2-Step Process

You've already:
- ✅ Fixed bugs locally with production database
- ✅ Tested everything works
- ✅ Committed and pushed to git (database included)

Now just deploy:

---

## Step 1: Push Your Changes (Local)

```bash
# On your local development machine
cd /home/kdresdell/Documents/DEV/minipass_env/app

# Commit your changes (including the database)
git add -A
git commit -m "Fix [describe your fixes] - includes updated database"
git push origin v1
```

---

## Step 2: Deploy on VPS

### 2.1 Connect to VPS and Navigate
```bash
# SSH to your VPS
ssh your-vps
cd /home/kdresdell/minipass_env/app
```

### 2.2 Force Pull Latest Changes (Solves Git Issues)
```bash
# This handles any staging/conflict issues you mentioned
git fetch origin v1
git reset --hard origin/v1

# This ensures you get the exact database from git, not keeping local VPS database
```

### 2.3 Deploy the Container
```bash
# Go back to deploy directory and run your deploy script
cd /home/kdresdell/minipass_env
./deploy-lghi-vps.sh
```

### 2.4 Verify Success
The deploy script will automatically:
- ✅ Build new container
- ✅ Start container
- ✅ Verify it's running at https://lhgi.minipass.me
- ✅ Rollback if anything fails

---

## Why This Works

### Git Strategy
- **Database IS in git** - intentional
- **`git reset --hard origin/v1`** - forces VPS to match git exactly
- **No local VPS changes preserved** - git version is the truth

### Deploy Script
Your `deploy-lghi-vps.sh` already:
- Creates database backup for safety
- Rebuilds container with no cache
- Verifies deployment
- Rolls back automatically if issues

---

## If Git Pull Still Has Issues

Try this more aggressive approach:

```bash
# SSH to VPS
ssh your-vps
cd /home/kdresdell/minipass_env/app

# Nuclear option - completely reset to match git
git fetch origin
git checkout v1
git reset --hard origin/v1
git clean -fd

# Then deploy
cd ../
./deploy-lghi-vps.sh
```

---

## Total Time: ~5 Minutes
- Push changes: 30 seconds
- SSH to VPS: 30 seconds  
- Git pull: 30 seconds
- Deploy script: 3-4 minutes
- Done! ✅

---

**Last Updated**: 2025-09-12  
**Process**: Local push → VPS git pull → Deploy script → Live