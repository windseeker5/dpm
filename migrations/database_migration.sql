-- Database Migration: Add Passport Type Management Fields
-- =======================================================
-- Run this script to add the new columns for passport type management
-- Execute this in your SQLite database before running the Flask application

-- Add new columns to PassportType table
ALTER TABLE passport_type ADD COLUMN status VARCHAR(50) DEFAULT 'active';
ALTER TABLE passport_type ADD COLUMN archived_at DATETIME NULL;
ALTER TABLE passport_type ADD COLUMN archived_by VARCHAR(120) NULL;

-- Add new column to Passport table
ALTER TABLE passport ADD COLUMN passport_type_name VARCHAR(100) NULL;

-- Update existing passport_type records to have 'active' status
UPDATE passport_type SET status = 'active' WHERE status IS NULL;

-- Backfill passport_type_name for existing passports
UPDATE passport 
SET passport_type_name = (
    SELECT pt.name 
    FROM passport_type pt 
    WHERE pt.id = passport.passport_type_id
)
WHERE passport.passport_type_id IS NOT NULL 
AND passport.passport_type_name IS NULL;