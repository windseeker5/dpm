#!/usr/bin/env python3
"""
Test script to verify hero image fixes work correctly for Activity 5
This tests our fix for the user's specific issue with smiley face not appearing
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, '/home/kdresdell/Documents/DEV/minipass_env/app')

def test_hero_image_function():
    """Test the get_activity_hero_image function directly"""
    from app import app
    from models import Activity
    from utils import get_activity_hero_image
    
    with app.app_context():
        # Get Activity 5 as the user specified
        activity = Activity.query.get(5)
        if not activity:
            print("❌ Activity 5 not found in database")
            return False
            
        print(f"✅ Found Activity 5: {activity.name}")
        
        # Test the hero image function for newPass template (user's test case)
        template_type = 'newPass'
        print(f"\n🔍 Testing get_activity_hero_image for Activity {activity.id}, template '{template_type}'")
        
        # This should show our debug messages
        hero_data, is_custom_hero, is_template_default = get_activity_hero_image(activity, template_type)
        
        print(f"📋 Results:")
        print(f"   hero_data: {'Present' if hero_data else 'None'} ({len(hero_data) if hero_data else 0} bytes)")
        print(f"   is_custom_hero: {is_custom_hero}")
        print(f"   is_template_default: {is_template_default}")
        
        # Check if custom hero file exists at expected path
        custom_hero_path = f"static/uploads/5_newPass_hero.png"
        file_exists = os.path.exists(custom_hero_path)
        print(f"   Custom hero file exists: {file_exists} ({custom_hero_path})")
        
        if hero_data and is_custom_hero:
            print("✅ SUCCESS: Custom hero image found and loaded correctly!")
            return True
        elif file_exists and not is_custom_hero:
            print("❌ ISSUE: Custom hero file exists but wasn't detected as custom")
            return False
        elif not file_exists:
            print("❌ ISSUE: Custom hero file doesn't exist - user needs to upload smiley again")
            return False
        else:
            print("❌ ISSUE: Unknown problem with hero image detection")
            return False

def main():
    print("🧪 Testing Hero Image Fix for Activity 5")
    print("=" * 60)
    
    success = test_hero_image_function()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED: Hero image fix is working correctly!")
        print("   The preview and test email should now show the custom smiley face.")
    else:
        print("❌ TEST FAILED: Hero image fix needs more work.")
        print("   Check the debug messages above for clues.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())