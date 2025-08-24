#!/usr/bin/env python3
"""
Comprehensive test for signup form after cosmetic improvements.
Tests multiple passport types and ensures form submission works correctly.
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def test_signup_form():
    """Test signup form with different passport types"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        test_results = []
        
        # Test passport type 1
        print("Testing passport type 1...")
        await page.goto('http://127.0.0.1:8890/signup/1?passport_type_id=1')
        await page.wait_for_load_state('networkidle')
        
        # Check that form loads
        title = await page.title()
        assert "Signup" in title, f"Page title should contain 'Signup', got: {title}"
        
        # Fill form
        await page.fill('input[name="name"]', 'Test User Type1')
        await page.fill('input[name="email"]', f'test1_{int(time.time())}@example.com')
        await page.fill('input[name="phone"]', '514-555-0301')
        await page.fill('textarea[name="notes"]', 'Testing passport type 1')
        await page.check('input[name="accept_terms"]')
        
        # Submit form
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        
        # Check redirect (should go to login for unauthenticated users)
        current_url = page.url
        test_results.append({
            'passport_type': 1,
            'success': '/login' in current_url,
            'url': current_url
        })
        
        # Test passport type 2
        print("Testing passport type 2...")
        await page.goto('http://127.0.0.1:8890/signup/1?passport_type_id=2')
        await page.wait_for_load_state('networkidle')
        
        # Fill form
        await page.fill('input[name="name"]', 'Test User Type2')
        await page.fill('input[name="email"]', f'test2_{int(time.time())}@example.com')
        await page.fill('input[name="phone"]', '514-555-0302')
        await page.fill('textarea[name="notes"]', 'Testing passport type 2')
        await page.check('input[name="accept_terms"]')
        
        # Submit form
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        
        # Check redirect
        current_url = page.url
        test_results.append({
            'passport_type': 2,
            'success': '/login' in current_url,
            'url': current_url
        })
        
        # Test mobile view
        print("Testing mobile view...")
        await page.set_viewport_size({"width": 375, "height": 812})
        await page.goto('http://127.0.0.1:8890/signup/1?passport_type_id=1')
        await page.wait_for_load_state('networkidle')
        
        # Fill form on mobile
        await page.fill('input[name="name"]', 'Mobile Test User')
        await page.fill('input[name="email"]', f'mobile_{int(time.time())}@example.com')
        await page.fill('input[name="phone"]', '514-555-0303')
        await page.check('input[name="accept_terms"]')
        
        # Submit form
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        
        # Check redirect
        current_url = page.url
        test_results.append({
            'passport_type': 'mobile',
            'success': '/login' in current_url,
            'url': current_url
        })
        
        await browser.close()
        
        # Print results
        print("\n=== Test Results ===")
        all_passed = True
        for result in test_results:
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"Passport Type {result['passport_type']}: {status}")
            print(f"  Redirected to: {result['url']}")
            if not result['success']:
                all_passed = False
        
        if all_passed:
            print("\n✅ ALL TESTS PASSED - Form submission works correctly!")
        else:
            print("\n❌ SOME TESTS FAILED - Check the results above")
        
        return all_passed

if __name__ == "__main__":
    result = asyncio.run(test_signup_form())
    exit(0 if result else 1)