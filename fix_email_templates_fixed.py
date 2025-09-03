#!/usr/bin/env python3
"""
Fix email templates for activities after migration.
Run this after importing data from backup.
"""

import json
from app import app, db, Activity
from utils_email_defaults import get_default_email_templates

print("🔧 Fixing email templates for migrated activities...")

with app.app_context():
    # Get default French templates
    defaults = get_default_email_templates()
    
    # Get all activities
    activities = Activity.query.all()
    fixed = 0
    
    for activity in activities:
        needs_fix = False
        
        # Check if templates need fixing
        # Handle both None and empty string cases
        if not activity.email_templates or activity.email_templates == '':
            needs_fix = True
        else:
            try:
                # Try to parse as JSON - if it fails or is empty dict, needs fix
                parsed = json.loads(activity.email_templates)
                if not parsed or parsed == {}:
                    needs_fix = True
            except (json.JSONDecodeError, TypeError):
                needs_fix = True
        
        if needs_fix:
            print(f"  ✓ Fixing: {activity.name}")
            # Convert dict to JSON string for TEXT field
            activity.email_templates = json.dumps(defaults)
            fixed += 1
    
    # Save changes
    if fixed > 0:
        try:
            db.session.commit()
            print(f"\n✅ Done! Fixed {fixed} activities")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error committing changes: {e}")
    else:
        print("\n✅ All activities already have templates")