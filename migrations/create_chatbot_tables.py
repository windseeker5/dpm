#!/usr/bin/env python3
"""
Create chatbot database tables manually
"""
import sqlite3
import os
from datetime import datetime

def create_chatbot_tables():
    """Create the chatbot tables in the database"""
    
    # Determine database path (same logic as app.py)
    env = os.environ.get("FLASK_ENV", "dev").lower()
    db_filename = "dev_database.db" if env == "dev" else "prod_database.db"
    db_path = os.path.join("instance", db_filename)
    
    print(f"🗃️  Creating chatbot tables in: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create ChatConversation table
        print("   Creating chat_conversation table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_conversation (
                id INTEGER PRIMARY KEY,
                admin_email VARCHAR(150) NOT NULL,
                session_token VARCHAR(32) UNIQUE NOT NULL,
                created_at DATETIME DEFAULT (datetime('now')),
                updated_at DATETIME DEFAULT (datetime('now')),
                status VARCHAR(20) DEFAULT 'active'
            )
        """)
        
        # Create ChatMessage table
        print("   Creating chat_message table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_message (
                id INTEGER PRIMARY KEY,
                conversation_id INTEGER NOT NULL,
                message_type VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                sql_query TEXT,
                query_result TEXT,
                ai_provider VARCHAR(50),
                ai_model VARCHAR(100),
                tokens_used INTEGER DEFAULT 0,
                cost_cents INTEGER DEFAULT 0,
                response_time_ms INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT (datetime('now')),
                FOREIGN KEY (conversation_id) REFERENCES chat_conversation (id)
            )
        """)
        
        # Create QueryLog table
        print("   Creating query_log table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_log (
                id INTEGER PRIMARY KEY,
                admin_email VARCHAR(150) NOT NULL,
                original_question TEXT NOT NULL,
                generated_sql TEXT NOT NULL,
                execution_status VARCHAR(20) NOT NULL,
                execution_time_ms INTEGER,
                rows_returned INTEGER DEFAULT 0,
                error_message TEXT,
                ai_provider VARCHAR(50),
                ai_model VARCHAR(100),
                tokens_used INTEGER DEFAULT 0,
                cost_cents INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT (datetime('now'))
            )
        """)
        
        # Create ChatUsage table
        print("   Creating chat_usage table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_usage (
                id INTEGER PRIMARY KEY,
                admin_email VARCHAR(150) NOT NULL,
                date DATE NOT NULL,
                total_queries INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                total_cost_cents INTEGER DEFAULT 0,
                provider_usage TEXT,
                created_at DATETIME DEFAULT (datetime('now')),
                updated_at DATETIME DEFAULT (datetime('now')),
                UNIQUE(admin_email, date)
            )
        """)
        
        # Create indexes for performance
        print("   Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS ix_chat_conversation_admin ON chat_conversation (admin_email)",
            "CREATE INDEX IF NOT EXISTS ix_chat_conversation_token ON chat_conversation (session_token)",
            "CREATE INDEX IF NOT EXISTS ix_chat_conversation_status ON chat_conversation (status)",
            "CREATE INDEX IF NOT EXISTS ix_chat_message_conversation ON chat_message (conversation_id)",
            "CREATE INDEX IF NOT EXISTS ix_chat_message_type ON chat_message (message_type)",
            "CREATE INDEX IF NOT EXISTS ix_chat_message_created ON chat_message (created_at)",
            "CREATE INDEX IF NOT EXISTS ix_query_log_admin ON query_log (admin_email)",
            "CREATE INDEX IF NOT EXISTS ix_query_log_status ON query_log (execution_status)",
            "CREATE INDEX IF NOT EXISTS ix_query_log_created ON query_log (created_at)",
            "CREATE INDEX IF NOT EXISTS ix_query_log_provider ON query_log (ai_provider)",
            "CREATE INDEX IF NOT EXISTS ix_chat_usage_date ON chat_usage (date)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("✅ All chatbot tables created successfully!")
        
        # Verify tables exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'chat_%'")
        tables = cursor.fetchall()
        conn.close()
        
        print(f"✅ Verified {len(tables)} chatbot tables exist:")
        for table in tables:
            print(f"   - {table[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating AI Analytics Chatbot Database Tables")
    print("=" * 55)
    
    success = create_chatbot_tables()
    
    if success:
        print("\n🎉 Database setup complete!")
        print("✅ Your chatbot should now work correctly.")
        print("🔗 Try accessing: http://localhost:8890/chatbot/")
    else:
        print("\n❌ Database setup failed!")
        print("💡 Make sure your Flask app has been run at least once to create the database.")