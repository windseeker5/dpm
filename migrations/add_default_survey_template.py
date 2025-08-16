#!/usr/bin/env python3
"""
Migration script to add default "Post-Activity Feedback" survey template
This template provides a universal set of questions suitable for any activity type
"""

import json
import sys
import os
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import SurveyTemplate

def create_default_template():
    """Create and insert the default Post-Activity Feedback template"""
    
    # Check if default template already exists
    existing = SurveyTemplate.query.filter_by(name="Post-Activity Feedback").first()
    if existing:
        print("Default template 'Post-Activity Feedback' already exists. Skipping...")
        return
    
    # Define the default questions
    questions = {
        "questions": [
            {
                "id": 1,
                "text": "How would you rate your overall satisfaction with this activity?",
                "type": "rating",
                "required": True,
                "options": {
                    "min": 1,
                    "max": 5,
                    "labels": {
                        "1": "Very Dissatisfied",
                        "2": "Dissatisfied", 
                        "3": "Neutral",
                        "4": "Satisfied",
                        "5": "Very Satisfied"
                    }
                }
            },
            {
                "id": 2,
                "text": "How would you rate the instructor/facilitator?",
                "type": "rating",
                "required": True,
                "options": {
                    "min": 1,
                    "max": 5,
                    "labels": {
                        "1": "Poor",
                        "2": "Fair",
                        "3": "Good",
                        "4": "Very Good",
                        "5": "Excellent"
                    }
                }
            },
            {
                "id": 3,
                "text": "What did you enjoy most about this activity?",
                "type": "text",
                "required": False,
                "options": {
                    "placeholder": "Please share what you enjoyed...",
                    "maxLength": 500
                }
            },
            {
                "id": 4,
                "text": "What aspects could be improved?",
                "type": "text",
                "required": False,
                "options": {
                    "placeholder": "Your suggestions help us improve...",
                    "maxLength": 500
                }
            },
            {
                "id": 5,
                "text": "Would you recommend this activity to others?",
                "type": "radio",
                "required": True,
                "options": {
                    "choices": [
                        {"value": "yes", "label": "Yes, definitely!"},
                        {"value": "maybe", "label": "Maybe"},
                        {"value": "no", "label": "No"}
                    ]
                }
            }
        ],
        "settings": {
            "showProgress": True,
            "allowSkip": False,
            "randomizeQuestions": False,
            "estimatedTime": "2-3 minutes"
        }
    }
    
    # Create the template
    template = SurveyTemplate(
        name="Post-Activity Feedback",
        description="A universal feedback template suitable for any activity type. Collect essential feedback about satisfaction, instructor performance, and areas for improvement.",
        questions=json.dumps(questions),
        created_by=1,  # System/Admin user
        created_dt=datetime.now(timezone.utc),
        status="active"
    )
    
    try:
        db.session.add(template)
        db.session.commit()
        print("✅ Successfully created default template: 'Post-Activity Feedback'")
        print(f"   - 5 questions (3 required, 2 optional)")
        print(f"   - Estimated completion time: 2-3 minutes")
        print(f"   - Status: Active")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating default template: {e}")
        return False
    
    return True

def main():
    """Run the migration"""
    with app.app_context():
        print("\n🚀 Running migration: Add default survey template")
        print("-" * 50)
        
        success = create_default_template()
        
        if success:
            print("-" * 50)
            print("✅ Migration completed successfully!\n")
        else:
            print("-" * 50)
            print("⚠️ Migration completed with warnings.\n")

if __name__ == "__main__":
    main()