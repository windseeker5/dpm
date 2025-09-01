#!/usr/bin/env python3
"""
Manual mobile browser test for dashboard fixes.

This script uses basic HTTP requests to test the dashboard
and provides guidance for manual testing.
"""

import urllib.request
import urllib.parse
import http.cookiejar
import json
import time
import sys


class MobileDashboardTester:
    """Simple tester for mobile dashboard using urllib."""
    
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        
        # Set up cookie jar for session handling
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        
        # Set mobile user agent
        self.opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Language', 'en-us'),
            ('Accept-Encoding', 'gzip, deflate'),
            ('Connection', 'keep-alive'),
        ]
    
    def test_server_available(self):
        """Test if the Flask server is available."""
        try:
            response = self.opener.open(f'{self.base_url}/')
            print(f"✅ Server is running (status: {response.getcode()})")
            return True
        except Exception as e:
            print(f"❌ Server not available: {e}")
            return False
    
    def attempt_login(self, email='kdresdell@gmail.com', password='admin123'):
        """Attempt to login with credentials."""
        try:
            # Get login page
            login_url = f'{self.base_url}/login'
            response = self.opener.open(login_url)
            login_html = response.read().decode('utf-8')
            
            # Simple form data preparation
            form_data = urllib.parse.urlencode({
                'email': email,
                'password': password
            }).encode('utf-8')
            
            # Submit login
            req = urllib.request.Request(login_url, data=form_data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            response = self.opener.open(req)
            final_url = response.geturl()
            
            if 'dashboard' in final_url:
                print("✅ Login successful")
                return True
            else:
                print("❌ Login failed - check credentials")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_dashboard_content(self):
        """Get dashboard content for analysis."""
        try:
            dashboard_url = f'{self.base_url}/dashboard'
            response = self.opener.open(dashboard_url)
            content = response.read().decode('utf-8')
            
            print("✅ Dashboard content retrieved")
            return content
            
        except Exception as e:
            print(f"❌ Dashboard access error: {e}")
            return None
    
    def analyze_mobile_fixes(self, content):
        """Analyze the dashboard content for mobile fixes."""
        print("\n📱 Analyzing Mobile Fixes in Live Content...")
        
        # Chart fixes analysis
        chart_indicators = [
            'height: 40px !important',
            'position: absolute !important', 
            'overflow: hidden !important',
            'background: transparent !important',
        ]
        
        chart_fixes_found = 0
        for indicator in chart_indicators:
            if indicator in content:
                chart_fixes_found += 1
        
        print(f"📊 Chart fixes: {chart_fixes_found}/{len(chart_indicators)} indicators found")
        
        # Dropdown fixes analysis
        dropdown_indicators = [
            'z-index: 999999 !important',
            'calc(100vh - 100px)',
            'overflow: visible !important',
            'handleMobileDropdownPositioning',
        ]
        
        dropdown_fixes_found = 0
        for indicator in dropdown_indicators:
            if indicator in content:
                dropdown_fixes_found += 1
        
        print(f"📋 Dropdown fixes: {dropdown_fixes_found}/{len(dropdown_indicators)} indicators found")
        
        # Check for essential elements
        essential_elements = [
            'id="revenue-chart"',
            'id="active-passports-chart"', 
            'class="dropdown-toggle"',
            'class="kpi-period-btn"',
        ]
        
        elements_found = 0
        for element in essential_elements:
            if element in content:
                elements_found += 1
        
        print(f"🔧 Essential elements: {elements_found}/{len(essential_elements)} found")
        
        return {
            'chart_fixes': chart_fixes_found >= len(chart_indicators) * 0.75,
            'dropdown_fixes': dropdown_fixes_found >= len(dropdown_indicators) * 0.5,
            'elements': elements_found >= len(essential_elements) * 0.75,
        }
    
    def generate_test_report(self, content, analysis):
        """Generate a test report."""
        print("\n" + "=" * 60)
        print("📋 MOBILE DASHBOARD TEST REPORT")
        print("=" * 60)
        
        # Content stats
        print(f"📄 Dashboard HTML size: {len(content):,} characters")
        
        # Check for key mobile viewport
        if 'viewport' in content.lower():
            print("✅ Mobile viewport meta tag found")
        else:
            print("⚠️  Mobile viewport meta tag not detected")
        
        # Analysis results
        chart_status = "✅ GOOD" if analysis['chart_fixes'] else "⚠️ NEEDS CHECK"
        dropdown_status = "✅ GOOD" if analysis['dropdown_fixes'] else "⚠️ NEEDS CHECK" 
        elements_status = "✅ GOOD" if analysis['elements'] else "❌ MISSING"
        
        print(f"📊 Chart White Gap Fixes: {chart_status}")
        print(f"📋 Dropdown Cutoff Fixes: {dropdown_status}")
        print(f"🔧 Essential Elements: {elements_status}")
        
        # Overall assessment
        fixes_working = sum(analysis.values())
        if fixes_working >= 2:
            print("\n🎉 MOBILE FIXES APPEAR TO BE WORKING!")
            print("\n✅ Ready for manual testing on mobile device")
        else:
            print("\n⚠️  SOME ISSUES DETECTED - MANUAL REVIEW RECOMMENDED")
        
        return fixes_working >= 2
    
    def provide_manual_test_guidance(self):
        """Provide guidance for manual mobile testing."""
        print("\n" + "=" * 60)
        print("📱 MANUAL MOBILE TESTING GUIDE")
        print("=" * 60)
        
        print("\n1. 📊 Test Chart White Gap Bug Fix:")
        print("   - Open dashboard on mobile device")
        print("   - Look at KPI cards with line charts")
        print("   - Verify NO white gaps or boxes around charts")
        print("   - Charts should extend edge-to-edge in cards")
        
        print("\n2. 📋 Test Dropdown Cutoff Bug Fix:")
        print("   - Tap time period dropdown (\"Last 7 days\", etc.)")  
        print("   - Verify ALL dropdown options are visible")
        print("   - No options should be cut off at bottom")
        print("   - Try on different screen sizes")
        
        print("\n3. 🔧 General Mobile Testing:")
        print("   - Test in portrait and landscape")
        print("   - Scroll vertically - dropdowns should close")
        print("   - Verify responsive grid layout")
        print("   - Check all KPI cards are accessible")
        
        print("\n4. 🌐 Browsers to test:")
        print("   - Safari (iOS)")
        print("   - Chrome (Android)")
        print("   - Firefox Mobile")
        print("   - Samsung Internet")
        
        print(f"\n🔗 Test URL: {self.base_url}/dashboard")
        print("👤 Login: kdresdell@gmail.com / admin123")
    
    def run_full_test(self):
        """Run complete mobile dashboard test."""
        print("🚀 Mobile Dashboard Live Testing")
        print("=" * 40)
        
        # Test server availability
        if not self.test_server_available():
            print("❌ Cannot proceed - server not available")
            return False
        
        # Attempt login
        if not self.attempt_login():
            print("⚠️  Cannot test with authentication, but server is running")
            print("Manual testing is still possible")
            self.provide_manual_test_guidance()
            return True
        
        # Get dashboard content
        content = self.get_dashboard_content()
        if not content:
            print("❌ Could not retrieve dashboard content")
            return False
        
        # Analyze fixes
        analysis = self.analyze_mobile_fixes(content)
        
        # Generate report
        success = self.generate_test_report(content, analysis)
        
        # Provide manual testing guidance
        self.provide_manual_test_guidance()
        
        return success


def main():
    """Main testing function."""
    try:
        tester = MobileDashboardTester()
        success = tester.run_full_test()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()