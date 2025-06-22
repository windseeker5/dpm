#!/usr/bin/env python3
"""
Simple script to create survey tables in the existing database
"""
import sqlite3
import os

# Database path
db_path = "instance/dev_database.db"  # Development database

def create_survey_tables():
    """Create the survey system tables"""
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("📋 Creating survey system tables...")
        
        # Create survey_template table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS survey_template (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(150) NOT NULL,
                description TEXT,
                questions TEXT,
                created_by INTEGER,
                created_dt DATETIME,
                status VARCHAR(50),
                FOREIGN KEY(created_by) REFERENCES admin (id)
            )
        """)
        
        # Create survey table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS survey (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                template_id INTEGER NOT NULL,
                passport_type_id INTEGER,
                name VARCHAR(150) NOT NULL,
                description TEXT,
                survey_token VARCHAR(32) NOT NULL UNIQUE,
                created_by INTEGER,
                created_dt DATETIME,
                status VARCHAR(50),
                email_sent BOOLEAN,
                email_sent_dt DATETIME,
                FOREIGN KEY(activity_id) REFERENCES activity (id),
                FOREIGN KEY(template_id) REFERENCES survey_template (id),
                FOREIGN KEY(passport_type_id) REFERENCES passport_type (id),
                FOREIGN KEY(created_by) REFERENCES admin (id)
            )
        """)
        
        # Create survey_response table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS survey_response (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                survey_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                passport_id INTEGER,
                response_token VARCHAR(32) NOT NULL UNIQUE,
                responses TEXT,
                completed BOOLEAN,
                completed_dt DATETIME,
                started_dt DATETIME,
                ip_address VARCHAR(45),
                user_agent TEXT,
                FOREIGN KEY(survey_id) REFERENCES survey (id),
                FOREIGN KEY(user_id) REFERENCES user (id),
                FOREIGN KEY(passport_id) REFERENCES passport (id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_survey_token ON survey (survey_token)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_survey_response_token ON survey_response (response_token)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_survey_activity ON survey (activity_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_survey_response_survey ON survey_response (survey_id)
        """)
        
        # Commit changes
        conn.commit()
        
        print("✅ Survey tables created successfully!")
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'survey%'")
        tables = cursor.fetchall()
        
        print(f"📊 Survey tables in database: {[table[0] for table in tables]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    print("🔧 Setting up survey system database tables...")
    success = create_survey_tables()
    
    if success:
        print("\n🎉 Database setup complete!")
        print("\nNext steps:")
        print("1. Restart your Flask app")
        print("2. Navigate to an activity dashboard")
        print("3. Click the 'Survey' button to test")
    else:
        print("\n❌ Database setup failed")
        print("Please check your database path and permissions")