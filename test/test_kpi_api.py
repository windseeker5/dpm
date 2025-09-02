#!/usr/bin/env python3
"""
Test script to verify KPI API is working correctly for activity dashboard
"""
import requests
import json

def test_kpi_api():
    """Test KPI API endpoints"""
    
    print("🚀 Testing KPI API for Activity Dashboard...")
    
    # Login first
    session = requests.Session()
    login_url = "http://localhost:5000/login"
    login_data = {
        "email": "kdresdell@gmail.com",
        "password": "admin123"
    }
    
    response = session.post(login_url, data=login_data)
    print(f"✓ Login status: {response.status_code}")
    
    # Test KPI API for activity 1 with different periods
    activity_id = 1
    periods = ['7d', '30d', '90d', 'all']
    
    for period in periods:
        api_url = f"http://localhost:5000/api/kpi-data?period={period}&activity_id={activity_id}"
        response = session.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Period: {period}")
            print(f"  Success: {data.get('success', False)}")
            
            if data.get('success'):
                kpi_data = data.get('kpi_data', {})
                
                # Check each KPI
                for kpi_type in ['revenue', 'active_users', 'passports_created', 'unpaid_passports']:
                    if kpi_type in kpi_data:
                        kpi = kpi_data[kpi_type]
                        current = kpi.get('current', 0)
                        trend_data = kpi.get('trend_data', [])
                        print(f"  {kpi_type}:")
                        print(f"    Current: {current}")
                        print(f"    Trend data points: {len(trend_data)}")
                        print(f"    Has data: {len(trend_data) > 0}")
            else:
                print(f"  Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"  ❌ Failed with status {response.status_code}")
    
    print("\n✅ API test completed!")

if __name__ == "__main__":
    test_kpi_api()