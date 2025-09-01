#!/usr/bin/env python3
"""
Test script to validate the KPI API endpoint fix
"""
import requests
import json
import sys

def test_kpi_api():
    # Test different period values
    base_url = "http://localhost:5000"
    activity_id = 1  # Use the first activity we found
    
    # First, try to get login page to check if server is running
    try:
        response = requests.get(f"{base_url}/login", timeout=5)
        print(f"✅ Server is running (status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server is not accessible: {e}")
        return False
    
    # Test different period values
    periods_to_test = [7, 30, 90, 365]
    
    for period in periods_to_test:
        url = f"{base_url}/api/activity-kpis/{activity_id}?period={period}"
        try:
            response = requests.get(url, timeout=10)
            print(f"\n📊 Testing period={period}")
            print(f"   URL: {url}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ Success: Got KPI data")
                    print(f"   📈 Data keys: {list(data.get('kpi_data', {}).keys())}")
                else:
                    print(f"   ⚠️  Response success=False: {data.get('error', 'Unknown error')}")
            elif response.status_code == 401:
                print(f"   🔒 Authentication required (expected without login)")
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    print(f"   ❌ Bad Request: {error_data.get('error', 'Unknown error')}")
                    print(f"   🔍 Error code: {error_data.get('code', 'No code')}")
                except:
                    print(f"   ❌ Bad Request: {response.text}")
            else:
                print(f"   ❓ Unexpected status: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing KPI API Endpoint")
    print("=" * 50)
    test_kpi_api()