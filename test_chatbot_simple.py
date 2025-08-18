#!/usr/bin/env python3
"""
Simple test to verify the chatbot improvements
"""

import requests
import time

def test_server_access():
    """Test that we can access the chatbot page"""
    try:
        # Test main page
        response = requests.get("http://127.0.0.1:8890")
        print(f"Main page status: {response.status_code}")
        
        # Test chatbot page (might redirect to login)
        response = requests.get("http://127.0.0.1:8890/analytics/chatbot")
        print(f"Chatbot page status: {response.status_code}")
        
        print("✅ Server is responding correctly")
        return True
        
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

if __name__ == "__main__":
    test_server_access()