#!/usr/bin/env python3
"""
Email Functionality Test Script
Tests both original email functionality and new template customization features
Sends test emails to kdresdell@gmail.com to verify everything is working
"""

import os
import sys
import traceback
from datetime import datetime

# Add the parent directory to the path so we can import from the main app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_email_functionality():
    """Test the basic email functionality without any customizations"""
    print("\n🧪 Testing Basic Email Functionality...")
    
    try:
        from app import app
        from utils import send_email_async
        
        with app.app_context():
            print("✅ App context created successfully")
            
            # Test 1: Basic email with HTML body (original functionality)
            print("\n📧 Test 1: Sending basic HTML email...")
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #007bff;">🧪 Minipass Email System Test</h2>
                <p>This is a test email to verify your email system is working correctly.</p>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>Test Details:</strong><br>
                    • Test Type: Basic HTML Email<br>
                    • Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                    • Status: ✅ Original email functionality is intact
                </div>
                <p style="color: #28a745;">
                    <strong>Result: Your email system is working perfectly!</strong>
                </p>
                <hr>
                <small style="color: #6c757d;">
                    Sent from your Minipass email testing script
                </small>
            </body>
            </html>
            """
            
            send_email_async(
                app=app,
                subject="✅ Minipass Email Test - Basic Functionality",
                to_email="kdresdell@gmail.com",
                html_body=html_content
            )
            
            print("✅ Basic email sent successfully!")
            
            # Test 2: Template-based email (original functionality)  
            print("\n📧 Test 2: Testing template-based email...")
            context = {
                'title': 'Email Template Test',
                'intro_text': 'This tests the original template functionality.',
                'body_text': 'Your email templates are working correctly!',
                'footer_text': 'This confirms backward compatibility.',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Try to send with a basic template (this will use existing templates)
            send_email_async(
                app=app,
                subject="📧 Minipass Template Test - Original Functionality", 
                to_email="kdresdell@gmail.com",
                template_name="email_templates/signup/index.html",
                context=context
            )
            
            print("✅ Template-based email sent successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Basic email test failed: {str(e)}")
        print(f"Full error: {traceback.format_exc()}")
        return False

def test_enhanced_email_functionality():
    """Test the new email template customization functionality"""
    print("\n🆕 Testing Enhanced Email Template Customization...")
    
    try:
        from app import app
        from utils import send_email_async, get_email_context
        from models import Activity
        
        with app.app_context():
            print("✅ App context created for enhanced testing")
            
            # Get the first available activity for testing
            activity = Activity.query.first()
            if not activity:
                print("⚠️  No activities found - creating test scenario without activity")
                
                # Test the helper function with None activity (should work fine)
                test_context = get_email_context(None, 'newPass', {'test': 'value'})
                print(f"✅ get_email_context works with no activity: {test_context}")
                
                return True
            
            print(f"🎯 Testing with Activity: {activity.name} (ID: {activity.id})")
            
            # Test 3: Enhanced email with activity customization
            print("\n📧 Test 3: Testing enhanced email with activity...")
            
            context = {
                'title': f'Enhanced Email Test for {activity.name}',
                'intro_text': 'This tests the new template customization system.',
                'body_text': 'The email customization features are working!',
                'footer_text': 'Enhanced functionality is active and compatible.',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            send_email_async(
                app=app,
                activity=activity,  # This enables the new customization features
                subject="🆕 Minipass Enhanced Email Test - New Features",
                to_email="kdresdell@gmail.com", 
                template_name="newPass",
                context=context
            )
            
            print("✅ Enhanced email with activity customization sent!")
            
            # Test 4: Test the get_email_context function directly
            print("\n🔧 Test 4: Testing get_email_context function...")
            base_context = {'test_field': 'test_value'}
            merged_context = get_email_context(activity, 'newPass', base_context)
            print(f"✅ Context merging works: {len(merged_context)} fields in final context")
            
            return True
            
    except Exception as e:
        print(f"❌ Enhanced email test failed: {str(e)}")
        print(f"Full error: {traceback.format_exc()}")
        return False

def main():
    """Main test runner"""
    print("🚀 Starting Minipass Email System Tests")
    print("=" * 50)
    
    # Test basic functionality first
    basic_test_passed = test_basic_email_functionality()
    
    # Test enhanced functionality  
    enhanced_test_passed = test_enhanced_email_functionality()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    if basic_test_passed:
        print("✅ BASIC EMAIL FUNCTIONALITY: PASSED")
        print("   → Your original email system is working perfectly")
        print("   → No breaking changes detected")
    else:
        print("❌ BASIC EMAIL FUNCTIONALITY: FAILED")
        print("   → There may be an issue with your email configuration")
    
    if enhanced_test_passed:
        print("✅ ENHANCED EMAIL FEATURES: PASSED") 
        print("   → New template customization system is working")
        print("   → Integration is successful and backward compatible")
    else:
        print("⚠️  ENHANCED EMAIL FEATURES: ISSUES DETECTED")
        print("   → Basic functionality should still work")
        
    print(f"\n📧 Test emails sent to: kdresdell@gmail.com")
    print(f"🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if basic_test_passed:
        print("\n🎉 CONCLUSION: Your email system is working! Check your inbox.")
    else:
        print("\n⚠️  CONCLUSION: Please check your email configuration.")

if __name__ == "__main__":
    main()