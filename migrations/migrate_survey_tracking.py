#!/usr/bin/env python3
"""
Migration script to add invitation tracking fields to SurveyResponse table
"""

import sqlite3
from datetime import datetime, timezone

def migrate_survey_tracking():
    """Add new tracking fields to SurveyResponse table"""
    
    db_path = "instance/minipass.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Survey Tracking Migration")
        print("=" * 40)
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(survey_response)")
        columns = [column[1] for column in cursor.fetchall()]
        
        migrations_needed = []
        
        if 'invited_dt' not in columns:
            migrations_needed.append('invited_dt')
        
        if 'created_dt' not in columns:
            migrations_needed.append('created_dt')
            
        # Check table schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='survey_response'")
        result = cursor.fetchone()
        table_sql = result[0] if result else ""
        
        if migrations_needed:
            print(f"Adding missing columns: {', '.join(migrations_needed)}")
            
            # Add missing columns
            if 'invited_dt' in migrations_needed:
                cursor.execute("ALTER TABLE survey_response ADD COLUMN invited_dt DATETIME")
                print("✅ Added invited_dt column")
            
            if 'created_dt' in migrations_needed:
                cursor.execute("ALTER TABLE survey_response ADD COLUMN created_dt DATETIME")
                print("✅ Added created_dt column")
                
                # Set created_dt for existing records (use started_dt as fallback)
                cursor.execute("""
                    UPDATE survey_response 
                    SET created_dt = COALESCE(started_dt, datetime('now'))
                    WHERE created_dt IS NULL
                """)
                print("✅ Set created_dt for existing records")
            
            # Make started_dt nullable for existing records without changing structure
            # (SQLite doesn't support modifying column constraints easily)
            
            conn.commit()
            print("✅ Migration completed successfully")
            
        else:
            print("✅ No migration needed - all columns already exist")
            
        # Show current table status
        cursor.execute("SELECT COUNT(*) FROM survey_response")
        total_responses = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM survey_response WHERE invited_dt IS NOT NULL")
        invited_responses = cursor.fetchone()[0]
        
        print(f"\n📊 Current Status:")
        print(f"Total responses: {total_responses}")
        print(f"Responses with invitation tracking: {invited_responses}")
        
        if total_responses > invited_responses:
            print(f"⚠️  {total_responses - invited_responses} responses don't have invitation tracking")
            print("   These were likely created before the tracking system was implemented")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
        
    return True

if __name__ == "__main__":
    migrate_survey_tracking()