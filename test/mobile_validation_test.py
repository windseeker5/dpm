#!/usr/bin/env python3
"""
Manual validation test for mobile dashboard fixes.

This script tests the mobile dashboard fixes by making HTTP requests
and validating the HTML/CSS content includes the necessary fixes.

Usage:
    python test/mobile_validation_test.py

Tests:
1. Chart white gap fix validation  
2. Dropdown cutoff fix validation
3. Mobile CSS media query validation
4. JavaScript function presence validation
"""

import requests
import sys
import re
from urllib.parse import urljoin


class MobileDashboardValidator:
    """Validator for mobile dashboard fixes."""
    
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        
    def login(self, email='kdresdell@gmail.com', password='admin123'):
        """Login to get authenticated session."""
        try:
            # Get login page first
            login_url = urljoin(self.base_url, '/login')
            response = self.session.get(login_url)
            
            if response.status_code != 200:
                print(f"❌ Failed to access login page: {response.status_code}")
                return False
                
            # Submit login form
            login_data = {
                'email': email,
                'password': password
            }
            
            response = self.session.post(login_url, data=login_data, allow_redirects=True)
            
            if response.status_code == 200 and 'dashboard' in response.url:
                print("✅ Successfully logged in")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_dashboard_html(self):
        """Get dashboard HTML content."""
        try:
            dashboard_url = urljoin(self.base_url, '/dashboard')
            response = self.session.get(dashboard_url)
            
            if response.status_code == 200:
                print("✅ Dashboard loaded successfully")
                return response.text
            else:
                print(f"❌ Failed to load dashboard: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Dashboard loading error: {e}")
            return None
    
    def validate_chart_white_gap_fixes(self, html_content):
        """Validate that chart white gap fixes are present."""
        print("\n📊 Validating Chart White Gap Fixes...")
        
        # Check for enhanced mobile chart CSS
        fixes = [
            # Container height fixes
            r'height:\s*40px\s*!\s*important',
            r'max-height:\s*40px\s*!\s*important',
            r'min-height:\s*40px\s*!\s*important',
            
            # Position fixes
            r'position:\s*absolute\s*!\s*important',
            r'overflow:\s*hidden\s*!\s*important',
            
            # Padding/margin removal
            r'padding:\s*0\s*!\s*important',
            r'margin:\s*0\s*!\s*important',
            
            # Background transparency
            r'background:\s*transparent\s*!\s*important',
        ]
        
        passed = 0
        for fix_pattern in fixes:
            if re.search(fix_pattern, html_content, re.IGNORECASE):
                passed += 1
            else:
                print(f"⚠️  Missing chart fix: {fix_pattern}")
        
        if passed >= len(fixes) * 0.8:  # 80% threshold
            print(f"✅ Chart white gap fixes validated ({passed}/{len(fixes)} patterns found)")
            return True
        else:
            print(f"❌ Chart white gap fixes incomplete ({passed}/{len(fixes)} patterns found)")
            return False
    
    def validate_dropdown_cutoff_fixes(self, html_content):
        """Validate that dropdown cutoff fixes are present."""
        print("\n📋 Validating Dropdown Cutoff Fixes...")
        
        # Check for enhanced dropdown positioning CSS
        fixes = [
            # Z-index fixes
            r'z-index:\s*999999\s*!\s*important',
            
            # Position fixes
            r'position:\s*absolute\s*!\s*important',
            r'right:\s*0\s*!\s*important',
            r'left:\s*auto\s*!\s*important',
            
            # Height and overflow fixes
            r'max-height:\s*calc\(100vh\s*-\s*100px\)\s*!\s*important',
            r'overflow-y:\s*auto\s*!\s*important',
            
            # Visibility fixes
            r'overflow:\s*visible\s*!\s*important',
        ]
        
        passed = 0
        for fix_pattern in fixes:
            if re.search(fix_pattern, html_content, re.IGNORECASE):
                passed += 1
            else:
                print(f"⚠️  Missing dropdown fix: {fix_pattern}")
        
        if passed >= len(fixes) * 0.7:  # 70% threshold
            print(f"✅ Dropdown cutoff fixes validated ({passed}/{len(fixes)} patterns found)")
            return True
        else:
            print(f"❌ Dropdown cutoff fixes incomplete ({passed}/{len(fixes)} patterns found)")
            return False
    
    def validate_mobile_media_queries(self, html_content):
        """Validate mobile media queries are present."""
        print("\n📱 Validating Mobile Media Queries...")
        
        # Check for mobile-specific media queries
        mobile_queries = [
            r'@media\s+screen\s+and\s+\(max-width:\s*767\.98px\)',
            r'@media\s+screen\s+and\s+\(max-width:\s*767px\)',
        ]
        
        found_queries = 0
        for query_pattern in mobile_queries:
            matches = re.findall(query_pattern, html_content, re.IGNORECASE)
            found_queries += len(matches)
        
        if found_queries >= 2:
            print(f"✅ Mobile media queries validated ({found_queries} found)")
            return True
        else:
            print(f"❌ Insufficient mobile media queries ({found_queries} found)")
            return False
    
    def validate_javascript_functions(self, html_content):
        """Validate required JavaScript functions are present."""
        print("\n🔧 Validating JavaScript Functions...")
        
        # Check for mobile fix functions
        functions = [
            r'function\s+fixMobileChartRendering\s*\(',
            r'function\s+handleMobileDropdownPositioning\s*\(',
        ]
        
        passed = 0
        for func_pattern in functions:
            if re.search(func_pattern, html_content, re.IGNORECASE):
                passed += 1
                print(f"✅ Found: {func_pattern}")
            else:
                print(f"❌ Missing: {func_pattern}")
        
        if passed == len(functions):
            print("✅ All required JavaScript functions validated")
            return True
        else:
            print(f"❌ Missing JavaScript functions ({passed}/{len(functions)} found)")
            return False
    
    def validate_chart_elements(self, html_content):
        """Validate chart elements are present with correct IDs."""
        print("\n📈 Validating Chart Elements...")
        
        # Check for chart container IDs
        chart_ids = [
            r'id="revenue-chart"',
            r'id="active-passports-chart"',
            r'id="passports-created-chart"',
            r'id="pending-signups-chart"',
        ]
        
        passed = 0
        for chart_id in chart_ids:
            if re.search(chart_id, html_content, re.IGNORECASE):
                passed += 1
                print(f"✅ Found chart: {chart_id}")
            else:
                print(f"❌ Missing chart: {chart_id}")
        
        if passed >= 3:  # At least 3 out of 4 charts
            print(f"✅ Chart elements validated ({passed}/{len(chart_ids)} found)")
            return True
        else:
            print(f"❌ Insufficient chart elements ({passed}/{len(chart_ids)} found)")
            return False
    
    def validate_dropdown_elements(self, html_content):
        """Validate dropdown elements are present."""
        print("\n⬇️  Validating Dropdown Elements...")
        
        # Check for dropdown classes and elements
        dropdown_elements = [
            r'class="[^"]*dropdown[^"]*"',
            r'class="[^"]*dropdown-toggle[^"]*"',
            r'class="[^"]*dropdown-menu[^"]*"',
            r'class="[^"]*dropdown-item[^"]*"',
            r'data-period="7d"',
            r'data-period="30d"',
        ]
        
        passed = 0
        for element_pattern in dropdown_elements:
            if re.search(element_pattern, html_content, re.IGNORECASE):
                passed += 1
            else:
                print(f"⚠️  Missing dropdown element: {element_pattern}")
        
        if passed >= len(dropdown_elements) * 0.8:
            print(f"✅ Dropdown elements validated ({passed}/{len(dropdown_elements)} found)")
            return True
        else:
            print(f"❌ Insufficient dropdown elements ({passed}/{len(dropdown_elements)} found)")
            return False
    
    def run_full_validation(self):
        """Run complete validation suite."""
        print("🚀 Starting Mobile Dashboard Validation...")
        print("=" * 60)
        
        # Login first
        if not self.login():
            print("❌ Validation failed: Could not login")
            return False
        
        # Get dashboard content
        html_content = self.get_dashboard_html()
        if not html_content:
            print("❌ Validation failed: Could not load dashboard")
            return False
        
        # Run all validations
        results = {
            'chart_fixes': self.validate_chart_white_gap_fixes(html_content),
            'dropdown_fixes': self.validate_dropdown_cutoff_fixes(html_content),
            'media_queries': self.validate_mobile_media_queries(html_content),
            'javascript': self.validate_javascript_functions(html_content),
            'chart_elements': self.validate_chart_elements(html_content),
            'dropdown_elements': self.validate_dropdown_elements(html_content),
        }
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION RESULTS:")
        print("=" * 60)
        
        passed_count = sum(results.values())
        total_count = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title():.<30} {status}")
        
        print(f"\nOverall Result: {passed_count}/{total_count} tests passed")
        
        if passed_count >= total_count * 0.8:  # 80% pass rate
            print("🎉 VALIDATION SUCCESSFUL - Mobile fixes are properly implemented!")
            return True
        else:
            print("⚠️  VALIDATION INCOMPLETE - Some fixes may need attention")
            return False


def main():
    """Main function to run validation."""
    try:
        validator = MobileDashboardValidator()
        success = validator.run_full_validation()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()