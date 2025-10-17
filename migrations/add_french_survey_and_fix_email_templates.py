#!/usr/bin/env python3
"""
Migration script for survey email template fixes and French survey template
Fixes:
1. Adds French 8-question survey template
2. Cleans up stale hero_image references in email templates
3. Ensures Jinja2 variables in survey_invitation templates

Safe to run multiple times (idempotent)
"""

import json
import sys
import os
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import SurveyTemplate, Activity
from sqlalchemy.orm.attributes import flag_modified

def add_french_survey_template():
    """Add the French 8-question survey template"""
    print("\n📋 Task 1: Adding French Survey Template")
    print("-" * 60)

    # Check if template already exists
    existing = SurveyTemplate.query.filter_by(name="Sondage d'Activité - Simple (questions)").first()
    if existing:
        print("✅ French survey template already exists (ID: {}). Skipping...".format(existing.id))
        return True

    # Define the French survey questions
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
                "options": [
                    "Trop cher",
                    "Un peu cher",
                    "Juste",
                    "Bon rapport qualité-prix",
                    "Excellent rapport qualité-prix"
                ]
            },
            {
                "id": 3,
                "question": "Recommanderiez-vous cette activité à un ami?",
                "type": "multiple_choice",
                "required": True,
                "options": [
                    "Certainement",
                    "Probablement",
                    "Peut-être",
                    "Probablement pas",
                    "Certainement pas"
                ]
            },
            {
                "id": 4,
                "question": "Comment évaluez-vous l'emplacement/les installations?",
                "type": "multiple_choice",
                "required": False,
                "options": [
                    "Excellent",
                    "Très bien",
                    "Bien",
                    "Moyen",
                    "Insuffisant"
                ]
            },
            {
                "id": 5,
                "question": "L'horaire de l'activité vous convenait-il?",
                "type": "multiple_choice",
                "required": False,
                "options": [
                    "Parfaitement",
                    "Bien",
                    "Acceptable",
                    "Peu pratique",
                    "Très peu pratique"
                ]
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
                "options": [
                    "Oui, certainement",
                    "Oui, probablement",
                    "Peut-être",
                    "Probablement pas",
                    "Non"
                ]
            }
        ]
    }

    # Create the template
    template = SurveyTemplate(
        name="Sondage d'Activité - Simple (questions)",
        description="Sondage simple en français pour recueillir les retours après une activité ponctuelle (tournoi de golf, événement sportif, etc.). Temps de réponse: ~2 minutes.",
        questions=json.dumps(questions),
        created_by=1,  # System/Admin user
        created_dt=datetime.now(timezone.utc),
        status="active"
    )

    try:
        db.session.add(template)
        db.session.commit()
        print("✅ Successfully created French survey template")
        print(f"   - 8 questions (4 required, 4 optional)")
        print(f"   - 2 open-ended, 5 multiple choice, 1 rating scale")
        print(f"   - Status: Active")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating French survey template: {e}")
        return False


def cleanup_stale_hero_images():
    """Remove hero_image references that don't exist on disk"""
    print("\n🖼️  Task 2: Cleaning up stale hero_image references")
    print("-" * 60)

    activities = Activity.query.all()
    cleaned_count = 0

    for activity in activities:
        if not activity.email_templates:
            continue

        templates = activity.email_templates
        if 'survey_invitation' not in templates:
            continue

        survey_template = templates['survey_invitation']
        if 'hero_image' not in survey_template:
            continue

        hero_filename = survey_template['hero_image']
        hero_path = os.path.join('static', 'uploads', hero_filename)

        # Check if file exists
        if not os.path.exists(hero_path):
            print(f"   Activity {activity.id} ({activity.name}): Removing stale hero_image '{hero_filename}'")
            del survey_template['hero_image']

            # Mark modified for SQLAlchemy (JSON column needs explicit flag)
            activity.email_templates = templates
            flag_modified(activity, 'email_templates')
            cleaned_count += 1

    if cleaned_count > 0:
        try:
            db.session.commit()
            print(f"✅ Cleaned {cleaned_count} stale hero_image reference(s)")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error saving changes: {e}")
            return False
    else:
        print("✅ No stale hero_image references found")
        return True


def ensure_jinja2_variables():
    """Ensure survey_invitation templates use Jinja2 variables"""
    print("\n🔧 Task 3: Ensuring Jinja2 variables in email templates")
    print("-" * 60)

    # Default intro_text with Jinja2 variables (French)
    default_intro_text = '<p>Bonjour,</p><p>Nous aimerions connaître votre expérience récente avec nous pour l\'activité <strong>{{ activity_name }}</strong>!</p><p>Cela ne prendra que quelques minutes - seulement <strong>{{ question_count }}</strong> questions rapides.</p>'

    activities = Activity.query.all()
    updated_count = 0

    for activity in activities:
        if not activity.email_templates:
            continue

        templates = activity.email_templates
        if 'survey_invitation' not in templates:
            continue

        survey_template = templates['survey_invitation']
        intro_text = survey_template.get('intro_text', '')

        # Check if intro_text has Jinja2 variables
        if intro_text and '{{' in intro_text and '}}' in intro_text:
            # Already has variables, skip
            continue

        # Check if intro_text has hardcoded values (needs fixing)
        if intro_text and (activity.name in intro_text or any(str(i) in intro_text for i in range(1, 20))):
            print(f"   Activity {activity.id} ({activity.name}): Updating intro_text with Jinja2 variables")
            survey_template['intro_text'] = default_intro_text
            activity.email_templates = templates
            flag_modified(activity, 'email_templates')
            updated_count += 1
        elif not intro_text:
            # Empty intro_text, set default
            print(f"   Activity {activity.id} ({activity.name}): Setting default intro_text")
            survey_template['intro_text'] = default_intro_text
            activity.email_templates = templates
            flag_modified(activity, 'email_templates')
            updated_count += 1

    if updated_count > 0:
        try:
            db.session.commit()
            print(f"✅ Updated {updated_count} email template(s) with Jinja2 variables")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error saving changes: {e}")
            return False
    else:
        print("✅ All email templates already use Jinja2 variables")
        return True


def main():
    """Run all migration tasks"""
    print("\n" + "="*60)
    print("🚀 MIGRATION: Survey Email Template Fixes + French Survey")
    print("="*60)

    with app.app_context():
        results = []

        # Task 1: Add French survey
        results.append(add_french_survey_template())

        # Task 2: Clean up stale hero images
        results.append(cleanup_stale_hero_images())

        # Task 3: Ensure Jinja2 variables
        results.append(ensure_jinja2_variables())

        # Summary
        print("\n" + "="*60)
        if all(results):
            print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        else:
            print("⚠️  MIGRATION COMPLETED WITH SOME WARNINGS")
        print("="*60 + "\n")


if __name__ == "__main__":
    main()
