#!/usr/bin/env python3
"""
Test the API endpoint to verify it returns the correct folder name
"""

import requests
import json

def test_api_endpoint():
    """Test the email payment bot API endpoint"""
    
    print("="*60)
    print("API ENDPOINT VERIFICATION")
    print("="*60)
    
    url = "http://127.0.0.1:8890/api/settings/payment-bot"
    
    try:
        # Need to be logged in to access this endpoint
        session = requests.Session()
        
        # First login
        login_data = {
            'email': 'kdresdell@gmail.com',
            'password': 'admin123'
        }
        login_response = session.post('http://127.0.0.1:8890/login', data=login_data)
        
        if login_response.status_code == 200:
            print("\n✓ Logged in successfully")
        
        # Now access the API
        response = session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                folder_name = data['data'].get('gmail_label_folder_processed')
                print(f"\n✓ API Response - Folder name: '{folder_name}'")
                
                if folder_name == "PaymentProcessed":
                    print("✅ SUCCESS: API returns correct folder 'PaymentProcessed'")
                    return True
                else:
                    print(f"❌ ERROR: API returns wrong folder '{folder_name}'")
                    return False
            else:
                print(f"❌ API returned error: {data.get('error')}")
                return False
        else:
            print(f"❌ API request failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False
    
    finally:
        print("\n" + "="*60)

if __name__ == "__main__":
    import sys
    success = test_api_endpoint()
    sys.exit(0 if success else 1)