#!/usr/bin/env python3
"""
Test Email with Hero Image - Verify hero images are working
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from utils import send_email_async
from datetime import datetime
from models import Activity

def test_hero_image_email():
    """Test email with hero image from activity 2"""
    try:
        with app.app_context():
            print("🖼️ Testing Email with Hero Image")
            print("=" * 50)
            
            # Get activity 2 that has the hero image
            activity = Activity.query.get(2)
            print(f"Activity: {activity.name}")
            
            # Check if hero image exists
            if activity.email_templates and 'newPass' in activity.email_templates:
                template_data = activity.email_templates['newPass']
                if 'hero_image' in template_data:
                    hero_image = template_data['hero_image']
                    hero_path = os.path.join('static', 'uploads', 'email_heroes', hero_image)
                    print(f"Hero image: {hero_image}")
                    print(f"Hero path exists: {os.path.exists(hero_path)}")
                    
                    # Try to read the file size
                    if os.path.exists(hero_path):
                        file_size = os.path.getsize(hero_path) / 1024  # KB
                        print(f"Hero image size: {file_size:.2f} KB")
            
            # Send email using the newPass template with hero image
            context = {
                'user_name': 'Hero Image Test',
                'user_email': 'kdresdell@gmail.com',
                'activity_name': activity.name,
                'pass_code': 'HERO123',
                'title': 'Hero Image Test Email',
                'intro_text': 'This email should include the hero image you uploaded.',
                'conclusion_text': 'Check if the hero image appears above!'
            }
            
            # Send using newPass template which should have the hero
            send_email_async(
                app=app,
                activity=activity,  # This should apply customizations including hero
                subject=f"🖼️ Hero Image Test - {datetime.now().strftime('%H:%M:%S')}",
                to_email="kdresdell@gmail.com",
                template_name="newPass",
                context=context
            )
            
            print("\n✅ Test email sent to kdresdell@gmail.com")
            print("📧 Check if the hero image appears in the email!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_hero_image_email()