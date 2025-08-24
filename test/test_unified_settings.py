#!/usr/bin/env python3
"""
Test script for unified settings route
"""
import sys
import os

# Add the parent directory to sys.path to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Setting

def test_unified_settings_route():
    """Test that unified settings route exists and handles GET requests"""
    with app.test_client() as client:
        # Create a test session
        with client.session_transaction() as sess:
            sess['admin'] = 'test@example.com'
        
        # Test GET request
        response = client.get('/admin/unified-settings')
        print(f"GET /admin/unified-settings status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Unified settings route is working!")
            print("Response content type:", response.content_type)
            # Check if it's rendering the template
            if b'Unified Settings' in response.data:
                print("✅ Template appears to be rendering correctly")
            else:
                print("⚠️ Template may not be rendering as expected")
        else:
            print(f"❌ Route returned status {response.status_code}")
            print("Response data:", response.data.decode('utf-8')[:500])

        # Test alternative route name
        response = client.get('/admin/settings')
        print(f"GET /admin/settings status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Alternative settings route is working!")

if __name__ == '__main__':
    with app.app_context():
        test_unified_settings_route()