# Migration Workflow - Import Production Data from VPS

## Overview
This workflow imports production data from your friend's VPS backup (1 week old) into your latest development version, handling the 2 new database fields that were added since the backup was created.

## Database Differences Found
- **Activity table** has 2 new fields in current version:
  - `email_templates` (TEXT) - For custom email configurations
  - `logo_filename` (VARCHAR 255) - For activity-specific logos

## Data to Import
- 3 Activities
- 2 Admin accounts  
- 32 Passports
- 34 Users
- 7 Signups
- Plus all related data and uploaded images

---

## Step-by-Step Migration Process

### Step 1: Save Your Current Work
```bash
git add -A
git commit -m "Backup before importing production data"
```
*This saves everything you have now as a safety backup*

### Step 2: Reset Your Database
1. Open your browser
2. Go to `http://localhost:5000`
3. Login to your app
4. Go to **Settings** → **Your Data** → **Reset Database**
5. Click Reset (this will keep your admin password but clear all data)

### Step 3: Create Migration Script
Create a file called `migrate.sh` with this content:

```bash
#!/bin/bash

echo "🚀 Starting migration..."

# Extract backup
echo "📦 Extracting your friend's backup..."
mkdir -p /tmp/migration
tar -xzf /home/kdresdell/minipass_app_backup_20250902_220450.tgz -C /tmp/migration/

# Import all the data
echo "📊 Importing database..."
sqlite3 instance/minipass.db << 'EOF'
ATTACH DATABASE '/tmp/migration/app/instance/minipass.db' AS old;

-- Copy everything from your friend's database
-- Note: Adding NULL, NULL for the 2 new fields in activity table
INSERT INTO activity SELECT *, NULL, NULL FROM old.activity;
INSERT INTO admin SELECT * FROM old.admin;
INSERT INTO passport SELECT * FROM old.passport;
INSERT INTO passport_type SELECT * FROM old.passport_type;
INSERT INTO signup SELECT * FROM old.signup;
INSERT INTO user SELECT * FROM old.user;
INSERT INTO income SELECT * FROM old.income;
INSERT INTO expense SELECT * FROM old.expense;
INSERT INTO survey SELECT * FROM old.survey;
INSERT INTO survey_response SELECT * FROM old.survey_response;
INSERT INTO survey_template SELECT * FROM old.survey_template;
INSERT INTO redemption SELECT * FROM old.redemption;

DETACH DATABASE old;
EOF

# Fix the 2 missing fields with default values
echo "🔧 Setting default values for new fields..."
sqlite3 instance/minipass.db << 'EOF'
UPDATE activity SET email_templates = '{}' WHERE email_templates IS NULL;
UPDATE activity SET logo_filename = NULL WHERE logo_filename IS NULL;
EOF

# Copy all uploaded images and files
echo "🖼️ Copying uploaded files..."
cp -r /tmp/migration/app/static/uploads/* static/uploads/

# Clean up temporary files
rm -rf /tmp/migration

echo "✅ MIGRATION COMPLETE! Go test your app at http://localhost:5000"
```

### Step 4: Run the Migration Script
```bash
chmod +x migrate.sh
./migrate.sh
```

### Step 5: Test Everything
1. Go to `http://localhost:5000`
2. Login with your friend's admin account
3. Verify:
   - [ ] All 3 activities are visible
   - [ ] All 32 passports are there
   - [ ] All 34 users are imported
   - [ ] Activity images are displaying correctly
   - [ ] You can create new passports
   - [ ] Email templates work (test sending)

### Step 6: Commit and Push to GitHub
If everything works correctly:
```bash
git add -A
git commit -m "Import production data from VPS - 3 activities, 32 passports, 34 users"
git push
```

### Step 7: Deploy to VPS
```bash
# SSH into your VPS
ssh your-vps

# Navigate to app directory
cd /path/to/your/app

# Pull latest changes
git pull

# Restart your application (adjust based on your setup)
systemctl restart minipass
# or
pm2 restart minipass
# or however you restart your app
```

---

## Rollback Plan (If Something Goes Wrong)

### Option 1: Git Rollback (if not pushed yet)
```bash
git reset --hard HEAD~1
```

### Option 2: Restore from backup (if already pushed)
```bash
# On VPS
git reset --hard HEAD~1
git push --force
```

### Option 3: Full restore
Keep your original backup file safe: `/home/kdresdell/minipass_app_backup_20250902_220450.tgz`

---

## Important Notes

1. **Admin Accounts**: The migration imports your friend's admin accounts. Make note of the credentials.

2. **Email Templates**: New activities will have empty email templates `{}`. You may want to set up proper templates after migration.

3. **Images**: All uploaded images from `static/uploads/` will be copied, including:
   - Activity images
   - Email logos
   - Any other uploaded content

4. **Database Reset**: The reset function in Settings preserves only the admin account settings, everything else is cleared before import.

5. **Testing**: Always test locally before pushing to production VPS.

---

## Files Involved
- Backup file: `/home/kdresdell/minipass_app_backup_20250902_220450.tgz`
- Database: `instance/minipass.db`
- Uploads: `static/uploads/`
- Migration script: `migrate.sh` (create this)

---

*Generated: January 3, 2025*