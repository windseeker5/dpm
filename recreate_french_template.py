#!/usr/bin/env python3
"""
Script to delete old French template and create new one with proper format
"""
import sys
sys.path.insert(0, '/home/kdresdell/Documents/DEV/minipass_env/app')

from app import app, db
from models import SurveyTemplate
import json

def recreate_french_template():
    """Delete old French templates and create new one"""
    with app.app_context():
        # Find and delete any existing French templates
        old_templates = SurveyTemplate.query.filter(
            SurveyTemplate.name.like("%Sondage d'Activité%")
        ).all()

        if old_templates:
            print(f"Found {len(old_templates)} existing French template(s)")
            for template in old_templates:
                print(f"  - Deleting: {template.name} (ID: {template.id})")
                db.session.delete(template)

            try:
                db.session.commit()
                print("✅ Old templates deleted successfully")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error deleting templates: {str(e)}")
                return False
        else:
            print("No existing French templates found")

        # Create new template
        print("\n🔨 Creating new French template with proper format...")
        from app import create_french_simple_survey_template

        new_template = create_french_simple_survey_template()

        if new_template:
            print(f"\n✅ Template created successfully!")
            print(f"   Name: {new_template.name}")
            print(f"   ID: {new_template.id}")
            print(f"   Description: {new_template.description}")

            # Verify the questions format
            questions_data = json.loads(new_template.questions)
            questions = questions_data.get('questions', [])
            print(f"\n📋 Template has {len(questions)} questions:")
            for q in questions:
                print(f"   {q['id']}. {q['question'][:60]}...")
                if q['type'] == 'multiple_choice':
                    print(f"      Type: {q['type']} ({len(q.get('options', []))} options)")
                    print(f"      Options: {q.get('options', [])[:3]}")
                else:
                    print(f"      Type: {q['type']}")

            return True
        else:
            print("❌ Failed to create template")
            return False

if __name__ == "__main__":
    success = recreate_french_template()
    sys.exit(0 if success else 1)
