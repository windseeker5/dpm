#!/usr/bin/env python3
"""
Test script for organization-specific email configuration
Run this to test the new email system with organization settings
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8890"

def test_organization_email_system():
    """Test the organization email system"""
    
    print("🧪 Testing Organization Email System")
    print("=" * 50)
    
    # Start a session to handle login
    session = requests.Session()
    
    # Step 1: Login as admin
    print("1. Logging in as admin...")
    login_data = {
        'email': 'kdresdell@gmail.com',
        'password': 'admin123'
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200:
        print("   ✅ Login successful")
    else:
        print("   ❌ Login failed")
        return False
    
    # Step 2: Create test LHGI organization
    print("2. Creating LHGI test organization...")
    try:
        response = session.post(f"{BASE_URL}/admin/create-test-org")
        result = response.json()
        
        if result.get('success'):
            print(f"   ✅ {result.get('message')}")
            org_id = result.get('organization_id')
        else:
            print(f"   ⚠️  {result.get('error', 'Unknown error')}")
            # Try to get existing organizations
            response = session.get(f"{BASE_URL}/admin/organizations")
            if response.status_code == 200:
                orgs = response.json().get('organizations', [])
                lhgi_org = next((org for org in orgs if org['domain'] == 'lhgi'), None)
                if lhgi_org:
                    org_id = lhgi_org['id']
                    print(f"   ℹ️  Using existing LHGI organization (ID: {org_id})")
                else:
                    print("   ❌ Could not find or create LHGI organization")
                    return False
            else:
                print("   ❌ Failed to check existing organizations")
                return False
                
    except Exception as e:
        print(f"   ❌ Error creating organization: {e}")
        return False
    
    # Step 3: List organizations
    print("3. Listing configured organizations...")
    try:
        response = session.get(f"{BASE_URL}/admin/organizations")
        if response.status_code == 200:
            organizations = response.json().get('organizations', [])
            print(f"   ✅ Found {len(organizations)} organizations:")
            for org in organizations:
                print(f"      - {org['name']} ({org['domain']}@minipass.me) - {'Enabled' if org['email_enabled'] else 'Disabled'}")
        else:
            print(f"   ❌ Failed to list organizations: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error listing organizations: {e}")
    
    # Step 4: Test email configuration
    print("4. Testing LHGI email configuration...")
    try:
        response = session.post(f"{BASE_URL}/admin/organizations/{org_id}/test")
        result = response.json()
        
        if result.get('success'):
            print(f"   ✅ {result.get('message')}")
        else:
            print(f"   ❌ {result.get('message')}")
            
    except Exception as e:
        print(f"   ❌ Error testing email: {e}")
    
    # Step 5: Test the organization management UI
    print("5. Testing organization management UI...")
    try:
        response = session.get(f"{BASE_URL}/setup")
        if response.status_code == 200 and 'Organization Email Settings' in response.text:
            print("   ✅ Organization management UI is available in settings")
        else:
            print("   ❌ Organization management UI not found")
    except Exception as e:
        print(f"   ❌ Error checking UI: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Organization Email System Test Complete!")
    print("\nNext steps:")
    print("1. Visit http://127.0.0.1:8890/setup and go to 'Organization' tab")
    print("2. You should see the LHGI organization listed")
    print("3. Test email functionality by creating a test activity and user")
    print("4. Send test emails to verify organization-specific email settings")
    
    return True

if __name__ == "__main__":
    test_organization_email_system()