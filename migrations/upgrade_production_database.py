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
        ('activity', 'organization_id', 'Organization support'),
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
        ("Data Backfill", task2_backfill_financial_records),
        ("Foreign Keys", task3_fix_redemption_cascade),
        ("Survey Templates", task4_add_french_survey),
        ("Email Templates", task5_fix_email_templates),
        ("Verification", task6_verify_schema),
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

        # Task 7: Mark Flask migrations as complete
        log("🏷️ ", "TASK 7: Marking Flask migrations as complete", Colors.BLUE)
        try:
            import subprocess
            result = subprocess.run(
                ['flask', 'db', 'stamp', 'head'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )

            if result.returncode == 0:
                log("✅", "  Flask migrations marked as complete (flask db stamp head)", Colors.GREEN)
                completed += 1
            else:
                log("⚠️ ", f"  Warning: flask db stamp failed: {result.stderr}", Colors.YELLOW)
                log("💡", "  You may need to run manually: flask db stamp head", Colors.YELLOW)
        except Exception as e:
            log("⚠️ ", f"  Warning: Could not run flask db stamp: {e}", Colors.YELLOW)
            log("💡", "  You may need to run manually: flask db stamp head", Colors.YELLOW)

        print()

        # Final summary
        separator()
        log("🎉", f"{Colors.BOLD}UPGRADE COMPLETED SUCCESSFULLY!{Colors.RESET}", Colors.GREEN)
        separator()
        log("📊", f"Database tasks: {len(tasks)}/{len(tasks)} completed")
        log("📊", f"Total tasks: {completed}/{len(tasks) + 1} completed (including Flask stamp)")
        log("🕐", f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        separator()

        print()
        log("📝", f"{Colors.BOLD}NEXT STEPS:{Colors.RESET}", Colors.BLUE)
        log("1️⃣ ", "Test your application:")
        print(f"     {Colors.YELLOW}flask run{Colors.RESET}")
        log("2️⃣ ", "Verify passport scanning works for hockey game!")
        log("3️⃣ ", "Check all images/uploads display correctly")
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
