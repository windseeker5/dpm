#!/usr/bin/env python3
"""
MASTER PRODUCTION DATABASE UPGRADE SCRIPT
Upgrades production database from survey_system_2025 version to latest version.

This script combines ALL necessary upgrades:
1. Schema changes (add location fields)
2. Data backfills (financial records)
3. Foreign key fixes (redemption CASCADE)
4. Survey template additions/updates (French survey - always latest version)
5. Email template fixes
6. Verification
7. Flask migration tracking (flask db stamp head)

SAFE to run multiple times - checks what's already done and skips it.
"""

import sqlite3
import sys
import os
import json
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'minipass.db')

# Color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'

def log(emoji, message, color=None):
    """Print timestamped log message with optional color"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if color:
        print(f"{color}{emoji} [{timestamp}] {message}{Colors.RESET}")
    else:
        print(f"{emoji} [{timestamp}] {message}")

def separator(char="="):
    """Print separator line"""
    print(char * 70)

def check_column_exists(cursor, table, column):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def check_table_exists(cursor, table):
    """Check if a table exists"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None

# ============================================================================
# TASK 1: Add Location Fields to Activity Table
# ============================================================================
def task1_add_location_fields(cursor):
    """Add location fields to Activity table"""
    log("📍", "TASK 1: Adding location fields to Activity table", Colors.BLUE)

    fields = [
        ('location_address_raw', 'TEXT'),
        ('location_address_formatted', 'TEXT'),
        ('location_coordinates', 'VARCHAR(100)')
    ]

    added = 0
    skipped = 0

    for field_name, field_type in fields:
        if check_column_exists(cursor, 'activity', field_name):
            log("⏭️ ", f"  Column '{field_name}' already exists", Colors.YELLOW)
            skipped += 1
        else:
            try:
                cursor.execute(f"ALTER TABLE activity ADD COLUMN {field_name} {field_type}")
                log("✅", f"  Added column '{field_name}'", Colors.GREEN)
                added += 1
            except sqlite3.OperationalError as e:
                log("❌", f"  Failed to add '{field_name}': {e}", Colors.RED)
                raise

    log("📊", f"  Summary: {added} added, {skipped} already existed")
    return True

# ============================================================================
# TASK 2: Backfill Financial Records
# ============================================================================
def task2_backfill_financial_records(cursor):
    """Backfill created_by for existing income and expense records"""
    log("💰", "TASK 2: Backfilling financial records", Colors.BLUE)

    total_updated = 0

    for table in ['income', 'expense']:
        if not check_table_exists(cursor, table):
            log("⏭️ ", f"  Table '{table}' doesn't exist, skipping", Colors.YELLOW)
            continue

        if not check_column_exists(cursor, table, 'created_by'):
            log("⏭️ ", f"  Column 'created_by' doesn't exist in {table}, skipping", Colors.YELLOW)
            continue

        try:
            cursor.execute(f"UPDATE {table} SET created_by = 'legacy' WHERE created_by IS NULL OR created_by = ''")
            updated = cursor.rowcount
            log("✅", f"  Updated {updated} {table} record(s)", Colors.GREEN)
            total_updated += updated
        except sqlite3.OperationalError as e:
            log("❌", f"  Failed to update {table}: {e}", Colors.RED)
            raise

    log("📊", f"  Summary: {total_updated} total records backfilled")
    return True

# ============================================================================
# TASK 3: Fix Redemption CASCADE DELETE
# ============================================================================
def task3_fix_redemption_cascade(cursor):
    """Add CASCADE DELETE to redemption.passport_id foreign key"""
    log("🔗", "TASK 3: Fixing redemption CASCADE DELETE", Colors.BLUE)

    # Check if redemption table exists
    if not check_table_exists(cursor, 'redemption'):
        log("⏭️ ", "  Redemption table doesn't exist, skipping", Colors.YELLOW)
        return True

    # Check current foreign key constraint
    cursor.execute("PRAGMA foreign_key_list(redemption)")
    fk_info = cursor.fetchall()

    if fk_info:
        # Check if already has CASCADE
        for fk in fk_info:
            if 'CASCADE' in str(fk):
                log("⏭️ ", "  CASCADE DELETE already configured", Colors.YELLOW)
                return True

    log("🔄", "  Recreating redemption table with CASCADE DELETE")

    try:
        # Disable foreign keys temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")

        # Create new table with CASCADE
        cursor.execute("""
            CREATE TABLE redemption_new (
                id INTEGER NOT NULL,
                passport_id INTEGER NOT NULL,
                date_used DATETIME,
                redeemed_by VARCHAR(100),
                PRIMARY KEY (id),
                FOREIGN KEY(passport_id) REFERENCES passport (id) ON DELETE CASCADE
            )
        """)

        # Copy data
        cursor.execute("""
            INSERT INTO redemption_new (id, passport_id, date_used, redeemed_by)
            SELECT id, passport_id, date_used, redeemed_by
            FROM redemption
        """)

        rows_copied = cursor.rowcount

        # Drop old table
        cursor.execute("DROP TABLE redemption")

        # Rename new table
        cursor.execute("ALTER TABLE redemption_new RENAME TO redemption")

        # Re-enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        log("✅", f"  Redemption table recreated with CASCADE DELETE ({rows_copied} rows preserved)", Colors.GREEN)
        return True

    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to fix redemption CASCADE: {e}", Colors.RED)
        # Try to re-enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        raise

