# How to Upgrade the Container - LHGI Production Deployment

## Overview
This guide explains how to safely upgrade your production container with the latest code while preserving all customer data, especially email template customizations.

## Database Change
**Only ONE change**: Added `email_opt_out` field to the `user` table
- Type: BOOLEAN
- Default: 0 (false)
- All other tables remain unchanged
- Email templates are 100% preserved

## Step 1: Test Locally First (MANDATORY)

### 1.1 Backup your current local database
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app
cp instance/minipass.db instance/minipass_local_backup.db
```

### 1.2 Replace with production database from backup
```bash
# Extract the production database from your backup
unzip -o /home/kdresdell/Documents/DEV/minipass_backup_2025-09-09_23-34-13.zip database/minipass.db
mv database/minipass.db instance/minipass.db
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

### 1.5 Test the application locally
```bash
# Run your Flask app
python app.py

# Test these critical functions:
# - Login as admin
# - View activities
# - Check email template editor (should show all customizations)
# - Try sending a test email
```

## Step 2: Deploy to Production (Only if local test passes)

### 2.1 Push code to Git repository
```bash
git add .
git commit -m "Add email opt-out feature with database migration"
git push origin v1
```

### 2.2 Connect to VPS and prepare
```bash
ssh your-vps
cd /home/kdresdell/minipass_env/app

# Create safety backup
cp instance/minipass.db instance/minipass_pre_upgrade_$(date +%Y%m%d_%H%M%S).db
```

### 2.3 Pull latest code
```bash
git pull origin v1
```

### 2.4 Run the migration on production
```bash
sqlite3 instance/minipass.db < migrate_email_opt_out.sql
```

### 2.5 Verify migration on production
```bash
# Should show: 5|email_opt_out|BOOLEAN|1|0|0
sqlite3 instance/minipass.db "PRAGMA table_info(user);" | grep email_opt_out
```

### 2.6 Deploy the container
```bash
cd /home/kdresdell/minipass_env
./deploy.sh  # Your existing deploy script
```

## Rollback Plan (If something goes wrong)

### On VPS:
```bash
# Stop container
docker stop lhgi

# Restore database
cd /home/kdresdell/minipass_env/app
cp instance/minipass_pre_upgrade_*.db instance/minipass.db

# Revert code
git checkout HEAD~1

# Restart container
cd ..
./deploy.sh
```

## What's Preserved
✅ All email templates (subject, intro_text, conclusion_text, etc.)  
✅ All user data  
✅ All activities and passports  
✅ All uploaded images  
✅ All admin settings  

## Verification Checklist
After deployment, verify:
- [ ] Container is running: `docker ps | grep lhgi`
- [ ] Website loads: https://lhgi.minipass.me
- [ ] Admin can login
- [ ] Email templates show customizations
- [ ] Activities display correctly
- [ ] Check logs: `docker logs lhgi --tail 50`

## Important Notes
1. The migration script is idempotent - running it twice won't break anything
2. The `email_opt_out` field defaults to 0 (false) for all existing users
3. Total downtime: < 30 seconds (during container restart)
4. Always test locally first with production data

## Support
If you encounter issues:
1. Check the backup exists: `ls -la instance/minipass_pre_upgrade_*.db`
2. Review container logs: `docker logs lhgi`
3. Verify database structure: `sqlite3 instance/minipass.db ".schema user"`

---
Last updated: 2025-09-10
Tested with: minipass_backup_2025-09-09_23-34-13.zip