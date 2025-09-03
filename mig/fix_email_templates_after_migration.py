#!/usr/bin/env python3
"""
Fix email templates for activities after migration.
Run this after importing data from backup.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        # Fix if templates are empty or missing
        if not activity.email_templates or activity.email_templates == {}:
            print(f"  ✓ Fixing: {activity.name}")
            activity.email_templates = defaults
            fixed += 1
    
    # Save changes
    if fixed > 0:
        db.session.commit()
        print(f"\n✅ Done! Fixed {fixed} activities")
    else:
        print("\n✅ All activities already have templates")