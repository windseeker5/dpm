#!/usr/bin/env python3
"""
Simple test for live preview endpoint - just to verify it works
"""
import sys
import os
import requests
import json

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_live_preview_endpoint():
    """Test the live preview endpoint manually"""
    print("🔍 Testing live preview endpoint...")
    
    try:
        # Test with minimal data - we expect CSRF error for now
        response = requests.post(
            'http://localhost:5000/activity/1/email-preview-live',
            data={
                'template_type': 'newPass',
                'newPass_subject': 'Live Test Subject',
                'newPass_title': 'Live Test Title'
            }
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Content (first 200 chars): {response.text[:200]}")
        
        if response.status_code == 400 and 'CSRF' in response.text:
            print("✅ Endpoint exists and is properly protected by CSRF")
            return True
        elif response.status_code == 302:
            print("✅ Endpoint redirects (probably to login - expected for unauthenticated request)")
            return True
        elif response.status_code == 200:
            print("✅ Endpoint responded successfully")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False

def test_route_registration():
    """Test that the route is properly registered"""
    from app import app
    
    print("\n🔍 Testing route registration...")
    
    # Get all routes
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': str(rule.rule)
        })
    
    # Look for our route
    live_preview_route = None
    for route in routes:
        if 'email-preview-live' in route['rule']:
            live_preview_route = route
            break
    
    if live_preview_route:
        print(f"✅ Route found: {live_preview_route}")
        return True
    else:
        print("❌ Live preview route not found in registered routes")
        # Show some similar routes for debugging
        preview_routes = [r for r in routes if 'preview' in r['rule']]
        print(f"Similar routes found: {preview_routes}")
        return False

if __name__ == '__main__':
    print("🧪 Simple Live Preview Tests")
    print("=" * 50)
    
    success1 = test_route_registration()
    success2 = test_live_preview_endpoint()
    
    if success1 and success2:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)