#!/usr/bin/env python3
"""
Test script to verify KPI chart fixes work on both dashboard pages
"""
import time
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import sys

def test_kpi_pages():
    """Test both dashboard pages for successful loading and KPI elements"""
    
    # Setup session with retry strategy
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    base_url = "http://localhost:5000"
    
    try:
        print("🧪 Testing KPI implementations on both dashboards\n")
        
        # Test 1: Main dashboard
        print("1️⃣ Testing main dashboard...")
        response = session.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("   ✅ Main dashboard loads successfully")
            
            # Check for KPI chart elements
            chart_elements = ['revenue-chart', 'active-passports-chart', 'passports-created-chart', 'pending-signups-chart']
            missing_elements = []
            
            for element in chart_elements:
                if f'id="{element}"' not in response.text:
                    missing_elements.append(element)
            
            if not missing_elements:
                print("   ✅ All 4 KPI chart elements found in HTML")
            else:
                print(f"   ❌ Missing chart elements: {missing_elements}")
                
            # Check for ApexCharts library
            if 'apexcharts' in response.text.lower():
                print("   ✅ ApexCharts library included")
            else:
                print("   ❌ ApexCharts library missing")
                
            # Check for initialization function
            if 'initializeApexCharts' in response.text:
                print("   ✅ Chart initialization function found")
            else:
                print("   ❌ Chart initialization function missing")
                
        else:
            print(f"   ❌ Main dashboard failed to load (status: {response.status_code})")
        
        # Test 2: Activity dashboard
        print("\n2️⃣ Testing activity dashboard...")
        response = session.get(f"{base_url}/activity/1", timeout=10)
        if response.status_code == 200:
            print("   ✅ Activity dashboard loads successfully")
            
            # Check for KPI chart elements (should match main dashboard)
            chart_elements = ['revenue-chart', 'active-passports-chart', 'passports-created-chart', 'pending-signups-chart']
            missing_elements = []
            
            for element in chart_elements:
                if f'id="{element}"' not in response.text:
                    missing_elements.append(element)
            
            if not missing_elements:
                print("   ✅ All 4 KPI chart elements found in HTML")
            else:
                print(f"   ❌ Missing chart elements: {missing_elements}")
                
            # Check for ApexCharts library
            if 'apexcharts' in response.text.lower():
                print("   ✅ ApexCharts library included")
            else:
                print("   ❌ ApexCharts library missing")
                
            # Check for initialization function
            if 'initializeActivityKPICharts' in response.text:
                print("   ✅ Activity chart initialization function found")
            else:
                print("   ❌ Activity chart initialization function missing")
                
        else:
            print(f"   ❌ Activity dashboard failed to load (status: {response.status_code})")
        
        print("\n🔧 FIXES APPLIED:")
        print("   • Fixed chart element IDs: active-users-chart → active-passports-chart")
        print("   • Fixed chart element IDs: unpaid-passports-chart → pending-signups-chart")
        print("   • Fixed JavaScript data access: data.trend_data → data.trend")
        print("   • Replaced simple chart init with robust working dashboard approach")
        print("   • Added proper ApexCharts error handling and library checks")
        
        print("\n✨ NEXT STEPS:")
        print("   • Test both pages in browser to verify charts render properly")
        print("   • Check browser console for any remaining JavaScript errors")
        print("   • Verify chart interactions (dropdowns, tooltips) work correctly")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error testing pages: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = test_kpi_pages()
    sys.exit(0 if success else 1)