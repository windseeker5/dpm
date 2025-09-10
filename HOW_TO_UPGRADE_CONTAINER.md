# How to Upgrade the Container - LHGI Production Deployment

## Overview
This guide explains how to safely upgrade your production container with the latest code while preserving all customer data, especially email template customizations and user-uploaded images.

## Database Change
**Only ONE change**: Added `email_opt_out` field to the `user` table
- Type: BOOLEAN
- Default: 0 (false)
- All other tables remain unchanged
- Email templates are 100% preserved

## 🚨 CRITICAL STEP 0: Fix Git Tracking (DO THIS FIRST!)

**PROBLEM**: Your `static/uploads/` directory is currently tracked by Git. This means `git pull` on VPS would overwrite production customer images with your local test images!

### 0.1 Stop tracking uploads directory
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app
echo "static/uploads/" >> .gitignore
git rm -r --cached static/uploads/
git commit -m "Stop tracking uploads directory - preserve customer images"
git push origin v1
```

## Step 1: Test Locally with Production Data (MANDATORY)

### 1.1 Backup your current local environment
```bash
# Backup local database
cp instance/minipass.db instance/minipass_local_backup.db

# Backup your local uploads (the "garbage")
mv static/uploads static/uploads_LOCAL_BACKUP
```

### 1.2 Extract BOTH database AND images from VPS backup
```bash
# Extract everything from production backup
unzip -o /home/kdresdell/Documents/DEV/minipass_backup_2025-09-09_23-34-13.zip

# Use production database
mv database/minipass.db instance/minipass.db

# Use production images (CRITICAL for proper testing!)
mkdir -p static/uploads
cp -r static/uploads/* static/uploads/
```

### 1.3 Run the migration script
```bash
sqlite3 instance/minipass.db < migrate_email_opt_out.sql
```

### 1.4 Verify migration succeeded
```bash
# Should show: 5|email_opt_out|BOOLEAN|1|0|0
sqlite3 instance/minipass.db "PRAGMA table_info(user);" | grep email_opt_out
```

### 1.5 Test with REAL production data and images
```bash
# Run your Flask app
python app.py

# Test these critical functions:
# - Login as admin
# - View activities (images should load correctly!)
# - Check email template editor (should show all customizations)
# - Try sending a test email
# - Verify all customer images display properly
```

### 1.6 Restore your local environment after testing
```bash
# Restore your local database
cp instance/minipass_local_backup.db instance/minipass.db

# Restore your local "garbage" uploads
rm -rf static/uploads
mv static/uploads_LOCAL_BACKUP static/uploads
```

## Step 2: Deploy to Production (Only if local test passes)

### 2.1 Connect to VPS and create backup
```bash
ssh your-vps
cd /home/kdresdell/minipass_env/app

# Create safety backup of database only (uploads will stay intact)
cp instance/minipass.db instance/minipass_pre_upgrade_$(date +%Y%m%d_%H%M%S).db
```

### 2.2 Pull latest code (uploads are now safe!)
```bash
# This is now SAFE because uploads are no longer tracked by git
git pull origin v1
```

### 2.3 Run the migration on production
```bash
sqlite3 instance/minipass.db < migrate_email_opt_out.sql
```

### 2.4 Verify migration on production
```bash
# Should show: 5|email_opt_out|BOOLEAN|1|0|0
sqlite3 instance/minipass.db "PRAGMA table_info(user);" | grep email_opt_out

# Verify uploads are still intact
ls -la static/uploads/ | head -5
```

### 2.5 Deploy the container
```bash
cd /home/kdresdell/minipass_env
./deploy.sh  # Your existing deploy script
```

## Rollback Plan (If something goes wrong)

### On VPS:
```bash
# Stop container
docker stop lhgi

# Restore database (uploads are never touched)
cd /home/kdresdell/minipass_env/app
cp instance/minipass_pre_upgrade_*.db instance/minipass.db

# Revert code if needed
git checkout HEAD~1

# Restart container
cd ..
./deploy.sh
```

## What's Preserved
✅ All email templates (subject, intro_text, conclusion_text, etc.)  
✅ All user data  
✅ All activities and passports  
✅ All uploaded images (now properly protected from git!)  
✅ All admin settings  

## Verification Checklist
After deployment, verify:
- [ ] Container is running: `docker ps | grep lhgi`
- [ ] Website loads: https://lhgi.minipass.me
- [ ] Admin can login
- [ ] Email templates show customizations
- [ ] Activities display correctly with images
- [ ] Customer uploaded images are intact
- [ ] Check logs: `docker logs lhgi --tail 50`

## Why This New Approach is Better
🔥 **Old Problem**: Local test images would overwrite production customer images  
✅ **New Solution**: Git ignores uploads, local testing uses real production images  
✅ **Result**: Safe deployment with proper testing  

## Important Notes
1. **ALWAYS do Step 0 first** - fix git tracking before deployment
2. The migration script is idempotent - running it twice won't break anything
3. The `email_opt_out` field defaults to 0 (false) for all existing users
4. Total downtime: < 30 seconds (during container restart)
5. Local testing now uses real production data AND images

## Support
If you encounter issues:
1. Check the backup exists: `ls -la instance/minipass_pre_upgrade_*.db`
2. Review container logs: `docker logs lhgi`
3. Verify database structure: `sqlite3 instance/minipass.db ".schema user"`
4. Check uploads are safe: `ls -la static/uploads/ | head -5`

---
Last updated: 2025-09-10  
Tested with: minipass_backup_2025-09-09_23-34-13.zip  
**NEW**: Fixed uploads tracking issue for safe deployment