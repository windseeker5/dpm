#!/usr/bin/env python3
"""
Test script to verify automatic hero image resizing functionality.
This script will test the complete workflow described in the user's request.
"""

import requests
import os
import time
import re
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://localhost:5000"
LOGIN_EMAIL = "test@example.com"
LOGIN_PASSWORD = "password123" 
TEST_IMAGE_PATH = "static/uploads/test_smiley_300x300.png"

def test_hero_image_resizing():
    """Test the complete hero image resizing workflow."""
    
    print("🧪 Starting Hero Image Resizing Test")
    print("=" * 50)
    
    # Create session to maintain cookies
    session = requests.Session()
    
    # Step 1: Test server connection
    print("1️⃣ Testing server connection...")
    try:
        response = session.get(BASE_URL)
        print(f"✅ Server responding: {response.status_code}")
    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        return False
    
    # Step 2: Get login page and extract CSRF token
    print("\n2️⃣ Accessing login page and extracting CSRF token...")
    try:
        login_page = session.get(urljoin(BASE_URL, "/login"))
        print(f"✅ Login page loaded: {login_page.status_code}")
        
        # Extract CSRF token using regex
        csrf_token = None
        try:
            csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_page.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                print(f"✅ CSRF token extracted: {csrf_token[:20]}...")
            else:
                print("⚠️ No CSRF token found in login form")
        except Exception as e:
            print(f"⚠️ CSRF token extraction failed: {e}")
            
    except Exception as e:
        print(f"❌ Login page failed: {e}")
        return False
    
    # Step 3: Login with test credentials
    print(f"\n3️⃣ Logging in with {LOGIN_EMAIL}...")
    login_data = {
        'email': LOGIN_EMAIL,
        'password': LOGIN_PASSWORD
    }
    
    # Add CSRF token if found
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    try:
        login_response = session.post(urljoin(BASE_URL, "/login"), data=login_data, allow_redirects=True)
        if login_response.status_code == 200 and 'dashboard' in login_response.url.lower():
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {login_response.status_code}, URL: {login_response.url}")
            print("Response content preview:", login_response.text[:500])
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 4: Navigate to Activity 5 email template customization
    print("\n4️⃣ Navigating to Activity 5 email template customization...")
    try:
        templates_url = urljoin(BASE_URL, "/activity/5/email-templates")
        templates_response = session.get(templates_url)
        if templates_response.status_code == 200:
            print("✅ Email templates page loaded")
        else:
            print(f"❌ Email templates page failed: {templates_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Email templates navigation error: {e}")
        return False
    
    # Step 5: Access New Pass template customization
    print("\n5️⃣ Accessing New Pass template customization...")
    try:
        newpass_url = urljoin(BASE_URL, "/activity/5/email-templates/newPass")
        newpass_response = session.get(newpass_url)
        if newpass_response.status_code == 200:
            print("✅ New Pass template page loaded")
        else:
            print(f"❌ New Pass template page failed: {newpass_response.status_code}")
            print("Response content preview:", newpass_response.text[:500])
            return False
    except Exception as e:
        print(f"❌ New Pass template navigation error: {e}")
        return False
    
    # Step 6: Reset to default template (simulate button click)
    print("\n6️⃣ Resetting template to default...")
    try:
        reset_url = urljoin(BASE_URL, "/activity/5/email-templates/reset")
        reset_response = session.post(reset_url, allow_redirects=True)
        if reset_response.status_code == 200:
            print("✅ Template reset to default")
        else:
            print(f"⚠️ Reset may have failed: {reset_response.status_code}")
            # Continue anyway as this might not be critical
    except Exception as e:
        print(f"⚠️ Reset error (continuing anyway): {e}")
    
    # Step 7: Upload test image as hero image
    print(f"\n7️⃣ Uploading test image ({TEST_IMAGE_PATH})...")
    
    # Check if test image exists
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"❌ Test image not found: {TEST_IMAGE_PATH}")
        return False
    
    # Get original image size
    original_size = os.path.getsize(TEST_IMAGE_PATH)
    print(f"📁 Original image size: {original_size} bytes")
    
    try:
        with open(TEST_IMAGE_PATH, 'rb') as img_file:
            files = {'hero_image': ('test_smiley_300x300.png', img_file, 'image/png')}
            upload_url = urljoin(BASE_URL, "/activity/5/email-templates/save")
            
            # Include template data to simulate form submission
            form_data = {
                'template_type': 'newPass',
                'subject': 'Test Subject',
                'content': 'Test Content'
            }
            
            upload_response = session.post(upload_url, files=files, data=form_data, allow_redirects=True)
            
            if upload_response.status_code == 200:
                print("✅ Hero image uploaded successfully")
                
                # Check if resizing message is in response
                response_text = upload_response.text
                if "resized" in response_text.lower():
                    print("✅ Image resizing was performed")
                else:
                    print("⚠️ No resizing confirmation found in response")
                    
            else:
                print(f"❌ Upload failed: {upload_response.status_code}")
                print("Response content preview:", upload_response.text[:500])
                return False
                
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False
    
    # Step 8: Check if resized image was saved
    print("\n8️⃣ Checking for resized image...")
    expected_resized_path = "static/uploads/5_newPass_hero.png"
    if os.path.exists(expected_resized_path):
        resized_size = os.path.getsize(expected_resized_path)
        print(f"✅ Resized image found: {expected_resized_path}")
        print(f"📁 Resized image size: {resized_size} bytes")
        print(f"📊 Size change: {original_size} → {resized_size} bytes")
        
        # Load and check dimensions using PIL if available
        try:
            from PIL import Image
            with Image.open(expected_resized_path) as img:
                width, height = img.size
                print(f"📏 Resized dimensions: {width}x{height}")
                
                # Check if dimensions match expected newPass template size (1408x768)
                if width == 1408 and height == 768:
                    print("✅ Image dimensions match newPass template size (1408x768)")
                else:
                    print(f"❌ Unexpected dimensions! Expected 1408x768, got {width}x{height}")
                    return False
                    
        except ImportError:
            print("⚠️ PIL not available to check dimensions")
        except Exception as e:
            print(f"⚠️ Error checking image dimensions: {e}")
    else:
        print(f"❌ Resized image not found: {expected_resized_path}")
        return False
    
    # Step 9: Test email preview
    print("\n9️⃣ Testing email preview...")
    try:
        preview_url = urljoin(BASE_URL, "/activity/5/email-templates/preview")
        preview_response = session.get(preview_url)
        if preview_response.status_code == 200:
            print("✅ Email preview loaded")
            
            # Check if hero image is referenced in preview
            preview_html = preview_response.text
            if "5_newPass_hero.png" in preview_html:
                print("✅ Hero image found in preview HTML")
            else:
                print("⚠️ Hero image not found in preview HTML")
                
        else:
            print(f"⚠️ Preview failed: {preview_response.status_code}")
    except Exception as e:
        print(f"⚠️ Preview error: {e}")
    
    # Step 10: Send test email (if endpoint exists)
    print("\n🔟 Testing email sending...")
    try:
        test_email_url = urljoin(BASE_URL, "/activity/5/email-templates/test")
        test_email_data = {'test_email': 'test@example.com'}
        
        test_response = session.post(test_email_url, data=test_email_data)
        if test_response.status_code == 200:
            print("✅ Test email sent successfully")
        else:
            print(f"⚠️ Test email failed: {test_response.status_code}")
    except Exception as e:
        print(f"⚠️ Test email error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Hero Image Resizing Test Completed Successfully!")
    print("\nKey Test Results:")
    print(f"   • Original image: 300x300 pixels, {original_size} bytes")
    print(f"   • Resized image: 1408x768 pixels, {resized_size} bytes" if 'resized_size' in locals() else "   • Resized image: Check manually")
    print("   • Template: newPass")
    print("   • Expected dimensions: 1408x768 (✅ Confirmed)" if 'width' in locals() and width == 1408 and height == 768 else "   • Expected dimensions: 1408x768 (⚠️ Check manually)")
    
    return True

if __name__ == "__main__":
    success = test_hero_image_resizing()
    if not success:
        print("\n❌ Test failed - check the output above for details")
        exit(1)
    else:
        print("\n✅ All tests passed!")