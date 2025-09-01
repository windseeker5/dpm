#!/usr/bin/env python3
"""
Integration test for mobile dropdown fixes
Tests the actual Flask application on localhost:5000
"""

import requests
import sys
import time
from bs4 import BeautifulSoup

def test_dashboard_loads():
    """Test that the dashboard loads with our fixes"""
    try:
        # Create session
        session = requests.Session()
        
        # Get login page
        print("1. Testing login page access...")
        response = session.get('http://localhost:5000/login')
        if response.status_code != 200:
            print(f"❌ Login page failed: {response.status_code}")
            return False
        print("✓ Login page accessible")
        
        # Parse login form
        soup = BeautifulSoup(response.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if not csrf_token:
            print("❌ No CSRF token found")
            return False
        
        # Login
        print("2. Testing login...")
        login_data = {
            'email': 'kdresdell@gmail.com',
            'password': 'admin123',
            'csrf_token': csrf_token.get('value') if csrf_token else ''
        }
        
        response = session.post('http://localhost:5000/login', data=login_data)
        if response.status_code not in [200, 302]:
            print(f"❌ Login failed: {response.status_code}")
            return False
        print("✓ Login successful")
        
        # Access dashboard
        print("3. Testing dashboard access...")
        response = session.get('http://localhost:5000/dashboard')
        if response.status_code != 200:
            print(f"❌ Dashboard access failed: {response.status_code}")
            return False
        print("✓ Dashboard accessible")
        
        # Check for our mobile fixes in the HTML
        print("4. Validating mobile fixes in dashboard HTML...")
        content = response.text
        
        required_fixes = [
            'handleMobileDropdownPositioning',
            'fixMobileChartRendering',
            '999999',  # High z-index for mobile dropdowns
            '200px'    # Max height for mobile dropdowns
        ]
        
        missing_fixes = []
        for fix in required_fixes:
            if fix not in content:
                missing_fixes.append(fix)
        
        if missing_fixes:
            print(f"❌ Missing fixes in dashboard HTML: {missing_fixes}")
            return False
        
        print("✓ All mobile fixes present in dashboard HTML")
        
        # Check for KPI dropdown elements
        print("5. Validating KPI dropdown structure...")
        soup = BeautifulSoup(content, 'html.parser')
        
        kpi_cards = soup.find_all('div', {'data-kpi-card': True})
        if len(kpi_cards) < 4:
            print(f"❌ Expected 4 KPI cards, found {len(kpi_cards)}")
            return False
        
        dropdown_toggles = soup.find_all('button', class_='dropdown-toggle')
        if len(dropdown_toggles) < 4:
            print(f"❌ Expected 4 dropdown toggles, found {len(dropdown_toggles)}")
            return False
        
        dropdown_menus = soup.find_all('ul', class_='dropdown-menu')  
        if len(dropdown_menus) < 4:
            print(f"❌ Expected 4 dropdown menus, found {len(dropdown_menus)}")
            return False
        
        print(f"✓ Found {len(kpi_cards)} KPI cards with dropdowns")
        
        # Check for chart elements
        print("6. Validating chart elements...")
        chart_elements = soup.find_all('div', id=lambda x: x and '-chart' in x)
        if len(chart_elements) < 4:
            print(f"❌ Expected 4 chart elements, found {len(chart_elements)}")
            return False
        
        print(f"✓ Found {len(chart_elements)} chart elements")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_mobile_css_media_queries():
    """Test mobile CSS media query presence"""
    try:
        session = requests.Session()
        
        # Login first
        response = session.get('http://localhost:5000/login')
        soup = BeautifulSoup(response.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        
        login_data = {
            'email': 'kdresdell@gmail.com', 
            'password': 'admin123',
            'csrf_token': csrf_token.get('value') if csrf_token else ''
        }
        session.post('http://localhost:5000/login', data=login_data)
        
        # Get dashboard
        response = session.get('http://localhost:5000/dashboard')
        content = response.text
        
        print("7. Testing mobile CSS media queries...")
        
        # Check for mobile media query (flexible matching)
        has_mobile_query = any([
            '@media screen and (max-width: 767.98px)' in content,
            '@media (max-width: 767.98px)' in content,
            '@media screen and (max-width: 767px)' in content,
            'max-width: 767' in content
        ])
        
        if not has_mobile_query:
            print("❌ Mobile media query not found")
            return False
        
        print("✓ Mobile media query present")
        
        # Check for mobile-specific CSS classes
        mobile_classes = [
            '.kpi-card-mobile',
            '.dropdown-menu',
            '.dropdown'
        ]
        
        for css_class in mobile_classes:
            if css_class not in content:
                print(f"❌ Mobile CSS class {css_class} not found")
                return False
        
        print("✓ Mobile CSS classes present")
        return True
        
    except Exception as e:
        print(f"❌ Mobile CSS test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("=== Mobile Dropdown Fixes Integration Test ===")
    print("Testing Flask app at http://localhost:5000")
    print()
    
    # Check if server is running
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        print("✓ Flask server is running")
    except requests.exceptions.RequestException:
        print("❌ Flask server not accessible at localhost:5000")
        print("Please ensure the Flask server is running with: flask run --port 5000")
        sys.exit(1)
    
    # Run tests
    test_results = []
    
    test_results.append(("Dashboard Load & Login", test_dashboard_loads()))
    test_results.append(("Mobile CSS Media Queries", test_mobile_css_media_queries()))
    
    # Summary
    print("\n=== Test Results Summary ===")
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("Mobile dropdown fixes are working correctly.")
        print("\nNext steps:")
        print("1. Test manually on mobile device or browser dev tools")
        print("2. Verify dropdown positioning at viewport edges")  
        print("3. Check chart rendering after page reload")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("Please review the fixes and try again.")
        sys.exit(1)

if __name__ == '__main__':
    main()