# ============================================================================
# TASK 4: Add French Survey Template
# ============================================================================
def task4_add_french_survey(cursor):
    """Add French survey template if it doesn't exist"""
    log("📋", "TASK 4: Adding French survey template", Colors.BLUE)

    # Check if survey_template table exists
    if not check_table_exists(cursor, 'survey_template'):
        log("⏭️ ", "  survey_template table doesn't exist, skipping", Colors.YELLOW)
        return True

    # Check if French survey already exists
    cursor.execute("SELECT id FROM survey_template WHERE name = ?",
                   ("Sondage d'Activité - Simple (questions)",))
    existing = cursor.fetchone()

    # Define the French survey template
    questions = {
        "questions": [
            {
                "id": 1,
                "question": "Comment évaluez-vous votre satisfaction globale concernant cette activité?",
                "type": "rating",
                "required": True,
                "min_rating": 1,
                "max_rating": 5,
                "labels": {
                    "1": "Très insatisfait",
                    "2": "Insatisfait",
                    "3": "Neutre",
                    "4": "Satisfait",
                    "5": "Très satisfait"
                }
            },
            {
                "id": 2,
                "question": "Le prix demandé pour cette activité est-il justifié?",
                "type": "multiple_choice",
                "required": True,
                "options": ["Trop cher", "Un peu cher", "Juste", "Bon rapport qualité-prix", "Excellent rapport qualité-prix"]
            },
            {
                "id": 3,
                "question": "Recommanderiez-vous cette activité à un ami?",
                "type": "multiple_choice",
                "required": True,
                "options": ["Certainement", "Probablement", "Peut-être", "Probablement pas", "Certainement pas"]
            },
            {
                "id": 4,
                "question": "Comment évaluez-vous l'emplacement/les installations?",
                "type": "multiple_choice",
                "required": False,
                "options": ["Excellent", "Très bien", "Bien", "Moyen", "Insuffisant"]
            },
            {
                "id": 5,
                "question": "L'horaire de l'activité vous convenait-il?",
                "type": "multiple_choice",
                "required": False,
                "options": ["Parfaitement", "Bien", "Acceptable", "Peu pratique", "Très peu pratique"]
            },
            {
                "id": 6,
                "question": "Qu'avez-vous le plus apprécié de cette activité?",
                "type": "open_ended",
                "required": False,
                "max_length": 300
            },
            {
                "id": 7,
                "question": "Qu'est-ce qui pourrait être amélioré?",
                "type": "open_ended",
                "required": False,
                "max_length": 300
            },
            {
                "id": 8,
                "question": "Souhaiteriez-vous participer à nouveau à une activité similaire?",
                "type": "multiple_choice",
                "required": True,
                "options": ["Oui, certainement", "Oui, probablement", "Peut-être", "Probablement pas", "Non"]
            }
        ]
    }

    try:
        if existing:
            # Update existing template with NEW version
            template_id = existing[0]
            cursor.execute("""
                UPDATE survey_template
                SET description = ?,
                    questions = ?,
                    status = 'active'
                WHERE id = ?
            """, (
                "Sondage simple en français pour recueillir les retours après une activité ponctuelle (tournoi de golf, événement sportif, etc.). Temps de réponse: ~2 minutes.",
                json.dumps(questions),
                template_id
            ))

            log("✅", f"  French survey template UPDATED to new version (ID: {template_id}, 8 questions)", Colors.GREEN)
        else:
            # Insert new template
            cursor.execute("""
                INSERT INTO survey_template (name, description, questions, created_by, created_dt, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "Sondage d'Activité - Simple (questions)",
                "Sondage simple en français pour recueillir les retours après une activité ponctuelle (tournoi de golf, événement sportif, etc.). Temps de réponse: ~2 minutes.",
                json.dumps(questions),
                1,  # System admin
                datetime.now(timezone.utc).isoformat(),
                "active"
            ))

            log("✅", "  French survey template CREATED (8 questions)", Colors.GREEN)

        return True

    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to update/add French survey: {e}", Colors.RED)
        raise

# ============================================================================
# TASK 5: Fix Email Template Jinja2 Variables
# ============================================================================
def task5_fix_email_templates(cursor):
    """Fix hardcoded values in email templates with Jinja2 variables"""
    log("✉️ ", "TASK 5: Fixing email template Jinja2 variables", Colors.BLUE)

    # Check if activity table exists and has email_templates column
    if not check_table_exists(cursor, 'activity'):
        log("⏭️ ", "  Activity table doesn't exist, skipping", Colors.YELLOW)
        return True

    if not check_column_exists(cursor, 'activity', 'email_templates'):
        log("⏭️ ", "  email_templates column doesn't exist, skipping", Colors.YELLOW)
        return True

    # Get all activities with email templates
    cursor.execute("SELECT id, name, email_templates FROM activity WHERE email_templates IS NOT NULL")
    activities = cursor.fetchall()

    if not activities:
        log("⏭️ ", "  No activities with email templates found", Colors.YELLOW)
        return True

    updated = 0
    skipped = 0

    default_intro = '<p>Bonjour,</p><p>Nous aimerions connaître votre expérience récente avec nous pour l\'activité <strong>{{ activity_name }}</strong>!</p><p>Cela ne prendra que quelques minutes - seulement <strong>{{ question_count }}</strong> questions rapides.</p>'

    for activity_id, activity_name, email_templates_json in activities:
        try:
            templates = json.loads(email_templates_json) if email_templates_json else {}

            if 'survey_invitation' not in templates:
                skipped += 1
                continue

            survey_template = templates['survey_invitation']
            intro_text = survey_template.get('intro_text', '')

            # Check if already has Jinja2 variables
            if intro_text and '{{' in intro_text and '}}' in intro_text:
                skipped += 1
                continue

            # Update with Jinja2 variables
            survey_template['intro_text'] = default_intro
            templates['survey_invitation'] = survey_template

            # Save back to database
            cursor.execute(
                "UPDATE activity SET email_templates = ? WHERE id = ?",
                (json.dumps(templates), activity_id)
            )
            updated += 1

        except (json.JSONDecodeError, KeyError) as e:
            log("⚠️ ", f"  Skipped activity {activity_id}: {e}", Colors.YELLOW)
            continue

    log("✅", f"  Updated {updated} email template(s), skipped {skipped}", Colors.GREEN)
    return True

# ============================================================================
# TASK 6: Verify Database Schema
# ============================================================================
def task6_verify_schema(cursor):
    """Verify that all expected changes were applied"""
    log("🔍", "TASK 6: Verifying database schema", Colors.BLUE)

    checks = [
        ('admin', 'first_name', 'Admin names'),
        ('admin', 'last_name', 'Admin names'),
        ('admin', 'avatar_filename', 'Admin avatar'),
        ('activity', 'location_address_raw', 'Location fields'),
        ('activity', 'location_address_formatted', 'Location fields'),
        ('activity', 'location_coordinates', 'Location fields'),
        ('activity', 'offer_passport_renewal', 'Passport renewal setting'),
    ]

    all_good = True
    for table, column, description in checks:
        if check_table_exists(cursor, table):
            if check_column_exists(cursor, table, column):
                log("✅", f"  {description}: '{column}' exists", Colors.GREEN)
            else:
                log("❌", f"  {description}: '{column}' MISSING", Colors.RED)
                all_good = False
        else:
            log("⚠️ ", f"  Table '{table}' doesn't exist", Colors.YELLOW)

    # Check survey template
    if check_table_exists(cursor, 'survey_template'):
        cursor.execute("SELECT COUNT(*) FROM survey_template WHERE name LIKE 'Sondage%'")
        count = cursor.fetchone()[0]
        if count > 0:
            log("✅", f"  French survey template: {count} found", Colors.GREEN)
        else:
            log("⚠️ ", "  French survey template: not found", Colors.YELLOW)

    return all_good

# ============================================================================
# TASK 7: Add email_received_date to ebank_payment table
# ============================================================================
def task7_add_email_received_date(cursor):
    """Add email_received_date column to ebank_payment table"""
    log("📅", "TASK 7: Adding email_received_date to ebank_payment table", Colors.BLUE)

    # Check if ebank_payment table exists
    if not check_table_exists(cursor, 'ebank_payment'):
        log("⏭️ ", "  ebank_payment table doesn't exist, skipping", Colors.YELLOW)
        return True

    # Check if column already exists
    if check_column_exists(cursor, 'ebank_payment', 'email_received_date'):
        log("⏭️ ", "  Column 'email_received_date' already exists", Colors.YELLOW)
        return True

    try:
        # Add the new column
        cursor.execute("ALTER TABLE ebank_payment ADD COLUMN email_received_date DATETIME")
        log("✅", "  Added column 'email_received_date' to ebank_payment", Colors.GREEN)

        # Check how many existing records don't have this date
        cursor.execute("SELECT COUNT(*) FROM ebank_payment WHERE email_received_date IS NULL")
        null_count = cursor.fetchone()[0]

        if null_count > 0:
            log("ℹ️ ", f"  {null_count} existing payment(s) will have NULL email_received_date (bot run date only)", Colors.BLUE)
            log("ℹ️ ", "  Future payments will have actual email received dates", Colors.BLUE)

        return True

    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to add email_received_date column: {e}", Colors.RED)
        raise

# ============================================================================
# TASK 8: Fix ReminderLog CASCADE DELETE
# ============================================================================
def task8_fix_reminderlog_cascade(cursor):
    """Migrate reminder_log from old pass_id to passport_id with CASCADE DELETE"""
    log("🔗", "TASK 8: Fixing reminder_log CASCADE DELETE", Colors.BLUE)

    # Check if reminder_log table exists
    if not check_table_exists(cursor, 'reminder_log'):
        log("⏭️ ", "  reminder_log table doesn't exist, skipping", Colors.YELLOW)
        return True

    # Get current table schema to check what columns exist
    cursor.execute("PRAGMA table_info(reminder_log)")
    columns_info = cursor.fetchall()
    column_names = [col[1] for col in columns_info]

    # Check if we have old pass_id or new passport_id
    has_pass_id = 'pass_id' in column_names
    has_passport_id = 'passport_id' in column_names

    if not has_pass_id and not has_passport_id:
        log("⏭️ ", "  reminder_log table has neither pass_id nor passport_id, skipping", Colors.YELLOW)
        return True

    # Check current foreign key constraint
    cursor.execute("PRAGMA foreign_key_list(reminder_log)")
    fk_info = cursor.fetchall()

    # If already has passport_id with CASCADE, we're done
    if has_passport_id and fk_info:
        for fk in fk_info:
            # fk format: (id, seq, table, from, to, on_update, on_delete, match)
            if len(fk) >= 7 and fk[2] == 'passport' and 'CASCADE' in str(fk[6]):
                log("⏭️ ", "  CASCADE DELETE already configured with passport_id", Colors.YELLOW)
                return True

    # Need to migrate from pass_id to passport_id or fix CASCADE
    if has_pass_id:
        log("🔄", "  Migrating from old 'pass_id' to 'passport_id' with CASCADE DELETE")
    else:
        log("🔄", "  Recreating reminder_log table with CASCADE DELETE")

    try:
        # Disable foreign keys temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")

        # Create new table with passport_id and CASCADE (matching Flask migration format)
        cursor.execute("""CREATE TABLE IF NOT EXISTS "reminder_log_new" (
    id INTEGER NOT NULL PRIMARY KEY,
    passport_id INTEGER NOT NULL,
    reminder_sent_at DATETIME,
    FOREIGN KEY(passport_id) REFERENCES passport (id) ON DELETE CASCADE
)""")

        # Copy data - handle both old pass_id and new passport_id column names
        if has_pass_id:
            # Migrate from old pass_id to new passport_id
            cursor.execute("""
                INSERT INTO reminder_log_new (id, passport_id, reminder_sent_at)
                SELECT id, pass_id, reminder_sent_at
                FROM reminder_log
            """)
        else:
            # Already has passport_id, just copy
            cursor.execute("""
                INSERT INTO reminder_log_new (id, passport_id, reminder_sent_at)
                SELECT id, passport_id, reminder_sent_at
                FROM reminder_log
            """)

        rows_copied = cursor.rowcount

        # Drop old table
        cursor.execute("DROP TABLE reminder_log")

        # Rename new table
        cursor.execute("ALTER TABLE reminder_log_new RENAME TO reminder_log")

        # Re-enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        if has_pass_id:
            log("✅", f"  reminder_log migrated: pass_id → passport_id with CASCADE DELETE ({rows_copied} rows preserved)", Colors.GREEN)
        else:
            log("✅", f"  reminder_log recreated with CASCADE DELETE ({rows_copied} rows preserved)", Colors.GREEN)
        return True

    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to fix reminder_log CASCADE: {e}", Colors.RED)
        # Try to re-enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        raise

# ============================================================================
# TASK 9: Fix Passport Deletion FK Constraints (SET NULL)
# ============================================================================
def task9_fix_passport_deletion_fks(cursor):
    """Add ON DELETE SET NULL to passport_id foreign keys in signup, ebank_payment, and survey_response"""
    log("🔗", "TASK 9: Fixing passport deletion FK constraints (SET NULL)", Colors.BLUE)

    tables_to_fix = [
        {
            'name': 'signup',
            'fk_column': 'passport_id',
            'columns': 'id, user_id, activity_id, subject, description, form_url, form_data, signed_up_at, paid, paid_at, passport_id, status, passport_type_id',
            'schema': """
                CREATE TABLE signup_new (
                    id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    activity_id INTEGER NOT NULL,
                    subject VARCHAR(200),
                    description TEXT,
                    form_url VARCHAR(500),
                    form_data TEXT,
                    signed_up_at DATETIME,
                    paid BOOLEAN,
                    paid_at DATETIME,
                    passport_id INTEGER,
                    status VARCHAR(50),
                    passport_type_id INTEGER,
                    PRIMARY KEY (id),
                    FOREIGN KEY(activity_id) REFERENCES activity (id),
                    FOREIGN KEY(passport_id) REFERENCES passport (id) ON DELETE SET NULL,
                    FOREIGN KEY(user_id) REFERENCES user (id),
                    FOREIGN KEY(passport_type_id) REFERENCES passport_type (id)
                )
            """,
            'indexes': [
                "CREATE INDEX ix_signup_status ON signup (status)"
            ]
        },
        {
            'name': 'ebank_payment',
            'fk_column': 'matched_pass_id',
            'columns': 'id, timestamp, from_email, subject, bank_info_name, bank_info_amt, matched_pass_id, matched_name, matched_amt, name_score, result, mark_as_paid, note, email_received_date',
            'schema': """
                CREATE TABLE ebank_payment_new (
                    id INTEGER NOT NULL PRIMARY KEY,
                    timestamp DATETIME,
                    from_email VARCHAR(150),
                    subject TEXT,
                    bank_info_name VARCHAR(100),
                    bank_info_amt FLOAT,
                    matched_pass_id INTEGER,
                    matched_name VARCHAR(100),
                    matched_amt FLOAT,
                    name_score INTEGER,
                    result VARCHAR(50),
                    mark_as_paid BOOLEAN,
                    note TEXT,
                    email_received_date DATETIME,
                    FOREIGN KEY(matched_pass_id) REFERENCES passport (id) ON DELETE SET NULL
                )
            """,
            'indexes': []
        },
        {
            'name': 'survey_response',
            'fk_column': 'passport_id',
            'columns': 'id, survey_id, user_id, passport_id, response_token, responses, completed, completed_dt, started_dt, invited_dt, created_dt, ip_address, user_agent',
            'schema': """
                CREATE TABLE survey_response_new (
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
                )
            """,
            'indexes': [
                "CREATE INDEX ix_survey_response_token ON survey_response (response_token)",
                "CREATE INDEX ix_survey_response_survey ON survey_response (survey_id)"
            ]
        }
    ]

    total_fixed = 0
    total_skipped = 0

    for table_config in tables_to_fix:
        table_name = table_config['name']
        fk_column = table_config['fk_column']

        # Check if table exists
        if not check_table_exists(cursor, table_name):
            log("⏭️ ", f"  Table '{table_name}' doesn't exist, skipping", Colors.YELLOW)
            total_skipped += 1
            continue

        # Check current foreign key constraint
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fk_info = cursor.fetchall()

        # Check if already has ON DELETE SET NULL for passport_id
        already_fixed = False
        for fk in fk_info:
            # fk format: (id, seq, table, from, to, on_update, on_delete, match)
            if len(fk) >= 7 and fk[3] == fk_column and 'SET NULL' in str(fk[6]):
                already_fixed = True
                break

        if already_fixed:
            log("⏭️ ", f"  {table_name}.{fk_column}: ON DELETE SET NULL already configured", Colors.YELLOW)
            total_skipped += 1
            continue

        log("🔄", f"  Recreating {table_name} table with ON DELETE SET NULL")

        try:
            # Disable foreign keys temporarily
            cursor.execute("PRAGMA foreign_keys = OFF")

            # Create new table with ON DELETE SET NULL
            cursor.execute(table_config['schema'])

            # Copy data with explicit column names to preserve order
            columns = table_config['columns']
            cursor.execute(f"INSERT INTO {table_name}_new ({columns}) SELECT {columns} FROM {table_name}")
            rows_copied = cursor.rowcount

            # Drop old table
            cursor.execute(f"DROP TABLE {table_name}")

            # Rename new table
            cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")

            # Recreate indexes
            for index_sql in table_config['indexes']:
                cursor.execute(index_sql)

            # Re-enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")

            log("✅", f"  {table_name} recreated with ON DELETE SET NULL ({rows_copied} rows preserved)", Colors.GREEN)
            total_fixed += 1

        except sqlite3.OperationalError as e:
            log("❌", f"  Failed to fix {table_name}: {e}", Colors.RED)
            # Try to re-enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            raise

    log("📊", f"  Summary: {total_fixed} table(s) fixed, {total_skipped} already configured")
    return True


def task10_fix_passport_type_deletion_fks(cursor):
    """Add ON DELETE SET NULL to passport_type_id foreign keys in signup, passport, and survey"""
    log("🔗", "TASK 10: Fixing passport_type deletion FK constraints (SET NULL)", Colors.BLUE)

    tables_to_fix = [
        {
            'name': 'signup',
            'fk_column': 'passport_type_id',
            'columns': 'id, user_id, activity_id, subject, description, form_url, form_data, signed_up_at, paid, paid_at, passport_id, status, passport_type_id',
            'schema': """
                CREATE TABLE signup_new (
                    id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    activity_id INTEGER NOT NULL,
                    subject VARCHAR(200),
                    description TEXT,
                    form_url VARCHAR(500),
                    form_data TEXT,
                    signed_up_at DATETIME,
                    paid BOOLEAN,
                    paid_at DATETIME,
                    passport_id INTEGER,
                    status VARCHAR(50),
                    passport_type_id INTEGER,
                    PRIMARY KEY (id),
                    FOREIGN KEY(activity_id) REFERENCES activity (id),
                    FOREIGN KEY(passport_id) REFERENCES passport (id) ON DELETE SET NULL,
                    FOREIGN KEY(user_id) REFERENCES user (id),
                    FOREIGN KEY(passport_type_id) REFERENCES passport_type (id) ON DELETE SET NULL
                )
            """,
            'indexes': [
                "CREATE INDEX ix_signup_status ON signup (status)"
            ]
        },
        {
            'name': 'passport',
            'fk_column': 'passport_type_id',
            'columns': 'id, pass_code, user_id, activity_id, sold_amt, uses_remaining, created_by, created_dt, paid, paid_date, marked_paid_by, notes, passport_type_id, passport_type_name',
            'schema': """
                CREATE TABLE passport_new (
                    id INTEGER NOT NULL PRIMARY KEY,
                    pass_code VARCHAR(16) UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    activity_id INTEGER NOT NULL,
                    sold_amt FLOAT,
                    uses_remaining INTEGER,
                    created_by INTEGER,
                    created_dt DATETIME,
                    paid BOOLEAN,
                    paid_date DATETIME,
                    marked_paid_by VARCHAR(120),
                    notes TEXT,
                    passport_type_id INTEGER,
                    passport_type_name VARCHAR(100),
                    FOREIGN KEY(user_id) REFERENCES user (id),
                    FOREIGN KEY(activity_id) REFERENCES activity (id),
                    FOREIGN KEY(passport_type_id) REFERENCES passport_type (id) ON DELETE SET NULL,
                    FOREIGN KEY(created_by) REFERENCES admin (id)
                )
            """,
            'indexes': [
                "CREATE INDEX ix_passport_pass_code ON passport (pass_code)"
            ]
        },
        {
            'name': 'survey',
            'fk_column': 'passport_type_id',
            'columns': 'id, activity_id, template_id, passport_type_id, name, description, survey_token, created_by, created_dt, status, email_sent, email_sent_dt',
            'schema': """
                CREATE TABLE survey_new (
                    id INTEGER NOT NULL PRIMARY KEY,
                    activity_id INTEGER NOT NULL,
                    template_id INTEGER NOT NULL,
                    passport_type_id INTEGER,
                    name VARCHAR(150) NOT NULL,
                    description TEXT,
                    survey_token VARCHAR(32) UNIQUE NOT NULL,
                    created_by INTEGER,
                    created_dt DATETIME,
                    status VARCHAR(50),
                    email_sent BOOLEAN,
                    email_sent_dt DATETIME,
                    FOREIGN KEY(activity_id) REFERENCES activity (id),
                    FOREIGN KEY(template_id) REFERENCES survey_template (id),
                    FOREIGN KEY(passport_type_id) REFERENCES passport_type (id) ON DELETE SET NULL,
                    FOREIGN KEY(created_by) REFERENCES admin (id)
                )
            """,
            'indexes': [
                "CREATE INDEX ix_survey_token ON survey (survey_token)"
            ]
        }
    ]

    total_fixed = 0
    total_skipped = 0

    for table_config in tables_to_fix:
        table_name = table_config['name']
        fk_column = table_config['fk_column']

        # Check if table exists
        if not check_table_exists(cursor, table_name):
            log("⏭️ ", f"  Table '{table_name}' doesn't exist, skipping", Colors.YELLOW)
            total_skipped += 1
            continue

        # Check current foreign key constraint
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fk_info = cursor.fetchall()

        # Check if already has ON DELETE SET NULL for passport_type_id
        already_fixed = False
        for fk in fk_info:
            # fk format: (id, seq, table, from, to, on_update, on_delete, match)
            if len(fk) >= 7 and fk[3] == fk_column and 'SET NULL' in str(fk[6]):
                already_fixed = True
                break

        if already_fixed:
            log("⏭️ ", f"  {table_name}.{fk_column}: ON DELETE SET NULL already configured", Colors.YELLOW)
            total_skipped += 1
            continue

        log("🔄", f"  Recreating {table_name} table with ON DELETE SET NULL")

        try:
            # Disable foreign keys temporarily
            cursor.execute("PRAGMA foreign_keys = OFF")

            # Create new table with ON DELETE SET NULL
            cursor.execute(table_config['schema'])

            # Copy data with explicit column names to preserve order
            columns = table_config['columns']
            cursor.execute(f"INSERT INTO {table_name}_new ({columns}) SELECT {columns} FROM {table_name}")
            rows_copied = cursor.rowcount

            # Drop old table
            cursor.execute(f"DROP TABLE {table_name}")

            # Rename new table
            cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")

            # Recreate indexes
            for index_sql in table_config['indexes']:
                cursor.execute(index_sql)

            # Re-enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")

            log("✅", f"  {table_name} recreated with ON DELETE SET NULL ({rows_copied} rows preserved)", Colors.GREEN)
            total_fixed += 1

        except sqlite3.OperationalError as e:
            log("❌", f"  Failed to fix {table_name}: {e}", Colors.RED)
            # Try to re-enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            raise

    log("📊", f"  Summary: {total_fixed} table(s) fixed, {total_skipped} already configured")
    return True


def task11_drop_old_pass_table(cursor):
    """Drop obsolete 'pass' table if it exists (replaced by 'passport')"""
    log("🗑️ ", "TASK 11: Removing obsolete 'pass' table", Colors.BLUE)

    # Check if old pass table exists
    if not check_table_exists(cursor, 'pass'):
        log("⏭️ ", "  Old 'pass' table doesn't exist, skipping", Colors.YELLOW)
        return True

    # Check if it's empty (safety check)
    cursor.execute("SELECT COUNT(*) FROM pass")
    count = cursor.fetchone()[0]

    if count > 0:
        log("⚠️ ", f"  WARNING: 'pass' table has {count} records - manual review needed", Colors.YELLOW)
        log("💡", "  Keeping table for safety - please manually review and migrate data", Colors.YELLOW)
        return True

    try:
        cursor.execute("DROP TABLE pass")
        log("✅", "  Obsolete 'pass' table removed (was empty)", Colors.GREEN)
        return True
    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to drop 'pass' table: {e}", Colors.RED)
        raise


def task12_fix_survey_deletion_fk(cursor):
    """Add ON DELETE CASCADE to survey_response.survey_id foreign key"""
    log("🔗", "TASK 12: Fixing survey deletion FK constraint (CASCADE)", Colors.BLUE)

    table_name = 'survey_response'
    fk_column = 'survey_id'

    # Check if table exists
    if not check_table_exists(cursor, table_name):
        log("⏭️ ", f"  Table '{table_name}' doesn't exist, skipping", Colors.YELLOW)
        return True

    # Check current foreign key constraint
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    fk_info = cursor.fetchall()

    # Check if already has ON DELETE CASCADE for survey_id
    already_fixed = False
    for fk in fk_info:
        # fk format: (id, seq, table, from, to, on_update, on_delete, match)
        if len(fk) >= 7 and fk[3] == fk_column and 'CASCADE' in str(fk[6]):
            already_fixed = True
            break

    if already_fixed:
        log("⏭️ ", f"  {table_name}.{fk_column}: ON DELETE CASCADE already configured", Colors.YELLOW)
        return True

    log("🔄", f"  Recreating {table_name} table with ON DELETE CASCADE for {fk_column}")

    try:
        # Disable foreign keys temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")

        # Create new table with ON DELETE CASCADE
        cursor.execute("""
            CREATE TABLE survey_response_new (
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
                FOREIGN KEY(survey_id) REFERENCES survey (id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES user (id),
                FOREIGN KEY(passport_id) REFERENCES passport (id) ON DELETE SET NULL
            )
        """)

        # Copy data with explicit column names to preserve order
        columns = 'id, survey_id, user_id, passport_id, response_token, responses, completed, completed_dt, started_dt, invited_dt, created_dt, ip_address, user_agent'
        cursor.execute(f"INSERT INTO survey_response_new ({columns}) SELECT {columns} FROM survey_response")
        rows_copied = cursor.rowcount

        # Drop old table
        cursor.execute(f"DROP TABLE survey_response")

        # Rename new table
        cursor.execute(f"ALTER TABLE survey_response_new RENAME TO survey_response")

        # Recreate indexes
        cursor.execute("CREATE INDEX ix_survey_response_token ON survey_response (response_token)")
        cursor.execute("CREATE INDEX ix_survey_response_survey ON survey_response (survey_id)")

        # Re-enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        log("✅", f"  survey_response recreated with ON DELETE CASCADE ({rows_copied} rows preserved)", Colors.GREEN)
        return True

    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to fix survey_response: {e}", Colors.RED)
        # Try to re-enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        raise


# ============================================================================
# TASK 13: Add Payment Status Columns (Migration 0307966a5581)
# ============================================================================
def task13_add_payment_status_columns(cursor):
    """Add payment status tracking to income and expense tables"""
    log("💳", "TASK 13: Adding payment status columns", Colors.BLUE)

    added = 0
    skipped = 0

    # Expense table columns
    expense_columns = [
        ('payment_status', "VARCHAR(20) DEFAULT 'paid'"),
        ('payment_date', 'DATETIME'),
        ('due_date', 'DATETIME'),
        ('payment_method', 'VARCHAR(50)')
    ]

    if check_table_exists(cursor, 'expense'):
        for col_name, col_type in expense_columns:
            if check_column_exists(cursor, 'expense', col_name):
                log("⏭️ ", f"  expense.{col_name} already exists", Colors.YELLOW)
                skipped += 1
            else:
                try:
                    cursor.execute(f"ALTER TABLE expense ADD COLUMN {col_name} {col_type}")
                    log("✅", f"  Added expense.{col_name}", Colors.GREEN)
                    added += 1
                except sqlite3.OperationalError as e:
                    log("❌", f"  Failed to add expense.{col_name}: {e}", Colors.RED)
                    raise
    else:
        log("⏭️ ", "  expense table doesn't exist, skipping", Colors.YELLOW)

    # Income table columns
    income_columns = [
        ('payment_status', "VARCHAR(20) DEFAULT 'received'"),
        ('payment_date', 'DATETIME'),
        ('payment_method', 'VARCHAR(50)')
    ]

    if check_table_exists(cursor, 'income'):
        for col_name, col_type in income_columns:
            if check_column_exists(cursor, 'income', col_name):
                log("⏭️ ", f"  income.{col_name} already exists", Colors.YELLOW)
                skipped += 1
            else:
                try:
                    cursor.execute(f"ALTER TABLE income ADD COLUMN {col_name} {col_type}")
                    log("✅", f"  Added income.{col_name}", Colors.GREEN)
                    added += 1
                except sqlite3.OperationalError as e:
                    log("❌", f"  Failed to add income.{col_name}: {e}", Colors.RED)
                    raise
    else:
        log("⏭️ ", "  income table doesn't exist, skipping", Colors.YELLOW)

    log("📊", f"  Summary: {added} columns added, {skipped} already existed")
    return True


# ============================================================================
# TASK 14: Add Custom Payment Instructions Flag (Migration af5045ed1c22)
# ============================================================================
def task14_add_custom_payment_flag(cursor):
    """Add use_custom_payment_instructions to passport_type"""
    log("💰", "TASK 14: Adding custom payment instructions flag", Colors.BLUE)

    if not check_table_exists(cursor, 'passport_type'):
        log("⏭️ ", "  passport_type table doesn't exist, skipping", Colors.YELLOW)
        return True

    if check_column_exists(cursor, 'passport_type', 'use_custom_payment_instructions'):
        log("⏭️ ", "  use_custom_payment_instructions already exists", Colors.YELLOW)
        return True

    try:
        cursor.execute("""
            ALTER TABLE passport_type
            ADD COLUMN use_custom_payment_instructions BOOLEAN DEFAULT 0
        """)
        log("✅", "  Added use_custom_payment_instructions column", Colors.GREEN)
        return True
    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to add column: {e}", Colors.RED)
        raise


# ============================================================================
# TASK 15: Create Financial Views (Migrations a9e8d26b87b3 + 90c766ac9eed)
# ============================================================================
def task15_create_financial_views(cursor):
    """Create accounting-standard financial views (FIXED VERSION from migration 90c766ac9eed)"""
    log("📊", "TASK 15: Creating financial views", Colors.BLUE)

    # Drop old views if they exist
    try:
        cursor.execute("DROP VIEW IF EXISTS monthly_transactions_detail")
        cursor.execute("DROP VIEW IF EXISTS monthly_financial_summary")
        log("🔄", "  Dropped old views if they existed", Colors.BLUE)
    except:
        pass

    # Create detail view
    try:
        cursor.execute("""
            CREATE VIEW monthly_transactions_detail AS
            SELECT
                strftime('%Y-%m', COALESCE(p.paid_date, p.created_dt)) as month,
                a.name as project,
                'Income' as transaction_type,
                COALESCE(p.paid_date, p.created_dt) as transaction_date,
                'Passport Sales' as account,
                u.name as customer,
                NULL as vendor,
                p.notes as memo,
                p.sold_amt as amount,
                CASE WHEN p.paid = 1 THEN 'Paid' ELSE 'Unpaid (AR)' END as payment_status,
                'Passport System' as entered_by
            FROM passport p
            JOIN activity a ON p.activity_id = a.id
            LEFT JOIN user u ON p.user_id = u.id

            UNION ALL

            SELECT
                strftime('%Y-%m', i.date) as month,
                a.name as project,
                'Income' as transaction_type,
                i.date as transaction_date,
                i.category as account,
                NULL as customer,
                NULL as vendor,
                i.note as memo,
                i.amount,
                CASE
                    WHEN i.payment_status = 'received' THEN 'Paid'
                    WHEN i.payment_status = 'pending' THEN 'Unpaid (AR)'
                    ELSE 'Unpaid (AR)'
                END as payment_status,
                COALESCE(i.created_by, 'System') as entered_by
            FROM income i
            JOIN activity a ON i.activity_id = a.id

            UNION ALL

            SELECT
                strftime('%Y-%m', e.date) as month,
                a.name as project,
                'Expense' as transaction_type,
                e.date as transaction_date,
                e.category as account,
                NULL as customer,
                NULL as vendor,
                e.description as memo,
                e.amount,
                CASE
                    WHEN e.payment_status = 'paid' THEN 'Paid'
                    WHEN e.payment_status = 'unpaid' THEN 'Unpaid (AP)'
                    ELSE 'Unpaid (AP)'
                END as payment_status,
                COALESCE(e.created_by, 'System') as entered_by
            FROM expense e
            JOIN activity a ON e.activity_id = a.id

            ORDER BY month DESC, transaction_date DESC
        """)
        log("✅", "  Created monthly_transactions_detail view", Colors.GREEN)
    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to create transactions detail view: {e}", Colors.RED)
        raise

    # Create summary view (FIXED VERSION from migration 90c766ac9eed)
    try:
        cursor.execute("""
            CREATE VIEW monthly_financial_summary AS
            WITH
            all_month_activity AS (
                SELECT DISTINCT
                    strftime('%Y-%m', paid_date) as month,
                    activity_id
                FROM passport
                WHERE paid = 1 AND paid_date IS NOT NULL

                UNION

                SELECT DISTINCT
                    strftime('%Y-%m', COALESCE(paid_date, created_dt)) as month,
                    activity_id
                FROM passport
                WHERE paid = 0

                UNION

                SELECT DISTINCT
                    strftime('%Y-%m', date) as month,
                    activity_id
                FROM income
                WHERE payment_status = 'received'

                UNION

                SELECT DISTINCT
                    strftime('%Y-%m', date) as month,
                    activity_id
                FROM income
                WHERE payment_status = 'pending'

                UNION

                SELECT DISTINCT
                    strftime('%Y-%m', date) as month,
                    activity_id
                FROM expense
                WHERE payment_status = 'paid'

                UNION

                SELECT DISTINCT
                    strftime('%Y-%m', date) as month,
                    activity_id
                FROM expense
                WHERE payment_status = 'unpaid'
            ),
            monthly_passports_cash AS (
                SELECT
                    strftime('%Y-%m', paid_date) as month,
                    activity_id,
                    SUM(sold_amt) as passport_sales_cash
                FROM passport
                WHERE paid = 1 AND paid_date IS NOT NULL
                GROUP BY month, activity_id
            ),
            monthly_passports_ar AS (
                SELECT
                    strftime('%Y-%m', COALESCE(paid_date, created_dt)) as month,
                    activity_id,
                    SUM(sold_amt) as passport_sales_ar
                FROM passport
                WHERE paid = 0
                GROUP BY month, activity_id
            ),
            monthly_income_cash AS (
                SELECT
                    strftime('%Y-%m', date) as month,
                    activity_id,
                    SUM(amount) as other_income_cash
                FROM income
                WHERE payment_status = 'received'
                GROUP BY month, activity_id
            ),
            monthly_income_ar AS (
                SELECT
                    strftime('%Y-%m', date) as month,
                    activity_id,
                    SUM(amount) as other_income_ar
                FROM income
                WHERE payment_status = 'pending'
                GROUP BY month, activity_id
            ),
            monthly_expenses_cash AS (
                SELECT
                    strftime('%Y-%m', date) as month,
                    activity_id,
                    SUM(amount) as expenses_cash
                FROM expense
                WHERE payment_status = 'paid'
                GROUP BY month, activity_id
            ),
            monthly_expenses_ap AS (
                SELECT
                    strftime('%Y-%m', date) as month,
                    activity_id,
                    SUM(amount) as expenses_ap
                FROM expense
                WHERE payment_status = 'unpaid'
                GROUP BY month, activity_id
            )
            SELECT
                ma.month,
                ma.activity_id,
                a.name as account,

                COALESCE(pc.passport_sales_cash, 0) as passport_sales,
                COALESCE(ic.other_income_cash, 0) as other_income,
                COALESCE(pc.passport_sales_cash, 0) + COALESCE(ic.other_income_cash, 0) as cash_received,
                COALESCE(ec.expenses_cash, 0) as cash_paid,
                (COALESCE(pc.passport_sales_cash, 0) + COALESCE(ic.other_income_cash, 0) - COALESCE(ec.expenses_cash, 0)) as net_cash_flow,

                COALESCE(par.passport_sales_ar, 0) as passport_ar,
                COALESCE(iar.other_income_ar, 0) as other_income_ar,
                COALESCE(par.passport_sales_ar, 0) + COALESCE(iar.other_income_ar, 0) as accounts_receivable,
                COALESCE(eap.expenses_ap, 0) as accounts_payable,

                (COALESCE(pc.passport_sales_cash, 0) + COALESCE(par.passport_sales_ar, 0) +
                 COALESCE(ic.other_income_cash, 0) + COALESCE(iar.other_income_ar, 0)) as total_revenue,
                (COALESCE(ec.expenses_cash, 0) + COALESCE(eap.expenses_ap, 0)) as total_expenses,
                ((COALESCE(pc.passport_sales_cash, 0) + COALESCE(par.passport_sales_ar, 0) +
                  COALESCE(ic.other_income_cash, 0) + COALESCE(iar.other_income_ar, 0)) -
                 (COALESCE(ec.expenses_cash, 0) + COALESCE(eap.expenses_ap, 0))) as net_income

            FROM all_month_activity ma
            JOIN activity a ON ma.activity_id = a.id
            LEFT JOIN monthly_passports_cash pc ON ma.month = pc.month AND ma.activity_id = pc.activity_id
            LEFT JOIN monthly_passports_ar par ON ma.month = par.month AND ma.activity_id = par.activity_id
            LEFT JOIN monthly_income_cash ic ON ma.month = ic.month AND ma.activity_id = ic.activity_id
            LEFT JOIN monthly_income_ar iar ON ma.month = iar.month AND ma.activity_id = iar.activity_id
            LEFT JOIN monthly_expenses_cash ec ON ma.month = ec.month AND ma.activity_id = ec.activity_id
            LEFT JOIN monthly_expenses_ap eap ON ma.month = eap.month AND ma.activity_id = eap.activity_id
            ORDER BY ma.month DESC, a.name
        """)
        log("✅", "  Created monthly_financial_summary view (FIXED VERSION)", Colors.GREEN)
        return True
    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to create financial summary view: {e}", Colors.RED)
        raise


# ============================================================================
# TASK 16: Add AI Answer Column (Migration 937a43599a19)
# ============================================================================
def task16_add_ai_answer_column(cursor):
    """Add ai_answer column to query_log for chatbot responses"""
    log("🤖", "TASK 16: Adding ai_answer column to query_log", Colors.BLUE)

    if not check_table_exists(cursor, 'query_log'):
        log("⏭️ ", "  query_log table doesn't exist, skipping", Colors.YELLOW)
        return True

    if check_column_exists(cursor, 'query_log', 'ai_answer'):
        log("⏭️ ", "  ai_answer column already exists", Colors.YELLOW)
        return True

    try:
        cursor.execute("ALTER TABLE query_log ADD COLUMN ai_answer TEXT")
        log("✅", "  Added ai_answer column", Colors.GREEN)
        return True
    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to add ai_answer column: {e}", Colors.RED)
        raise


# ============================================================================
# TASK 18: Add Stripe Subscription Settings for Beta Testers
# ============================================================================
def task18_add_stripe_subscription_settings(cursor):
    """Add Stripe subscription setting keys with empty values for beta testers"""
    log("💳", "TASK 18: Adding Stripe subscription settings", Colors.BLUE)

    # Check if setting table exists
    if not check_table_exists(cursor, 'setting'):
        log("⏭️ ", "  setting table doesn't exist, skipping", Colors.YELLOW)
        return True

    stripe_settings = [
        ('STRIPE_CUSTOMER_ID', ''),
        ('STRIPE_SUBSCRIPTION_ID', ''),
        ('PAYMENT_AMOUNT', ''),
        ('SUBSCRIPTION_RENEWAL_DATE', ''),
        ('MINIPASS_TIER', ''),
        ('BILLING_FREQUENCY', '')
    ]

    added = 0
    skipped = 0

    for key, default_value in stripe_settings:
        # Check if setting already exists
        cursor.execute("SELECT id, value FROM setting WHERE key = ?", (key,))
        existing = cursor.fetchone()

        if existing:
            log("⏭️ ", f"  {key} already exists", Colors.YELLOW)
            skipped += 1
        else:
            try:
                cursor.execute("""
                    INSERT INTO setting (key, value)
                    VALUES (?, ?)
                """, (key, default_value))
                log("✅", f"  Added {key} with empty value", Colors.GREEN)
                added += 1
            except sqlite3.OperationalError as e:
                log("❌", f"  Failed to add {key}: {e}", Colors.RED)
                raise

    log("📊", f"  Summary: {added} settings added, {skipped} already existed")
    log("ℹ️ ", "  Empty values indicate beta tester - will show appreciation message", Colors.BLUE)
    return True


# ============================================================================
# TASK 19: Fix Activity Table PRIMARY KEY Constraint
# ============================================================================
def task19_fix_activity_primary_key(cursor):
    """Fix activity table PRIMARY KEY constraint (lost by CREATE TABLE AS SELECT bug)"""
    log("🔑", "TASK 19: Fixing activity table PRIMARY KEY", Colors.BLUE)

    # Check if PRIMARY KEY already exists
    cursor.execute("PRAGMA table_info(activity)")
    columns_info = cursor.fetchall()
    for col in columns_info:
        # col[5] is pk flag (1 = primary key)
        if col[1] == 'id' and col[5] == 1:
            log("⏭️ ", "  activity.id already has PRIMARY KEY", Colors.YELLOW)
            return True

    log("🔄", "  Recreating activity table with PRIMARY KEY")

    try:
        cursor.execute("PRAGMA foreign_keys = OFF")

        # Drop views that depend on activity table (Task 15 will recreate them)
        cursor.execute("DROP VIEW IF EXISTS monthly_transactions_detail")
        cursor.execute("DROP VIEW IF EXISTS monthly_financial_summary")
        log("🔄", "  Dropped dependent views (will be recreated by Task 15)")

        # Get current columns
        cursor.execute("PRAGMA table_info(activity)")
        columns = [col[1] for col in cursor.fetchall()]
        columns_str = ', '.join(columns)

        # Create new table with proper PRIMARY KEY
        cursor.execute("""
            CREATE TABLE activity_new (
                id INTEGER NOT NULL PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,
                description TEXT,
                sessions_included INTEGER,
                price_per_user REAL,
                goal_users INTEGER,
                goal_revenue REAL,
                cost_to_run REAL,
                created_by INTEGER,
                created_dt DATETIME,
                status TEXT,
                payment_instructions TEXT,
                start_date DATETIME,
                end_date DATETIME,
                image_filename TEXT,
                email_templates TEXT,
                logo_filename TEXT,
                location_address_raw TEXT,
                location_address_formatted TEXT,
                location_coordinates TEXT,
                FOREIGN KEY(created_by) REFERENCES admin(id)
            )
        """)

        # Copy data
        cursor.execute(f"INSERT INTO activity_new ({columns_str}) SELECT {columns_str} FROM activity")
        rows_copied = cursor.rowcount

        # Drop old table
        cursor.execute("DROP TABLE activity")

        # Rename new table
        cursor.execute("ALTER TABLE activity_new RENAME TO activity")

        cursor.execute("PRAGMA foreign_keys = ON")

        log("✅", f"  activity table recreated with PRIMARY KEY ({rows_copied} rows preserved)", Colors.GREEN)
        return True

    except sqlite3.OperationalError as e:
        cursor.execute("PRAGMA foreign_keys = ON")
        log("❌", f"  Failed to fix activity PRIMARY KEY: {e}", Colors.RED)
        raise


# ============================================================================
# TASK 20: Add Push Subscription Table for Web Push Notifications
# ============================================================================
def task20_add_push_subscription_table(cursor):
    """Add push_subscription table for web push notifications"""
    log("🔔", "TASK 20: Adding push_subscription table", Colors.BLUE)

    # Check if table already exists
    if check_table_exists(cursor, 'push_subscription'):
        log("⏭️ ", "  push_subscription table already exists", Colors.YELLOW)
        return True

    try:
        # Create the table
        cursor.execute("""
            CREATE TABLE push_subscription (
                id INTEGER NOT NULL PRIMARY KEY,
                admin_id INTEGER NOT NULL,
                endpoint TEXT NOT NULL UNIQUE,
                p256dh_key TEXT NOT NULL,
                auth_key TEXT NOT NULL,
                user_agent VARCHAR(255),
                created_dt DATETIME,
                last_used_dt DATETIME,
                FOREIGN KEY(admin_id) REFERENCES admin (id) ON DELETE CASCADE
            )
        """)
        log("✅", "  Created push_subscription table", Colors.GREEN)

        # Create index on admin_id
        cursor.execute("CREATE INDEX ix_push_subscription_admin ON push_subscription (admin_id)")
        log("✅", "  Created index ix_push_subscription_admin", Colors.GREEN)

        return True

    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to create push_subscription table: {e}", Colors.RED)
        raise


# ============================================================================
# TASK 17: Remove Organizations Table (Migration cb97872b8def)
# ============================================================================
def task17_remove_organizations_table(cursor):
    """Remove unused organizations table and migrate data to Settings"""
    log("🗑️ ", "TASK 17: Removing organizations table", Colors.BLUE)

    # Check if organizations table exists
    if not check_table_exists(cursor, 'organizations'):
        log("⏭️ ", "  Organizations table doesn't exist (already removed)", Colors.YELLOW)

        # Still ensure Settings are populated
        cursor.execute("SELECT COUNT(*) FROM setting WHERE key = 'ORG_NAME'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO setting (key, value) VALUES (?, ?)",
                          ('ORG_NAME', ''))
            log("✅", "  Created empty ORG_NAME placeholder (will be set during deployment)", Colors.GREEN)

        cursor.execute("SELECT COUNT(*) FROM setting WHERE key = 'ORG_ADDRESS'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO setting (key, value) VALUES (?, ?)",
                          ('ORG_ADDRESS', '821 rue des Sables, Rimouski, QC G5L 6Y7'))
            log("✅", "  Created default ORG_ADDRESS in settings", Colors.GREEN)

        return True

    # Migrate organization data to Settings
    log("🔄", "  Migrating organization data to Settings table", Colors.BLUE)
    try:
        cursor.execute("SELECT name, mail_username FROM organizations LIMIT 1")
        org_data = cursor.fetchone()

        if org_data:
            org_name = org_data[0] or ''
            org_email = org_data[1]

            # Insert ORG_NAME
            cursor.execute("SELECT COUNT(*) FROM setting WHERE key = 'ORG_NAME'")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO setting (key, value) VALUES (?, ?)",
                              ('ORG_NAME', org_name))
                log("✅", f"  Migrated ORG_NAME: {org_name}", Colors.GREEN)

            # Insert MAIL_USERNAME if exists
            if org_email:
                cursor.execute("SELECT COUNT(*) FROM setting WHERE key = 'MAIL_USERNAME'")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("INSERT INTO setting (key, value) VALUES (?, ?)",
                                  ('MAIL_USERNAME', org_email))
                    log("✅", f"  Migrated MAIL_USERNAME: {org_email}", Colors.GREEN)
    except Exception as e:
        log("⚠️ ", f"  Could not read organization data: {e}", Colors.YELLOW)
        cursor.execute("SELECT COUNT(*) FROM setting WHERE key = 'ORG_NAME'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO setting (key, value) VALUES (?, ?)",
                          ('ORG_NAME', ''))
            log("✅", "  Created empty ORG_NAME placeholder (will be set during deployment)", Colors.GREEN)

    # Ensure ORG_ADDRESS exists
    cursor.execute("SELECT COUNT(*) FROM setting WHERE key = 'ORG_ADDRESS'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO setting (key, value) VALUES (?, ?)",
                      ('ORG_ADDRESS', '821 rue des Sables, Rimouski, QC G5L 6Y7'))
        log("✅", "  Created ORG_ADDRESS", Colors.GREEN)

    # Drop views that reference organization columns
    log("🔄", "  Dropping views before table modifications", Colors.BLUE)
    cursor.execute("DROP VIEW IF EXISTS monthly_transactions_detail")
    cursor.execute("DROP VIEW IF EXISTS monthly_financial_summary")

    # Remove organization_id from user table if it exists
    if check_column_exists(cursor, 'user', 'organization_id'):
        log("🔄", "  Removing organization_id from user table", Colors.BLUE)
        try:
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute("""
                CREATE TABLE user_new (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100),
                    phone_number VARCHAR(20),
                    email_opt_out BOOLEAN NOT NULL DEFAULT 0
                )
            """)
            cursor.execute("""
                INSERT INTO user_new (id, name, email, phone_number, email_opt_out)
                SELECT id, name, email, phone_number, COALESCE(email_opt_out, 0) FROM user
            """)
            cursor.execute("DROP TABLE user")
            cursor.execute("ALTER TABLE user_new RENAME TO user")
            cursor.execute("PRAGMA foreign_keys = ON")
            log("✅", "  Removed organization_id from user table", Colors.GREEN)
        except Exception as e:
            cursor.execute("PRAGMA foreign_keys = ON")
            log("❌", f"  Failed to modify user table: {e}", Colors.RED)
            raise

    # Remove organization_id from activity table if it exists
    if check_column_exists(cursor, 'activity', 'organization_id'):
        log("🔄", "  Removing organization_id from activity table", Colors.BLUE)
        try:
            cursor.execute("PRAGMA foreign_keys = OFF")

            # Get all columns except organization_id
            cursor.execute("PRAGMA table_info(activity)")
            columns = [row[1] for row in cursor.fetchall() if row[1] != 'organization_id']
            columns_str = ', '.join(columns)

            # Create new table WITH proper PRIMARY KEY constraint (not CREATE TABLE AS SELECT which loses constraints)
            cursor.execute("""
                CREATE TABLE activity_new (
                    id INTEGER NOT NULL PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT,
                    description TEXT,
                    sessions_included INTEGER,
                    price_per_user REAL,
                    goal_users INTEGER,
                    goal_revenue REAL,
                    cost_to_run REAL,
                    created_by INTEGER,
                    created_dt DATETIME,
                    status TEXT,
                    payment_instructions TEXT,
                    start_date DATETIME,
                    end_date DATETIME,
                    image_filename TEXT,
                    email_templates TEXT,
                    logo_filename TEXT,
                    location_address_raw TEXT,
                    location_address_formatted TEXT,
                    location_coordinates TEXT,
                    FOREIGN KEY(created_by) REFERENCES admin(id)
                )
            """)

            # Copy data
            cursor.execute(f"INSERT INTO activity_new ({columns_str}) SELECT {columns_str} FROM activity")

            cursor.execute("DROP TABLE activity")
            cursor.execute("ALTER TABLE activity_new RENAME TO activity")
            cursor.execute("PRAGMA foreign_keys = ON")
            log("✅", "  Removed organization_id from activity table", Colors.GREEN)
        except Exception as e:
            cursor.execute("PRAGMA foreign_keys = ON")
            log("❌", f"  Failed to modify activity table: {e}", Colors.RED)
            raise

    # Finally, drop organizations table
    try:
        cursor.execute("DROP TABLE organizations")
        log("✅", "  Dropped organizations table", Colors.GREEN)
    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to drop organizations table: {e}", Colors.RED)
        raise

    return True


# ============================================================================
# TASK 21: Fix AP Fiscal Year Filtering for Unpaid Expenses
# ============================================================================
def task21_fix_ap_fiscal_year_filtering(cursor):
    """Fix AP fiscal year filtering - unpaid expenses use effective date (payment_date > due_date > date)

    This fixes a bug where unpaid expenses with a bill date in a previous fiscal year
    but a payment_date in the current fiscal year would not appear in AP for the current FY.

    Uses Cash Flow Planning approach: unpaid bills appear in the fiscal year when payment
    is EXPECTED (based on payment_date/due_date), which is better for budget planning.
    """
    log("💰", "TASK 21: Fixing AP fiscal year filtering in views", Colors.BLUE)

    # Drop both views first (they will be recreated with the fix)
    try:
        cursor.execute("DROP VIEW IF EXISTS monthly_transactions_detail")
        cursor.execute("DROP VIEW IF EXISTS monthly_financial_summary")
        log("🔄", "  Dropped existing views", Colors.BLUE)
    except:
        pass

    # Create monthly_transactions_detail WITH FIX for unpaid expenses
    try:
        cursor.execute("""
            CREATE VIEW monthly_transactions_detail AS
            SELECT
                strftime('%Y-%m', COALESCE(p.paid_date, p.created_dt)) as month,
                a.name as project,
                'Income' as transaction_type,
                COALESCE(p.paid_date, p.created_dt) as transaction_date,
                'Passport Sales' as account,
                u.name as customer,
                NULL as vendor,
                p.notes as memo,
                p.sold_amt as amount,
                CASE WHEN p.paid = 1 THEN 'Paid' ELSE 'Unpaid (AR)' END as payment_status,
                'Passport System' as entered_by
            FROM passport p
            JOIN activity a ON p.activity_id = a.id
            LEFT JOIN user u ON p.user_id = u.id

            UNION ALL

            SELECT
                strftime('%Y-%m', i.date) as month,
                a.name as project,
                'Income' as transaction_type,
                i.date as transaction_date,
                i.category as account,
                NULL as customer,
                NULL as vendor,
                i.note as memo,
                i.amount,
                CASE
                    WHEN i.payment_status = 'received' THEN 'Paid'
                    WHEN i.payment_status = 'pending' THEN 'Unpaid (AR)'
                    ELSE 'Unpaid (AR)'
                END as payment_status,
                COALESCE(i.created_by, 'System') as entered_by
            FROM income i
            JOIN activity a ON i.activity_id = a.id

            UNION ALL

            -- FIX: For unpaid expenses, use effective date (payment_date > due_date > date)
            SELECT
                strftime('%Y-%m', CASE
                    WHEN e.payment_status = 'unpaid'
                    THEN COALESCE(e.payment_date, e.due_date, e.date)
                    ELSE e.date
                END) as month,
                a.name as project,
                'Expense' as transaction_type,
                CASE
                    WHEN e.payment_status = 'unpaid'
                    THEN COALESCE(e.payment_date, e.due_date, e.date)
                    ELSE e.date
                END as transaction_date,
                e.category as account,
                NULL as customer,
                NULL as vendor,
                e.description as memo,
                e.amount,
                CASE
                    WHEN e.payment_status = 'paid' THEN 'Paid'
                    WHEN e.payment_status = 'unpaid' THEN 'Unpaid (AP)'
                    ELSE 'Unpaid (AP)'
                END as payment_status,
                COALESCE(e.created_by, 'System') as entered_by
            FROM expense e
            JOIN activity a ON e.activity_id = a.id

            ORDER BY month DESC, transaction_date DESC
        """)
        log("✅", "  Created monthly_transactions_detail view (with AP fix)", Colors.GREEN)
    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to create transactions detail view: {e}", Colors.RED)
        raise

    # Create monthly_financial_summary WITH FIX for unpaid expenses
    try:
        cursor.execute("""
            CREATE VIEW monthly_financial_summary AS
            WITH
            -- Get ALL distinct month+activity combinations from ALL transaction sources
            all_month_activity AS (
                SELECT DISTINCT
                    strftime('%Y-%m', paid_date) as month,
                    activity_id
                FROM passport
                WHERE paid = 1 AND paid_date IS NOT NULL

                UNION

                SELECT DISTINCT
                    strftime('%Y-%m', COALESCE(paid_date, created_dt)) as month,
                    activity_id
                FROM passport
                WHERE paid = 0

                UNION

                SELECT DISTINCT
                    strftime('%Y-%m', date) as month,
                    activity_id
                FROM income
                WHERE payment_status = 'received'

                UNION

                SELECT DISTINCT
                    strftime('%Y-%m', date) as month,
                    activity_id
                FROM income
                WHERE payment_status = 'pending'

                UNION

                SELECT DISTINCT
                    strftime('%Y-%m', date) as month,
                    activity_id
                FROM expense
                WHERE payment_status = 'paid'

                UNION

                -- FIX: For unpaid expenses, use effective date (payment_date > due_date > date)
                SELECT DISTINCT
                    strftime('%Y-%m', COALESCE(payment_date, due_date, date)) as month,
                    activity_id
                FROM expense
                WHERE payment_status = 'unpaid'
            ),
            monthly_passports_cash AS (
                SELECT
                    strftime('%Y-%m', paid_date) as month,
                    activity_id,
                    SUM(sold_amt) as passport_sales_cash
                FROM passport
                WHERE paid = 1 AND paid_date IS NOT NULL
                GROUP BY month, activity_id
            ),
            monthly_passports_ar AS (
                SELECT
                    strftime('%Y-%m', COALESCE(paid_date, created_dt)) as month,
                    activity_id,
                    SUM(sold_amt) as passport_sales_ar
                FROM passport
                WHERE paid = 0
                GROUP BY month, activity_id
            ),
            monthly_income_cash AS (
                SELECT
                    strftime('%Y-%m', date) as month,
                    activity_id,
                    SUM(amount) as other_income_cash
                FROM income
                WHERE payment_status = 'received'
                GROUP BY month, activity_id
            ),
            monthly_income_ar AS (
                SELECT
                    strftime('%Y-%m', date) as month,
                    activity_id,
                    SUM(amount) as other_income_ar
                FROM income
                WHERE payment_status = 'pending'
                GROUP BY month, activity_id
            ),
            monthly_expenses_cash AS (
                SELECT
                    strftime('%Y-%m', date) as month,
                    activity_id,
                    SUM(amount) as expenses_cash
                FROM expense
                WHERE payment_status = 'paid'
                GROUP BY month, activity_id
            ),
            -- FIX: For unpaid expenses, use effective date (payment_date > due_date > date)
            monthly_expenses_ap AS (
                SELECT
                    strftime('%Y-%m', COALESCE(payment_date, due_date, date)) as month,
                    activity_id,
                    SUM(amount) as expenses_ap
                FROM expense
                WHERE payment_status = 'unpaid'
                GROUP BY strftime('%Y-%m', COALESCE(payment_date, due_date, date)), activity_id
            )
            SELECT
                ma.month,
                ma.activity_id,
                a.name as account,

                COALESCE(pc.passport_sales_cash, 0) as passport_sales,
                COALESCE(ic.other_income_cash, 0) as other_income,
                COALESCE(pc.passport_sales_cash, 0) + COALESCE(ic.other_income_cash, 0) as cash_received,
                COALESCE(ec.expenses_cash, 0) as cash_paid,
                (COALESCE(pc.passport_sales_cash, 0) + COALESCE(ic.other_income_cash, 0) - COALESCE(ec.expenses_cash, 0)) as net_cash_flow,

                COALESCE(par.passport_sales_ar, 0) as passport_ar,
                COALESCE(iar.other_income_ar, 0) as other_income_ar,
                COALESCE(par.passport_sales_ar, 0) + COALESCE(iar.other_income_ar, 0) as accounts_receivable,
                COALESCE(eap.expenses_ap, 0) as accounts_payable,

                (COALESCE(pc.passport_sales_cash, 0) + COALESCE(par.passport_sales_ar, 0) +
                 COALESCE(ic.other_income_cash, 0) + COALESCE(iar.other_income_ar, 0)) as total_revenue,
                (COALESCE(ec.expenses_cash, 0) + COALESCE(eap.expenses_ap, 0)) as total_expenses,
                ((COALESCE(pc.passport_sales_cash, 0) + COALESCE(par.passport_sales_ar, 0) +
                  COALESCE(ic.other_income_cash, 0) + COALESCE(iar.other_income_ar, 0)) -
                 (COALESCE(ec.expenses_cash, 0) + COALESCE(eap.expenses_ap, 0))) as net_income

            FROM all_month_activity ma
            JOIN activity a ON ma.activity_id = a.id
            LEFT JOIN monthly_passports_cash pc ON ma.month = pc.month AND ma.activity_id = pc.activity_id
            LEFT JOIN monthly_passports_ar par ON ma.month = par.month AND ma.activity_id = par.activity_id
            LEFT JOIN monthly_income_cash ic ON ma.month = ic.month AND ma.activity_id = ic.activity_id
            LEFT JOIN monthly_income_ar iar ON ma.month = iar.month AND ma.activity_id = iar.activity_id
            LEFT JOIN monthly_expenses_cash ec ON ma.month = ec.month AND ma.activity_id = ec.activity_id
            LEFT JOIN monthly_expenses_ap eap ON ma.month = eap.month AND ma.activity_id = eap.activity_id
            ORDER BY ma.month DESC, a.name
        """)
        log("✅", "  Created monthly_financial_summary view (with AP fix)", Colors.GREEN)
        return True
    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to create financial summary view: {e}", Colors.RED)
        raise


# ============================================================================
# TASK 22: Add Passport Renewal Setting to Activity
# ============================================================================
def task22_add_passport_renewal_setting(cursor):
    """Add offer_passport_renewal column to activity table"""
    log("🔄", "TASK 22: Adding passport renewal setting to Activity", Colors.BLUE)

    if not check_table_exists(cursor, 'activity'):
        log("⏭️ ", "  Activity table doesn't exist, skipping", Colors.YELLOW)
        return True

    if check_column_exists(cursor, 'activity', 'offer_passport_renewal'):
        log("⏭️ ", "  Column 'offer_passport_renewal' already exists", Colors.YELLOW)
        return True

    try:
        cursor.execute("ALTER TABLE activity ADD COLUMN offer_passport_renewal BOOLEAN DEFAULT 0 NOT NULL")
        log("✅", "  Added column 'offer_passport_renewal' (default: disabled)", Colors.GREEN)
        return True
    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to add offer_passport_renewal: {e}", Colors.RED)
        raise


# ============================================================================
# TASK 23: Add email_uid to EbankPayment for reliable email move
# ============================================================================
def task23_add_email_uid_column(cursor):
    """Add email_uid column to ebank_payment table for reliable email move operations"""
    log("📧", "TASK 23: Adding email_uid to ebank_payment table", Colors.BLUE)

    if not check_table_exists(cursor, 'ebank_payment'):
        log("⏭️ ", "  ebank_payment table doesn't exist, skipping", Colors.YELLOW)
        return True

    if check_column_exists(cursor, 'ebank_payment', 'email_uid'):
        log("⏭️ ", "  Column 'email_uid' already exists", Colors.YELLOW)
        return True

    try:
        cursor.execute("ALTER TABLE ebank_payment ADD COLUMN email_uid VARCHAR(50)")
        log("✅", "  Added column 'email_uid' to ebank_payment", Colors.GREEN)

        # Info about existing records
        cursor.execute("SELECT COUNT(*) FROM ebank_payment WHERE email_uid IS NULL")
        null_count = cursor.fetchone()[0]

        if null_count > 0:
            log("ℹ️ ", f"  {null_count} existing payment(s) will have NULL email_uid", Colors.BLUE)
            log("ℹ️ ", "  Future payments will have UID stored for reliable email move", Colors.BLUE)

        return True

    except sqlite3.OperationalError as e:
        log("❌", f"  Failed to add email_uid column: {e}", Colors.RED)
        raise


# ============================================================================
# TASK 24: Add Workflow Type and Quantity Limit Fields
# ============================================================================
def task25_add_signup_code_column(cursor):
    """Add signup_code column to Signup table for reliable payment matching"""
    log("🔄", "TASK 25: Adding signup_code column for payment matching", Colors.BLUE)

    if check_column_exists(cursor, 'signup', 'signup_code'):
        log("⏭️ ", "  signup_code column already exists", Colors.YELLOW)
    else:
        try:
            cursor.execute("ALTER TABLE signup ADD COLUMN signup_code VARCHAR(20)")
            log("✅", "  Added signup_code column", Colors.GREEN)
        except sqlite3.OperationalError as e:
            log("❌", f"  Failed to add signup_code: {e}", Colors.RED)
            raise

    # Backfill existing signups with codes (format: MP-INS-0001234)
    log("🔄", "  Backfilling existing signups with codes...", Colors.BLUE)
    cursor.execute("UPDATE signup SET signup_code = 'MP-INS-' || printf('%07d', id) WHERE signup_code IS NULL")
    rows_updated = cursor.rowcount
    log("✅", f"  Backfilled {rows_updated} signups with codes", Colors.GREEN)

    return True


def task24_add_workflow_quantity_fields(cursor):
    """Add workflow type and quantity limit fields to Activity and Signup tables"""
    log("🔄", "TASK 24: Adding workflow type and quantity limit fields", Colors.BLUE)

    # Activity table fields
    activity_fields = [
        ('workflow_type', "VARCHAR(50) DEFAULT 'approval_first'"),
        ('allow_quantity_selection', "BOOLEAN DEFAULT 0"),
        ('is_quantity_limited', "BOOLEAN DEFAULT 0"),
        ('max_sessions', "INTEGER"),
        ('show_remaining_quantity', "BOOLEAN DEFAULT 0"),
    ]

    # Signup table fields
    signup_fields = [
        ('requested_sessions', "INTEGER DEFAULT 1"),
        ('requested_amount', "FLOAT DEFAULT 0.0"),
    ]

    added = 0
    skipped = 0

    # Add Activity fields
    for field_name, field_def in activity_fields:
        if check_column_exists(cursor, 'activity', field_name):
            log("⏭️ ", f"  Activity.{field_name} already exists", Colors.YELLOW)
            skipped += 1
        else:
            try:
                cursor.execute(f"ALTER TABLE activity ADD COLUMN {field_name} {field_def}")
                log("✅", f"  Added Activity.{field_name}", Colors.GREEN)
                added += 1
            except sqlite3.OperationalError as e:
                log("❌", f"  Failed to add Activity.{field_name}: {e}", Colors.RED)
                raise

    # Add Signup fields
    for field_name, field_def in signup_fields:
        if check_column_exists(cursor, 'signup', field_name):
            log("⏭️ ", f"  Signup.{field_name} already exists", Colors.YELLOW)
            skipped += 1
        else:
            try:
                cursor.execute(f"ALTER TABLE signup ADD COLUMN {field_name} {field_def}")
                log("✅", f"  Added Signup.{field_name}", Colors.GREEN)
                added += 1
            except sqlite3.OperationalError as e:
                log("❌", f"  Failed to add Signup.{field_name}: {e}", Colors.RED)
                raise

    log("📊", f"  Summary: {added} added, {skipped} already existed")
    return True


# ============================================================================
# MAIN UPGRADE FUNCTION
# ============================================================================
def main():
    """Run all upgrade tasks"""
    separator()
    log("🚀", f"{Colors.BOLD}MASTER PRODUCTION DATABASE UPGRADE{Colors.RESET}", Colors.BLUE)
    separator()
    log("📁", f"Database: {DB_PATH}")
    log("🕐", f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    separator()

    if not os.path.exists(DB_PATH):
        log("❌", f"Database not found at {DB_PATH}", Colors.RED)
        sys.exit(1)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tasks = [
        ("Schema Changes", task1_add_location_fields),
        ("Payment Status Columns", task13_add_payment_status_columns),
        ("Data Backfill", task2_backfill_financial_records),
        ("Foreign Keys", task3_fix_redemption_cascade),
        ("Survey Templates", task4_add_french_survey),
        ("Email Templates", task5_fix_email_templates),
        ("Verification", task6_verify_schema),
        ("Payment Email Dates", task7_add_email_received_date),
        ("ReminderLog CASCADE", task8_fix_reminderlog_cascade),
        ("Passport Deletion FKs", task9_fix_passport_deletion_fks),
        ("PassportType Deletion FKs", task10_fix_passport_type_deletion_fks),
        ("Drop Old Pass Table", task11_drop_old_pass_table),
        ("Survey Deletion FK", task12_fix_survey_deletion_fk),
        ("Custom Payment Flag", task14_add_custom_payment_flag),
        ("AI Answer Column", task16_add_ai_answer_column),
        ("Stripe Subscription Settings", task18_add_stripe_subscription_settings),
        ("Remove Organizations", task17_remove_organizations_table),
        ("Activity PRIMARY KEY Fix", task19_fix_activity_primary_key),
        ("Push Subscription Table", task20_add_push_subscription_table),
        ("AP Fiscal Year Fix", task21_fix_ap_fiscal_year_filtering),  # Creates views with AP fix
        ("Passport Renewal Setting", task22_add_passport_renewal_setting),
        ("Email UID for Payment Move", task23_add_email_uid_column),
        ("Workflow and Quantity Fields", task24_add_workflow_quantity_fields),
        ("Signup Code for Payment Matching", task25_add_signup_code_column),
    ]

    completed = 0
    failed = 0

    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        log("🔄", "Transaction started")
        print()

        # Run all tasks
        for task_name, task_func in tasks:
            try:
                result = task_func(cursor)
                if result:
                    completed += 1
                print()  # Blank line between tasks
            except Exception as e:
                log("❌", f"Task '{task_name}' failed: {e}", Colors.RED)
                failed += 1
                raise

        # Commit transaction
        conn.commit()
        log("✅", "Transaction committed successfully", Colors.GREEN)
        print()

        # Final summary
        separator()
        log("🎉", f"{Colors.BOLD}UPGRADE COMPLETED SUCCESSFULLY!{Colors.RESET}", Colors.GREEN)
        separator()
        log("📊", f"Tasks completed: {len(tasks)}/{len(tasks)}")
        log("🕐", f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        separator()

        print()
        log("📝", f"{Colors.BOLD}NEXT STEPS:{Colors.RESET}", Colors.BLUE)
        log("1️⃣ ", "Fix migration tracking:")
        print(f"     {Colors.YELLOW}sqlite3 instance/minipass.db \"UPDATE alembic_version SET version_num = 'c8f3a2d91b45';\" {Colors.RESET}")
        log("2️⃣ ", "Restart your application container")
        log("3️⃣ ", "Test login and verify all features work")
        separator()

        return True

    except Exception as e:
        # Rollback on error
        conn.rollback()
        separator("!")
        log("❌", f"{Colors.BOLD}UPGRADE FAILED{Colors.RESET}", Colors.RED)
        separator("!")
        log("❌", f"Error: {str(e)}", Colors.RED)
        log("↩️ ", "Transaction rolled back - database unchanged")
        log("💡", "Database is safe - no partial changes applied")
        separator("!")
        return False

    finally:
        conn.close()
        log("🔒", "Database connection closed")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
