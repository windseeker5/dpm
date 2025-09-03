#!/bin/bash

echo "🚀 Starting migration..."

# Extract backup
echo "📦 Extracting your friend's backup..."
mkdir -p /tmp/migration
tar -xzf /home/kdresdell/minipass_app_backup_20250902_220450.tgz -C /tmp/migration/

# Import all the data
echo "📊 Importing database..."
sqlite3 ../instance/minipass.db << 'EOF'
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
sqlite3 ../instance/minipass.db << 'EOF'
UPDATE activity SET email_templates = '{}' WHERE email_templates IS NULL;
UPDATE activity SET logo_filename = NULL WHERE logo_filename IS NULL;
EOF

# Copy all uploaded images and files
echo "🖼️ Copying uploaded files..."
cp -r /tmp/migration/app/static/uploads/* ../static/uploads/

# Clean up temporary files
rm -rf /tmp/migration

echo "✅ MIGRATION COMPLETE! Go test your app at http://localhost:5000"