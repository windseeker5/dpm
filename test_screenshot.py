#!/usr/bin/env python3
"""
Test script to take screenshots of the Unsplash error handling in action.
This uses requests to get session cookies and then opens the browser.
"""

import requests
import time
import subprocess
from bs4 import BeautifulSoup

def get_authenticated_session():
    """Get an authenticated session with proper cookies"""
    session = requests.Session()
    
    # Get login page for CSRF token
    login_page = session.get("http://127.0.0.1:8890/login")
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    
    if not csrf_input:
        print("❌ Could not find CSRF token")
        return None
    
    csrf_token = csrf_input.get('value')
    
    # Login
    login_data = {
        'email': 'kdresdell@gmail.com',
        'password': 'admin123', 
        'csrf_token': csrf_token
    }
    
    login_response = session.post("http://127.0.0.1:8890/login", data=login_data)
    
    if login_response.status_code == 200 and 'dashboard' in login_response.url:
        print("✅ Successfully authenticated")
        return session
    else:
        print(f"❌ Authentication failed: {login_response.status_code}")
        return None

def create_browser_screenshot_script():
    """Create a simple HTML page that automatically navigates and takes screenshot"""
    script_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Screenshot Test</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .status { padding: 1rem; margin: 1rem; border-radius: 8px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .info { background: #d1ecf1; color: #0c5460; }
        iframe { width: 100%; height: 600px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <h1>🧪 Unsplash Error Handling Test</h1>
    
    <div class="status info">
        <strong>Test Instructions:</strong>
        <ol>
            <li>Navigate to: <a href="http://127.0.0.1:8890/edit-activity/1" target="_blank">http://127.0.0.1:8890/edit-activity/1</a></li>
            <li>Login with: kdresdell@gmail.com / admin123</li>
            <li>Toggle "Search images from the Web"</li>
            <li>Click the search button</li>
            <li>Observe the improved error message</li>
        </ol>
    </div>
    
    <div class="status success">
        <strong>Expected Results:</strong>
        <ul>
            <li>✅ User-friendly error message instead of generic "Error loading images"</li>
            <li>✅ Specific message about API key configuration</li>
            <li>✅ Alternative suggestions (upload your own image)</li>
            <li>✅ Proper error styling with icons</li>
        </ul>
    </div>

    <div class="status error">
        <strong>What to Look For:</strong>
        <ul>
            <li>❌ No generic "Error loading images" message</li>
            <li>❌ No console errors without user explanation</li>
            <li>❌ No broken UI or missing error handling</li>
        </ul>
    </div>
    
    <h2>Quick Test Interface:</h2>
    <p><a href="http://127.0.0.1:8890/static/test_error_ui.html" target="_blank">View Simulated Error UI</a></p>
    
    <script>
        // Auto-open the test page
        setTimeout(() => {
            window.open('http://127.0.0.1:8890/edit-activity/1', '_blank');
        }, 2000);
    </script>
</body>
</html>
    """
    
    with open('/home/kdresdell/Documents/DEV/minipass_env/app/static/screenshot_test.html', 'w') as f:
        f.write(script_content)
    
    print("📄 Created screenshot test page at: /static/screenshot_test.html")
    return "http://127.0.0.1:8890/static/screenshot_test.html"

def take_manual_screenshots():
    """Instructions for manual screenshot testing"""
    print("\n📸 Manual Screenshot Testing Instructions:")
    print("=" * 50)
    print()
    print("1. Open your browser and navigate to:")
    print("   http://127.0.0.1:8890/edit-activity/1")
    print()
    print("2. Login with credentials:")
    print("   Email: kdresdell@gmail.com")
    print("   Password: admin123")
    print()
    print("3. Find the 'Activity Cover Photo' section")
    print("4. Toggle ON 'Search images from the Web'")
    print("5. Enter any search term (e.g., 'golf')")
    print("6. Click the 'Search' button")
    print()
    print("7. Take a screenshot of the error message that appears")
    print()
    print("Expected Results:")
    print("✅ Should show user-friendly error message")
    print("✅ Should mention API key configuration")  
    print("✅ Should suggest using upload alternative")
    print("✅ Should NOT show generic 'Error loading images'")
    print()
    
    test_url = create_browser_screenshot_script()
    print(f"🔗 Test helper page: {test_url}")

if __name__ == "__main__":
    print("🧪 Unsplash Error Handling Screenshot Test")
    print("=" * 50)
    
    # Verify we can authenticate
    session = get_authenticated_session()
    
    if session:
        print("\n✅ Authentication successful - ready for manual testing")
        
        # Test the error UI page
        print("\n📝 Testing simulated error UI...")
        error_ui_response = session.get("http://127.0.0.1:8890/static/test_error_ui.html")
        if error_ui_response.status_code == 200:
            print("✅ Simulated error UI page accessible")
            print("🔗 View at: http://127.0.0.1:8890/static/test_error_ui.html")
        
        take_manual_screenshots()
    else:
        print("❌ Authentication failed - cannot proceed with testing")
        
    print("\n" + "=" * 50)
    print("📋 Summary: Ready for manual UI testing")
    print("🎯 Key URLs:")
    print("   • Real test: http://127.0.0.1:8890/edit-activity/1") 
    print("   • Simulated: http://127.0.0.1:8890/static/test_error_ui.html")
    print("   • Helper: http://127.0.0.1:8890/static/screenshot_test.html")