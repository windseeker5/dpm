#!/usr/bin/env python3
"""Direct test bypassing auth to see template errors"""

# Direct Flask app testing
import sys
sys.path.insert(0, '/home/kdresdell/Documents/DEV/minipass_env/app')

try:
    from app import app
    from models import Activity, Passport, Signup
    
    with app.test_client() as client:
        # Force login bypass for testing
        with client.session_transaction() as sess:
            sess['admin'] = 'kdresdell@gmail.com'
            sess['email'] = 'kdresdell@gmail.com'
            sess['username'] = 'Ken Dresdell'
        
        # Now access the page
        response = client.get('/activity-dashboard/1')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            html = response.data.decode('utf-8')
            
            # Check for filter buttons
            if 'github-filter-btn' in html:
                print("✓ Filter buttons found!")
                # Count them
                count = html.count('github-filter-btn')
                print(f"  Found {count} filter buttons")
            else:
                print("✗ No filter buttons found")
                
            # Check for functions
            if 'function filterPassports' in html:
                print("✓ filterPassports function found")
            else:
                print("✗ filterPassports function NOT found")
                
            # Check for errors
            if 'UndefinedError' in html or 'TemplateError' in html:
                print("✗ Template error detected!")
                # Find the error
                import re
                error = re.search(r'(UndefinedError|TemplateError)[^<]*', html)
                if error:
                    print(f"  Error: {error.group(0)[:200]}")
        else:
            print(f"Failed with status: {response.status_code}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()