-- Migration Script: Add email_opt_out field to user table
-- Date: 2025-09-10
-- Purpose: Add email unsubscribe functionality

-- Check if column already exists (SQLite doesn't support IF NOT EXISTS for ALTER TABLE)
-- This will error if column exists, which is fine - it means migration already done

ALTER TABLE user ADD COLUMN email_opt_out BOOLEAN DEFAULT 0 NOT NULL;

-- Verify the migration succeeded
SELECT 'Migration complete! Verifying structure:' as status;
.schema user

-- Show confirmation
SELECT 'email_opt_out column added successfully!' as result WHERE EXISTS (
    SELECT 1 FROM pragma_table_info('user') WHERE name='email_opt_out'
);