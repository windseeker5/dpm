#!/usr/bin/env python3
"""
Initialize default survey templates in the database
"""
import sqlite3
import json
from datetime import datetime, timezone

# Database path
db_path = "instance/dev_database.db"

def setup_default_templates():
    """Create default survey templates"""
    
    # Default survey template
    default_template = {
        "questions": [
            {
                "id": 1,
                "type": "multiple_choice",
                "question": "How would you rate your overall experience?",
                "options": ["Excellent", "Good", "Fair", "Poor"],
                "required": True
            },
            {
                "id": 2,
                "type": "multiple_choice",
                "question": "How likely are you to recommend this activity to others?",
                "options": ["Very likely", "Likely", "Unlikely", "Very unlikely"],
                "required": True
            },
            {
                "id": 3,
                "type": "multiple_choice",
                "question": "What did you like most about this activity?",
                "options": ["Instruction quality", "Facilities", "Organization", "Other participants"],
                "required": False
            },
            {
                "id": 4,
                "type": "multiple_choice",
                "question": "Would you participate in this activity again?",
                "options": ["Definitely", "Probably", "Maybe", "No"],
                "required": True
            },
            {
                "id": 5,
                "type": "open_ended",
                "question": "Any additional feedback or suggestions for improvement?",
                "required": False,
                "max_length": 500
            }
        ]
    }
    
    # Quick feedback template
    quick_template = {
        "questions": [
            {
                "id": 1,
                "type": "multiple_choice",
                "question": "How satisfied were you with this activity?",
                "options": ["Very satisfied", "Satisfied", "Neutral", "Dissatisfied"],
                "required": True
            },
            {
                "id": 2,
                "type": "multiple_choice",
                "question": "Would you recommend this to a friend?",
                "options": ["Yes", "Maybe", "No"],
                "required": True
            },
            {
                "id": 3,
                "type": "open_ended",
                "question": "What could we improve?",
                "required": False,
                "max_length": 300
            }
        ]
    }
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("📋 Setting up default survey templates...")
        
        # Check if templates already exist
        cursor.execute("SELECT COUNT(*) FROM survey_template")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"ℹ️  Found {count} existing templates, skipping creation")
            return True
        
        # Insert default template
        cursor.execute("""
            INSERT INTO survey_template (name, description, questions, status, created_dt)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Activity Feedback Survey",
            "Standard feedback survey for activity participants",
            json.dumps(default_template),
            "active",
            datetime.now(timezone.utc).isoformat()
        ))
        
        # Insert quick template
        cursor.execute("""
            INSERT INTO survey_template (name, description, questions, status, created_dt)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Quick Feedback Survey",
            "Short 3-question survey for quick feedback collection",
            json.dumps(quick_template),
            "active",
            datetime.now(timezone.utc).isoformat()
        ))
        
        conn.commit()
        
        print("✅ Default survey templates created successfully!")
        
        # Verify templates were created
        cursor.execute("SELECT name, description FROM survey_template")
        templates = cursor.fetchall()
        
        print("\n📊 Available templates:")
        for name, desc in templates:
            print(f"  • {name}: {desc}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up templates: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    print("🔧 Setting up default survey templates...")
    success = setup_default_templates()
    
    if success:
        print("\n🎉 Template setup complete!")
        print("\nYour survey system is now ready to use!")
        print("Navigate to an activity dashboard and click 'Survey' to test.")
    else:
        print("\n❌ Template setup failed")