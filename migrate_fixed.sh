#!/bin/bash

echo "🚀 Starting migration..."

# Extract backup
echo "📦 Extracting your friend's backup..."
mkdir -p /tmp/migration
tar -xzf /home/kdresdell/minipass_app_backup_20250902_220450.tgz -C /tmp/migration/

# Import with explicit column mapping for activity table
echo "📊 Importing database..."
sqlite3 instance/minipass.db << 'EOF'
ATTACH DATABASE '/tmp/migration/app/instance/minipass.db' AS old;

-- Copy activity with explicit columns to handle new fields correctly
INSERT INTO activity (
    id, name, type, description, sessions_included, price_per_user, 
    goal_users, goal_revenue, cost_to_run, created_by, created_dt, 
    status, payment_instructions, start_date, end_date, image_filename, 
    organization_id, email_templates, logo_filename
) SELECT 
    id, name, type, description, sessions_included, price_per_user,
    goal_users, goal_revenue, cost_to_run, created_by, created_dt,
    status, payment_instructions, start_date, end_date, image_filename,
    organization_id, '{}', NULL
FROM old.activity;

-- Copy other tables as-is
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

# Copy files with existence check
echo "🖼️ Copying uploaded files..."
if [ -d "/tmp/migration/app/static/uploads" ]; then
    cp -r /tmp/migration/app/static/uploads/* static/uploads/ 2>/dev/null || echo "⚠️  No files to copy"
else
    echo "⚠️  No uploads directory in backup"
fi

rm -rf /tmp/migration
echo "✅ MIGRATION COMPLETE!"