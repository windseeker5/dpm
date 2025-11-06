-- Fix corrupted survey_response data
-- The columns got mixed up during migration

PRAGMA foreign_keys = OFF;

-- Create correct table
CREATE TABLE survey_response_fixed (
    id INTEGER NOT NULL PRIMARY KEY,
    survey_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    passport_id INTEGER,
    response_token VARCHAR(32) NOT NULL UNIQUE,
    responses TEXT,
    completed BOOLEAN,
    completed_dt DATETIME,
    started_dt DATETIME,
    invited_dt DATETIME,
    created_dt DATETIME,
    ip_address VARCHAR(45),
    user_agent TEXT,
    FOREIGN KEY(survey_id) REFERENCES survey (id),
    FOREIGN KEY(user_id) REFERENCES user (id),
    FOREIGN KEY(passport_id) REFERENCES passport (id) ON DELETE SET NULL
);

-- Copy data with column mapping to fix the order
-- Current (wrong): id, survey_id, user_id, passport_id, response_token, responses, completed, completed_dt, started_dt, invited_dt (=ip!), created_dt (=user_agent!), ip_address, user_agent
-- Target (right): id, survey_id, user_id, passport_id, response_token, responses, completed, completed_dt, started_dt, invited_dt, created_dt, ip_address, user_agent

-- The issue: columns shifted - invited_dt has IP, created_dt has user_agent
-- We need to get the ORIGINAL column positions before migration corrupted them

-- Check if there's data to fix
SELECT 'Records to fix:' as message, COUNT(*) as count FROM survey_response WHERE invited_dt NOT LIKE '____-__-__%';
