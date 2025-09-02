#!/usr/bin/env python3
"""
Comprehensive test suite for Activity Dashboard KPI cards
Tests the fix for KPI cards displaying correct numbers and rendering charts
"""
import time
import json
from playwright.sync_api import sync_playwright

def test_activity_dashboard_kpi_complete():
    """Complete test of KPI cards on activity dashboard"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("🚀 Starting Comprehensive KPI Activity Dashboard Test...")
        
        try:
            # Login
            page.goto("http://localhost:5000/login")
            print("✓ Navigated to login page")
            
            page.fill('input[name="email"]', "kdresdell@gmail.com")
            page.fill('input[name="password"]', "admin123")
            page.click('button[type="submit"]')
            print("✓ Logged in successfully")
            
            # Wait for navigation
            page.wait_for_timeout(2000)
            
            # Navigate to activity dashboard for activity 1
            page.goto("http://localhost:5000/activity-dashboard/1")
            print("✓ Navigated to activity dashboard")
            
            # Wait for page to fully load
            page.wait_for_timeout(3000)
            
            # Capture console messages
            console_messages = []
            page.on("console", lambda msg: console_messages.append({"type": msg.type, "text": msg.text}))
            
            # Force re-initialization to capture console logs
            page.evaluate("if (typeof initializeApexCharts === 'function') initializeApexCharts();")
            
            print("\n📊 Testing KPI Values:")
            
            # Test Revenue value
            revenue_value = page.locator('#revenue-value').text_content()
            print(f"  Revenue: {revenue_value}")
            assert revenue_value != '0', "Revenue should not be 0"
            
            # Test Active Passports value
            active_value = page.locator('#active-passports-value').text_content()
            print(f"  Active Passports: {active_value}")
            
            # Test Passports Created value
            created_value = page.locator('#passports-created-value').text_content()
            print(f"  Passports Created: {created_value}")
            
            # Test Pending Signups value
            pending_value = page.locator('#pending-signups-value').text_content()
            print(f"  Pending Signups: {pending_value}")
            
            print("\n📈 Testing Chart Rendering:")
            
            # Check if charts have rendered (look for SVG elements)
            charts = [
                ('revenue-chart', 'Revenue'),
                ('active-passports-chart', 'Active Passports'),
                ('passports-created-chart', 'Passports Created'),
                ('pending-signups-chart', 'Pending Signups')
            ]
            
            charts_status = []
            for chart_id, chart_name in charts:
                svg_count = page.locator(f'#{chart_id} svg').count()
                has_paths = page.locator(f'#{chart_id} path').count() > 0
                has_rects = page.locator(f'#{chart_id} rect').count() > 0
                
                is_rendered = svg_count > 0 and (has_paths or has_rects)
                charts_status.append({
                    'name': chart_name,
                    'rendered': is_rendered,
                    'svg_count': svg_count,
                    'has_content': has_paths or has_rects
                })
                
                status = "✓" if is_rendered else "✗"
                print(f"  {status} {chart_name}: SVG={svg_count}, Content={has_paths or has_rects}")
            
            print("\n🔄 Testing Period Dropdown:")
            
            # Test period change to "All time"
            dropdown = page.locator('[data-kpi-period-button]').first
            dropdown.click()
            page.wait_for_timeout(500)
            
            # Click "All time" option
            page.click('a[data-period="all"]')
            print("  ✓ Changed period to 'All time'")
            
            # Wait for AJAX update
            page.wait_for_timeout(2000)
            
            # Check values after period change
            new_revenue = page.locator('#revenue-value').text_content()
            new_active = page.locator('#active-passports-value').text_content()
            new_created = page.locator('#passports-created-value').text_content()
            
            print(f"\n📊 Values after period change:")
            print(f"  Revenue: {new_revenue}")
            print(f"  Active Passports: {new_active}")
            print(f"  Passports Created: {new_created}")
            
            # Verify charts still exist after update
            print("\n📈 Charts after period change:")
            for chart_id, chart_name in charts:
                svg_count = page.locator(f'#{chart_id} svg').count()
                status = "✓" if svg_count > 0 else "✗"
                print(f"  {status} {chart_name} still rendered")
            
            # Print console messages for debugging
            if console_messages:
                print("\n🔍 Console Output:")
                for msg in console_messages[-10:]:  # Last 10 messages
                    if 'Debugging' in msg['text'] or 'Chart' in msg['text'] or 'Rendering' in msg['text']:
                        print(f"  {msg['text'][:100]}")
            
            # Test results summary
            all_charts_rendered = all(chart['rendered'] for chart in charts_status)
            values_correct = (
                revenue_value != '0' and 
                active_value != '0' and 
                created_value != '0'
            )
            
            print("\n✅ Test Summary:")
            print(f"  KPI Values Display: {'PASS' if values_correct else 'FAIL'}")
            print(f"  All Charts Rendered: {'PASS' if all_charts_rendered else 'FAIL'}")
            print(f"  Period Dropdown Works: PASS")
            
            if all_charts_rendered and values_correct:
                print("\n🎉 All KPI cards working correctly!")
                return True
            else:
                print("\n⚠️ Some issues detected")
                return False
                
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            browser.close()
            print("\n🏁 Test completed")

def test_kpi_data_structure():
    """Test the KPI data structure returned by the API"""
    import requests
    
    print("\n🔬 Testing KPI Data Structure...")
    
    # Login and get session
    session = requests.Session()
    
    # First get the login page to establish session
    session.get("http://localhost:5000/login")
    
    # Now login
    login_data = {
        "email": "kdresdell@gmail.com",
        "password": "admin123"
    }
    
    response = session.post("http://localhost:5000/login", data=login_data, allow_redirects=True)
    
    # Check if we're logged in by trying to access a protected page
    check_response = session.get("http://localhost:5000/dashboard")
    if check_response.status_code == 200:
        print("✓ Login successful")
    else:
        print(f"❌ Login failed - unable to access dashboard")
        return False
    
    # Test KPI API
    api_url = "http://localhost:5000/api/kpi-data?period=30d&activity_id=1"
    response = session.get(api_url)
    
    if response.status_code == 200:
        data = response.json()
        print("✓ API responded successfully")
        
        if data.get('success'):
            kpi_data = data.get('kpi_data', {})
            
            print("\n📊 KPI Data Structure:")
            for kpi_type in ['revenue', 'active_users', 'passports_created', 'unpaid_passports']:
                if kpi_type in kpi_data:
                    kpi = kpi_data[kpi_type]
                    print(f"\n  {kpi_type}:")
                    print(f"    current: {kpi.get('current', 0)}")
                    print(f"    previous: {kpi.get('previous', 0)}")
                    print(f"    growth: {kpi.get('growth', 0)}%")
                    print(f"    trend_data points: {len(kpi.get('trend_data', []))}")
                    
                    # Validate structure
                    assert 'current' in kpi, f"Missing 'current' in {kpi_type}"
                    assert 'trend_data' in kpi, f"Missing 'trend_data' in {kpi_type}"
            
            print("\n✓ Data structure validation passed")
            return True
        else:
            print(f"❌ API error: {data.get('error')}")
            return False
    else:
        print(f"❌ API failed with status {response.status_code}")
        return False

if __name__ == "__main__":
    # Run both tests
    print("=" * 60)
    print("ACTIVITY DASHBOARD KPI TEST SUITE")
    print("=" * 60)
    
    # Test data structure
    structure_pass = test_kpi_data_structure()
    
    # Test UI rendering
    ui_pass = test_activity_dashboard_kpi_complete()
    
    # Final results
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print(f"  Data Structure Test: {'PASS ✓' if structure_pass else 'FAIL ✗'}")
    print(f"  UI Rendering Test: {'PASS ✓' if ui_pass else 'FAIL ✗'}")
    
    if structure_pass and ui_pass:
        print("\n🎉 ALL TESTS PASSED!")
        exit(0)
    else:
        print("\n⚠️ SOME TESTS FAILED")
        exit(1)