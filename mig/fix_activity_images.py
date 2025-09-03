#!/usr/bin/env python3
"""
Fix activity images after migration.
Maps activities to available images in the uploads folder.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, Activity
import random

print("🖼️ Fixing activity images after migration...")

# Available images that were successfully migrated
available_images = [
    'activity_images/activity_28486c0e82.jpg',  # Sports/outdoor activity
    'activity_images/activity_2b08008625.jpg',  # Another sports image
    'activity_images/activity_f169559bdf.jpg',  # General activity
    'activity_images/unsplash_135d2dbd.jpg',    # Nice stock photo
    'activity_images/unsplash_76ea720b.jpg',    # Another stock photo
    'activity_images/unsplash_bc335948.jpg',    # Stock photo
]

with app.app_context():
    activities = Activity.query.all()
    fixed = 0
    
    for i, activity in enumerate(activities):
        print(f"  Checking: {activity.name}")
        print(f"    Current image: {activity.image_filename}")
        
        # Check if current image exists
        if activity.image_filename:
            full_path = f"/home/kdresdell/Documents/DEV/minipass_env/app/static/uploads/{activity.image_filename}"
            if not os.path.exists(full_path):
                # Try with activity_images prefix
                full_path = f"/home/kdresdell/Documents/DEV/minipass_env/app/static/uploads/activity_images/{activity.image_filename}"
                if not os.path.exists(full_path):
                    # Assign a new image based on activity type
                    if 'hockey' in activity.name.lower():
                        new_image = 'activity_images/activity_28486c0e82.jpg'
                    elif 'golf' in activity.name.lower():
                        new_image = 'activity_images/activity_f169559bdf.jpg'
                    elif 'kite' in activity.name.lower() or 'surf' in activity.name.lower():
                        new_image = 'activity_images/activity_2b08008625.jpg'
                    else:
                        # Assign a random nice image
                        new_image = available_images[i % len(available_images)]
                    
                    print(f"    ✓ Fixing with: {new_image}")
                    activity.image_filename = new_image
                    fixed += 1
                else:
                    # Add the activity_images prefix if missing
                    if not activity.image_filename.startswith('activity_images/'):
                        activity.image_filename = f'activity_images/{activity.image_filename}'
                        print(f"    ✓ Added prefix: {activity.image_filename}")
                        fixed += 1
    
    if fixed > 0:
        db.session.commit()
        print(f"\n✅ Done! Fixed {fixed} activity images")
    else:
        print("\n✅ All activity images are already correct")