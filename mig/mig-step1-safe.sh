#!/bin/bash

echo "🚀 Starting migration..."

# Extract backup
echo "📦 Extracting your friend's backup..."
mkdir -p /tmp/migration
tar -xzf /home/kdresdell/minipass_app_backup_20250902_220450.tgz -C /tmp/migration/

# Backup current database first
echo "💾 Backing up current database..."
cp ../instance/minipass.db ../instance/minipass_backup_$(date +%Y%m%d_%H%M%S).db

# Clear existing data and import new data
echo "📊 Clearing existing data and importing fresh database..."
sqlite3 ../instance/minipass.db << 'EOF'
ATTACH DATABASE '/tmp/migration/app/instance/minipass.db' AS old;

-- Clear all existing data first
DELETE FROM survey_response;
DELETE FROM survey;
DELETE FROM survey_template;
DELETE FROM redemption;
DELETE FROM expense;
DELETE FROM income;
DELETE FROM passport;
DELETE FROM signup;
DELETE FROM passport_type;
DELETE FROM activity;
DELETE FROM user;
DELETE FROM admin;

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
sqlite3 ../instance/minipass.db << 'EOF'
UPDATE activity SET email_templates = '{}' WHERE email_templates IS NULL;
UPDATE activity SET logo_filename = NULL WHERE logo_filename IS NULL;
EOF

# Copy all uploaded images and files
echo "🖼️ Copying uploaded files..."
mkdir -p ../static/uploads
cp -r /tmp/migration/app/static/uploads/* ../static/uploads/ 2>/dev/null || echo "   No uploads to copy (this is OK)"

# Clean up temporary files
rm -rf /tmp/migration

echo "✅ MIGRATION COMPLETE! Go test your app at http://localhost:5000"
echo "📝 Your old database was backed up to instance/minipass_backup_*.db"