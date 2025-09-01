#!/usr/bin/env python3
"""
Simple test to debug the KPI data structure issue
"""
import requests
import json

def test_kpi_endpoint():
    """Test the KPI endpoint directly"""
    try:
        # Try to access the dashboard to see if we get any data
        response = requests.get('http://localhost:5000/')
        
        # Look for JavaScript data in the response
        if 'kpiData' in response.text:
            print("✅ Found kpiData in response")
            
            # Extract the kpiData from the script tag
            lines = response.text.split('\n')
            for line in lines:
                if 'var kpiData =' in line or 'const kpiData =' in line:
                    print("📊 KPI Data Line Found:")
                    print(line.strip())
                    break
        else:
            print("❌ No kpiData found in response")
            
        # Try to access an activity dashboard directly
        activity_response = requests.get('http://localhost:5000/activities')
        print(f"Activity page status: {activity_response.status_code}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_kpi_endpoint()