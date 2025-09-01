#!/usr/bin/env python3
"""
Manual test script for DEAD SIMPLE Mobile KPI Cards
Run this to verify the mobile KPI implementation works
"""

import os
import sys
import requests
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_dashboard_access():
    """Test that we can access the dashboard"""
    try:
        # Try to access the dashboard
        response = requests.get('http://localhost:5000/dashboard', timeout=5)
        print(f"✅ Dashboard accessible - Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Dashboard not accessible: {e}")
        return False

def test_template_structure():
    """Test that the template has the correct structure"""
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'dashboard.html')
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return False
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    checks = [
        ('mobile-kpi-container', 'Mobile KPI container'),
        ('mobile-kpi-scroll', 'Mobile scroll container'), 
        ('mobile-kpi-card', 'Mobile KPI cards'),
        ('mobile-kpi-dots', 'Mobile dots navigation'),
        ('$2,688', 'Revenue value'),
        ('>24</div>', 'Passport values'),
        ('>8</div>', 'Unpaid value'),
        ('d-md-none', 'Mobile-only visibility'),
        ('scroll-snap-type: x mandatory', 'CSS scroll snap'),
        ('DEAD SIMPLE Mobile KPI dot navigation', 'Simple JavaScript')
    ]
    
    all_passed = True
    for check, description in checks:
        if check in content:
            print(f"✅ {description}")
        else:
            print(f"❌ Missing: {description}")
            all_passed = False
    
    return all_passed

def test_no_broken_features():
    """Test that we removed the broken features"""
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'dashboard.html')
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Extract mobile section only
    mobile_start = content.find('<!-- Mobile Version (DEAD SIMPLE) -->')
    mobile_end = content.find('<!-- Activities Section -->', mobile_start)
    
    if mobile_start == -1 or mobile_end == -1:
        print("❌ Could not find mobile section boundaries")
        return False
        
    mobile_section = content[mobile_start:mobile_end]
    
    # Things that should NOT be in mobile section
    bad_things = [
        ('mobile_kpi_data', 'Dynamic data references'),
        ('chart', 'Chart elements'),
        ('apexcharts', 'ApexCharts'),
        ('kpi-carousel', 'Old carousel'),
        ('kpi-track', 'Old track'),
        ('kpi-slide', 'Old slides')
    ]
    
    all_clean = True
    for bad_thing, description in bad_things:
        if bad_thing in mobile_section.lower():
            print(f"❌ Found broken feature: {description}")
            all_clean = False
        else:
            print(f"✅ Removed: {description}")
    
    return all_clean

def main():
    """Run all manual tests"""
    print("🚀 DEAD SIMPLE Mobile KPI Cards - Manual Test")
    print("=" * 50)
    print(f"Test run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Server accessibility
    print("1. Testing server access...")
    server_ok = test_dashboard_access()
    print()
    
    # Test 2: Template structure
    print("2. Testing template structure...")
    template_ok = test_template_structure()
    print()
    
    # Test 3: Clean implementation
    print("3. Testing clean implementation...")
    clean_ok = test_no_broken_features()
    print()
    
    # Summary
    print("=" * 50)
    if server_ok and template_ok and clean_ok:
        print("🎉 ALL TESTS PASSED!")
        print("Your mobile KPI cards are ready to use!")
        print()
        print("To test manually:")
        print("1. Open http://localhost:5000/dashboard")
        print("2. Login with: kdresdell@gmail.com / admin123")
        print("3. Resize browser to mobile width (< 768px)")
        print("4. You should see 4 swipeable cards with hard-coded values")
        print("5. Swipe or scroll to navigate between cards")
        print("6. Dots should update as you swipe")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("Check the issues above and fix them.")
        return 1

if __name__ == '__main__':
    sys.exit(main())